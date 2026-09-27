"""
BeautyCRM — Appointments Router
Handles:
1. Available slot computation (public)
2. Creating an appointment (with Redis lock)
3. Confirming / cancelling appointments
4. Appointment listing (filtered by date range/status)
"""

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_tenant, get_db
from app.models.appointment import Appointment
from app.models.client import Client
from app.models.service import Service
from app.models.tenant import Tenant
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
    TimeSlotResponse,
)
from app.services.slot_service import SlotService

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.get("/slots", response_model=List[TimeSlotResponse])
async def get_available_slots(
    tenant_id: UUID = Query(...),
    service_id: UUID = Query(...),
    target_date: date = Query(..., alias="date"),
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint to calculate available time slots for a tenant, service, and date.
    Used by Telegram Mini App (TWA).
    """
    return await SlotService.get_available_slots(
        db, tenant_id, target_date, service_id
    )


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    tenant_id: UUID,
    req: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new appointment.
    Aquires a Redis slot lock for 10 minutes to prevent double booking.
    """
    # 1. Fetch service to calculate end_time & prepayment
    service = await db.get(Service, req.service_id)
    if not service or not service.is_active or service.tenant_id != tenant_id:
        raise HTTPException(400, "Invalid or inactive service.")

    end_time = req.start_time + timedelta(minutes=service.duration_minutes)

    # 2. Acquire Redis lock
    locked = await SlotService.lock_slot(tenant_id, req.start_time)
    if not locked:
        raise HTTPException(
            409, "This time slot was just selected by another client. Please choose another."
        )

    # 3. Find or create Client
    client: Optional[Client] = None
    if req.client_telegram_id:
        client_q = await db.execute(
            select(Client).where(
                and_(
                    Client.tenant_id == tenant_id,
                    Client.telegram_id == req.client_telegram_id,
                )
            )
        )
        client = client_q.scalars().first()

    if not client:
        # Create new client record
        client = Client(
            tenant_id=tenant_id,
            telegram_id=req.client_telegram_id or 0,
            name=req.client_name or "Гость",
            phone=req.client_phone,
        )
        db.add(client)
        await db.commit()
        await db.refresh(client)

    prepayment = service.effective_prepayment
    initial_status = "pending_payment" if prepayment > 0 else "confirmed"
    prepayment_status = "pending" if prepayment > 0 else "none"

    # 4. Create Appointment
    appt = Appointment(
        tenant_id=tenant_id,
        client_id=client.id,
        service_id=req.service_id,
        start_time=req.start_time,
        end_time=end_time,
        status=initial_status,
        prepayment_status=prepayment_status,
        prepayment_amount=prepayment,
        notes=req.notes,
        source=req.source,
    )
    db.add(appt)
    await db.commit()
    await db.refresh(appt)

    # If no prepayment required, release lock immediately
    if prepayment <= 0:
        await SlotService.unlock_slot(tenant_id, req.start_time)
        from app.services.notification_service import NotificationService
        await NotificationService.notify_appointment_confirmed(db, appt)

    return appt


@router.get("", response_model=List[AppointmentResponse])
async def list_appointments(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List tenant's appointments with options to filter by date range and status."""
    stmt = (
        select(Appointment)
        .options(selectinload(Appointment.service), selectinload(Appointment.client))
        .where(Appointment.tenant_id == current_tenant.id)
    )

    if start_date:
        start_dt = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        stmt = stmt.where(Appointment.start_time >= start_dt)

    if end_date:
        end_dt = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        stmt = stmt.where(Appointment.start_time <= end_dt)

    if status_filter:
        stmt = stmt.where(Appointment.status == status_filter)

    stmt = stmt.order_by(Appointment.start_time.asc())
    q = await db.execute(stmt)
    return q.scalars().all()


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: UUID,
    req: AppointmentUpdate,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update appointment status (confirm, cancel, mark completed/no-show)."""
    appt = await db.get(Appointment, appointment_id)
    if not appt or appt.tenant_id != current_tenant.id:
        raise HTTPException(404, "Appointment not found.")

    update_data = req.model_dump(exclude_unset=True)
    if update_data.get("status") == "cancelled":
        appt.cancelled_at = datetime.now(timezone.utc)
        await SlotService.unlock_slot(appt.tenant_id, appt.start_time)

    for field, val in update_data.items():
        setattr(appt, field, val)

    # If completed, update client CRM metrics
    if req.status == "completed":
        client = await db.get(Client, appt.client_id)
        if client:
            client.total_visits = (client.total_visits or 0) + 1
            client.last_visit_at = datetime.now(timezone.utc)
            if appt.service:
                client.total_spent = (client.total_spent or 0) + appt.service.price
            client.status = "regular"

    await db.commit()
    await db.refresh(appt)
    return appt
