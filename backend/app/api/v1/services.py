"""
BeautyCRM — Services & Categories Router
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_db, get_tenant_by_header
from app.models.service import Service, ServiceCategory
from app.models.tenant import Tenant
from app.schemas.service import (
    ServiceCategoryCreate,
    ServiceCategoryResponse,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)

router = APIRouter(prefix="/services", tags=["Services"])


# ================= Categories =================

@router.get("/categories", response_model=List[ServiceCategoryResponse])
async def list_categories(
    tenant_id: Optional[UUID] = None,
    current_tenant: Optional[Tenant] = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List service categories for a tenant."""
    target_tenant_id = tenant_id or (current_tenant.id if current_tenant else None)
    if not target_tenant_id:
        raise HTTPException(400, "tenant_id parameter or authentication required.")

    q = await db.execute(
        select(ServiceCategory)
        .where(
            ServiceCategory.tenant_id == target_tenant_id,
            ServiceCategory.is_active == True,
        )
        .order_by(ServiceCategory.sort_order)
    )
    return q.scalars().all()


@router.post("/categories", response_model=ServiceCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    req: ServiceCategoryCreate,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a new service category."""
    category = ServiceCategory(
        tenant_id=current_tenant.id,
        name=req.name,
        description=req.description,
        sort_order=req.sort_order,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


# ================= Services =================

@router.get("", response_model=List[ServiceResponse])
async def list_services(
    tenant_id: Optional[UUID] = None,
    category_id: Optional[UUID] = None,
    current_tenant: Optional[Tenant] = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List services for a tenant (publicly accessible if tenant_id is provided)."""
    target_tenant_id = tenant_id or (current_tenant.id if current_tenant else None)
    if not target_tenant_id:
        raise HTTPException(400, "tenant_id parameter or authentication required.")

    stmt = select(Service).where(
        Service.tenant_id == target_tenant_id,
        Service.is_active == True,
    )
    if category_id:
        stmt = stmt.where(Service.category_id == category_id)

    stmt = stmt.order_by(Service.sort_order, Service.title)
    q = await db.execute(stmt)
    return q.scalars().all()


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    req: ServiceCreate,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Create a new service."""
    service = Service(
        tenant_id=current_tenant.id,
        **req.model_dump(),
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@router.patch("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: UUID,
    req: ServiceUpdate,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update a service."""
    service = await db.get(Service, service_id)
    if not service or service.tenant_id != current_tenant.id:
        raise HTTPException(404, "Service not found.")

    update_data = req.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(service, field, val)

    await db.commit()
    await db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: UUID,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a service (sets is_active=False)."""
    service = await db.get(Service, service_id)
    if not service or service.tenant_id != current_tenant.id:
        raise HTTPException(404, "Service not found.")

    service.is_active = False
    await db.commit()
    return None
