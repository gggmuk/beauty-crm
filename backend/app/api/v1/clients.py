"""
BeautyCRM — Clients CRM Router
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_db
from app.models.client import Client
from app.models.tenant import Tenant
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate

router = APIRouter(prefix="/clients", tags=["Clients (CRM)"])


@router.get("", response_model=List[ClientResponse])
async def list_clients(
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List tenant's clients with search (name, phone) and status filter."""
    stmt = select(Client).where(Client.tenant_id == current_tenant.id)

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(Client.name.ilike(pattern), Client.phone.ilike(pattern))
        )

    if status_filter:
        stmt = stmt.where(Client.status == status_filter)

    stmt = stmt.order_by(Client.total_spent.desc(), Client.created_at.desc())
    q = await db.execute(stmt)
    return q.scalars().all()


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client_details(
    client_id: UUID,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get single client details."""
    client = await db.get(Client, client_id)
    if not client or client.tenant_id != current_tenant.id:
        raise HTTPException(404, "Client not found.")
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    req: ClientUpdate,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update client notes, status, or block status."""
    client = await db.get(Client, client_id)
    if not client or client.tenant_id != current_tenant.id:
        raise HTTPException(404, "Client not found.")

    update_data = req.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(client, field, val)

    await db.commit()
    await db.refresh(client)
    return client
