from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class ServiceCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    sort_order: int = 0


class ServiceCategoryCreate(ServiceCategoryBase):
    pass


class ServiceCategoryResponse(ServiceCategoryBase):
    id: UUID
    tenant_id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceBase(BaseModel):
    title: str
    description: Optional[str] = None
    duration_minutes: int = Field(..., gt=0)
    price: Decimal = Field(..., ge=0)
    prepayment_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    prepayment_percent: Optional[int] = Field(default=None, ge=0, le=100)
    photo_url: Optional[str] = None
    category_id: Optional[UUID] = None
    sort_order: int = 0


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[Decimal] = None
    prepayment_amount: Optional[Decimal] = None
    prepayment_percent: Optional[int] = None
    photo_url: Optional[str] = None
    category_id: Optional[UUID] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ServiceResponse(ServiceBase):
    id: UUID
    tenant_id: UUID
    is_active: bool
    effective_prepayment: float
    created_at: datetime

    class Config:
        from_attributes = True
