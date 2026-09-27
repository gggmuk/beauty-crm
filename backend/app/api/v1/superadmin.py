"""
BeautyCRM — SaaS SuperAdmin Router
Used by SaaS platform owner to manage tenants, subscription plans, and platform revenue metrics.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_superadmin
from app.models.appointment import Appointment
from app.models.tenant import Tenant
from app.models.subscription import SubscriptionPlan
from app.schemas.tenant import TenantResponse

router = APIRouter(prefix="/superadmin", tags=["SuperAdmin (SaaS Owner)"])


@router.get("/tenants", response_model=List[TenantResponse])
async def list_all_tenants(
    admin: dict = Depends(get_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """List all registered tenants / masters on the platform."""
    q = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    return q.scalars().all()


@router.patch("/tenants/{tenant_id}/block")
async def block_tenant(
    tenant_id: UUID,
    blocked: bool = True,
    admin: dict = Depends(get_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Block or unblock a tenant account."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(404, "Tenant not found.")

    tenant.subscription_status = "blocked" if blocked else "free"
    tenant.is_active = not blocked
    await db.commit()
    return {"status": "updated", "is_active": tenant.is_active}


@router.get("/analytics")
async def get_platform_analytics(
    admin: dict = Depends(get_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Get high-level SaaS platform analytics."""
    tenants_count = await db.scalar(select(func.count(Tenant.id)))
    active_tenants = await db.scalar(
        select(func.count(Tenant.id)).where(Tenant.is_active == True)
    )

    total_appts = await db.scalar(select(func.count(Appointment.id)))
    confirmed_appts = await db.scalar(
        select(func.count(Appointment.id)).where(Appointment.status == "confirmed")
    )

    total_prepayments = await db.scalar(
        select(func.sum(Appointment.prepayment_amount)).where(
            Appointment.prepayment_status == "paid"
        )
    ) or 0

    return {
        "total_tenants": tenants_count,
        "active_tenants": active_tenants,
        "total_appointments": total_appts,
        "confirmed_appointments": confirmed_appts,
        "total_platform_prepayments_turnover": float(total_prepayments),
    }
