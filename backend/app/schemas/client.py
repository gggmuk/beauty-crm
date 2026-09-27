from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class ClientBase(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    telegram_id: int
    avatar_url: Optional[str] = None
    referred_by: Optional[UUID] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    is_blocked: Optional[bool] = None


class ClientResponse(ClientBase):
    id: UUID
    tenant_id: UUID
    telegram_id: int
    avatar_url: Optional[str] = None
    total_visits: int
    total_spent: Decimal
    last_visit_at: Optional[datetime] = None
    status: str
    loyalty_points: int
    referred_by: Optional[UUID] = None
    is_blocked: bool
    no_show_count: int
    created_at: datetime

    class Config:
        from_attributes = True
