"""
BeautyCRM — Schedules & Break Times Router
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_db
from app.models.schedule import BreakTime, Schedule, ScheduleOverride
from app.models.tenant import Tenant
from app.schemas.schedule import (
    BreakTimeCreate,
    BreakTimeResponse,
    ScheduleCreate,
    ScheduleOverrideCreate,
    ScheduleOverrideResponse,
    ScheduleResponse,
)

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.get("", response_model=List[ScheduleResponse])
async def get_weekly_schedule(
    tenant_id: Optional[UUID] = None,
    current_tenant: Optional[Tenant] = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get tenant's 7-day weekly schedule."""
    target_id = tenant_id or (current_tenant.id if current_tenant else None)
    if not target_id:
        raise HTTPException(400, "tenant_id parameter or authentication required.")

    q = await db.execute(
        select(Schedule)
        .where(Schedule.tenant_id == target_id)
        .order_by(Schedule.day_of_week)
    )
    return q.scalars().all()


@router.post("/batch", response_model=List[ScheduleResponse])
async def set_weekly_schedule(
    schedules: List[ScheduleCreate],
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Bulk update/replace weekly schedule for all 7 days."""
    # Remove existing
    await db.execute(
        delete(Schedule).where(Schedule.tenant_id == current_tenant.id)
    )

    new_schedules = [
        Schedule(tenant_id=current_tenant.id, **s.model_dump()) for s in schedules
    ]
    db.add_all(new_schedules)
    await db.commit()

    q = await db.execute(
        select(Schedule)
        .where(Schedule.tenant_id == current_tenant.id)
        .order_by(Schedule.day_of_week)
    )
    return q.scalars().all()


# ================= Schedule Overrides =================

@router.get("/overrides", response_model=List[ScheduleOverrideResponse])
async def get_schedule_overrides(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get date overrides (holidays, special work days)."""
    q = await db.execute(
        select(ScheduleOverride)
        .where(ScheduleOverride.tenant_id == current_tenant.id)
        .order_by(ScheduleOverride.date)
    )
    return q.scalars().all()


@router.post("/overrides", response_model=ScheduleOverrideResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule_override(
    req: ScheduleOverrideCreate,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Add a schedule override for a specific date."""
    override = ScheduleOverride(
        tenant_id=current_tenant.id,
        **req.model_dump(),
    )
    db.add(override)
    await db.commit()
    await db.refresh(override)
    return override


# ================= Break Times =================

@router.get("/breaks", response_model=List[BreakTimeResponse])
async def get_break_times(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get break times (e.g. lunch breaks)."""
    q = await db.execute(
        select(BreakTime).where(BreakTime.tenant_id == current_tenant.id)
    )
    return q.scalars().all()


@router.post("/breaks", response_model=BreakTimeResponse, status_code=status.HTTP_201_CREATED)
async def create_break_time(
    req: BreakTimeCreate,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a break time."""
    bt = BreakTime(tenant_id=current_tenant.id, **req.model_dump())
    db.add(bt)
    await db.commit()
    await db.refresh(bt)
    return bt
