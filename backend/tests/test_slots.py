"""
BeautyCRM — Slot Calculation Unit Tests
"""

import pytest
from datetime import date, time, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.models.service import Service
from app.models.schedule import Schedule
from app.services.slot_service import SlotService


@pytest.mark.asyncio
async def test_get_available_slots(
    test_db: AsyncSession, sample_tenant: Tenant, sample_service: Service
):
    target_date = date.today() + timedelta(days=2)
    day_of_week = target_date.weekday()

    # Set up schedule for this day
    schedule = Schedule(
        tenant_id=sample_tenant.id,
        day_of_week=day_of_week,
        start_time=time(10, 0),
        end_time=time(18, 0),
        is_working_day=True,
    )
    test_db.add(schedule)
    await test_db.commit()

    slots = await SlotService.get_available_slots(
        test_db, sample_tenant.id, target_date, sample_service.id
    )

    assert len(slots) > 0
    # Service is 90 mins long, working day 10:00 to 18:00 (8 hours = 480 mins)
    # Slots generated every 30 mins: 10:00, 10:30, 11:00, 11:30, 12:00, 12:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30
    # Last slot starting at 16:30 finishes at 18:00
    assert any(s.is_available for s in slots)
