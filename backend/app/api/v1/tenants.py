"""
BeautyCRM — Tenant / Master Settings Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_db
from app.models.tenant import Tenant
from app.schemas.tenant import TenantResponse, TenantUpdate

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get("/me", response_model=TenantResponse)
async def get_my_profile(
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """Get currently logged-in master's profile."""
    return current_tenant


@router.patch("/me", response_model=TenantResponse)
async def update_my_profile(
    req: TenantUpdate,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update master settings (buffer_minutes, cancellation_hours, welcome message, etc.)."""
    update_data = req.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(current_tenant, field, val)

    await db.commit()
    await db.refresh(current_tenant)
    return current_tenant
