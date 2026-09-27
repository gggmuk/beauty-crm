"""
BeautyCRM — Slot Calculation & Distributed Locking Service

Computes available time slots for a given tenant, service, and date.
Handles:
1. Working hours by day of week
2. Special schedule overrides (holidays / extra workdays)
3. Break times
4. Existing appointments + buffer time
5. Redis SET NX distributed lock (10-minute TTL for booking flow)
"""

import json
from datetime import datetime, date, time, timedelta, timezone
from typing import List, Optional
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.tenant import Tenant
from app.models.service import Service
from app.models.schedule import Schedule, ScheduleOverride, BreakTime
from app.models.appointment import Appointment
from app.schemas.appointment import TimeSlotResponse

settings = get_settings()


async def get_redis_client() -> redis.Redis:
    """Get Redis connection."""
    return redis.from_url(settings.redis_url, decode_responses=True)


class SlotService:

    @staticmethod
    def _make_lock_key(tenant_id: UUID, slot_start: datetime) -> str:
        """Format Redis lock key for a specific slot."""
        timestamp_str = slot_start.strftime("%Y%m%d_%H%M")
        return f"slot_lock:{tenant_id}:{timestamp_str}"

    @classmethod
    async def lock_slot(
        cls, tenant_id: UUID, slot_start: datetime, client_id: Optional[str] = None
    ) -> bool:
        """
        Attempt to acquire a Redis lock on a slot using SET NX EX.
        TTL default is 600s (10 minutes).
        
        Returns True if acquired, False if already locked by someone else.
        """
        r = await get_redis_client()
        key = cls._make_lock_key(tenant_id, slot_start)
        val = json.dumps({"client_id": str(client_id) if client_id else "anonymous", "locked_at": datetime.now(timezone.utc).isoformat()})
        
        # SET key value NX EX ttl
        acquired = await r.set(key, val, nx=True, ex=settings.slot_lock_ttl_seconds)
        await r.aclose()
        return bool(acquired)

    @classmethod
    async def unlock_slot(cls, tenant_id: UUID, slot_start: datetime) -> bool:
        """Release a Redis lock on a slot."""
        r = await get_redis_client()
        key = cls._make_lock_key(tenant_id, slot_start)
        deleted = await r.delete(key)
        await r.aclose()
        return bool(deleted)

    @classmethod
    async def is_slot_locked(cls, tenant_id: UUID, slot_start: datetime) -> bool:
        """Check if a slot is currently locked in Redis."""
        r = await get_redis_client()
        key = cls._make_lock_key(tenant_id, slot_start)
        exists = await r.exists(key)
        await r.aclose()
        return bool(exists)

    @classmethod
    async def get_available_slots(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        target_date: date,
        service_id: UUID,
    ) -> List[TimeSlotResponse]:
        """
        Calculate all available start time slots for target_date.
        """
        # 1. Fetch tenant & buffer_minutes
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            return []

        buffer_min = tenant.buffer_minutes or 15

        # 2. Fetch service duration
        service = await db.get(Service, service_id)
        if not service or not service.is_active or service.tenant_id != tenant_id:
            return []

        service_duration = timedelta(minutes=service.duration_minutes)

        # 3. Determine working hours for target_date
        # Check override first
        override_q = await db.execute(
            select(ScheduleOverride).where(
                and_(
                    ScheduleOverride.tenant_id == tenant_id,
                    ScheduleOverride.date == target_date,
                )
            )
        )
        override = override_q.scalars().first()

        start_t: Optional[time] = None
        end_t: Optional[time] = None

        if override:
            if not override.is_working:
                return []  # Day off via override
            start_t = override.start_time
            end_t = override.end_time
        else:
            # Check weekly schedule
            day_of_week = target_date.weekday()  # 0=Mon ... 6=Sun
            sched_q = await db.execute(
                select(Schedule).where(
                    and_(
                        Schedule.tenant_id == tenant_id,
                        Schedule.day_of_week == day_of_week,
                    )
                )
            )
            sched = sched_q.scalars().first()
            if not sched or not sched.is_working_day:
                return []  # Not a working day
            start_t = sched.start_time
            end_t = sched.end_time

        if not start_t or not end_t:
            return []

        # Convert to full datetimes (naive or timezone aware based on tenant tz)
        day_start = datetime.combine(target_date, start_t).replace(tzinfo=timezone.utc)
        day_end = datetime.combine(target_date, end_t).replace(tzinfo=timezone.utc)

        # 4. Fetch break times
        breaks_q = await db.execute(
            select(BreakTime).where(
                and_(
                    BreakTime.tenant_id == tenant_id,
                    or_(
                        BreakTime.day_of_week == target_date.weekday(),
                        BreakTime.day_of_week.is_(None),
                    ),
                )
            )
        )
        breaks = breaks_q.scalars().all()
        break_intervals = [
            (
                datetime.combine(target_date, b.start_time).replace(tzinfo=timezone.utc),
                datetime.combine(target_date, b.end_time).replace(tzinfo=timezone.utc),
            )
            for b in breaks
        ]

        # 5. Fetch existing non-cancelled appointments for this day
        start_of_day = datetime.combine(target_date, time.min).replace(tzinfo=timezone.utc)
        end_of_day = datetime.combine(target_date, time.max).replace(tzinfo=timezone.utc)

        appts_q = await db.execute(
            select(Appointment).where(
                and_(
                    Appointment.tenant_id == tenant_id,
                    Appointment.status.in_(["pending_payment", "confirmed", "completed"]),
                    Appointment.start_time < end_of_day,
                    Appointment.end_time > start_of_day,
                )
            )
        )
        existing_appts = appts_q.scalars().all()

        # Add buffer to existing appts
        busy_intervals = []
        for appt in existing_appts:
            # appt end time + buffer
            buffered_end = appt.end_time + timedelta(minutes=buffer_min)
            busy_intervals.append((appt.start_time, buffered_end))

        # Add breaks to busy_intervals
        busy_intervals.extend(break_intervals)

        # 6. Generate candidate slots (e.g. every 30 mins or step = buffer_min)
        slot_step = timedelta(minutes=30)
        curr = day_start
        available_slots: List[TimeSlotResponse] = []

        now_utc = datetime.now(timezone.utc)

        while curr + service_duration <= day_end:
            slot_end = curr + service_duration

            # Cannot book in the past
            if curr < now_utc:
                curr += slot_step
                continue

            # Check overlap with busy_intervals
            is_busy = False
            for b_start, b_end in busy_intervals:
                # Overlap condition: slot_start < b_end AND slot_end > b_start
                if curr < b_end and slot_end > b_start:
                    is_busy = True
                    break

            # Check Redis lock
            is_locked = False
            if not is_busy:
                is_locked = await cls.is_slot_locked(tenant_id, curr)

            available_slots.append(
                TimeSlotResponse(
                    start_time=curr,
                    end_time=slot_end,
                    is_available=(not is_busy and not is_locked),
                    reason="Locked by another user" if is_locked else ("Booked" if is_busy else None),
                )
            )

            curr += slot_step

        return available_slots
