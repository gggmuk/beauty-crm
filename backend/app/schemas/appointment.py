from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.service import ServiceResponse
from app.schemas.client import ClientResponse


class TimeSlotResponse(BaseModel):
    start_time: datetime
    end_time: datetime
    is_available: bool = True
    reason: Optional[str] = None


class AppointmentCreate(BaseModel):
    service_id: UUID
    start_time: datetime
    notes: Optional[str] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_telegram_id: Optional[int] = None
    source: str = "bot"  # bot | web | manual


class AppointmentUpdate(BaseModel):
    status: Optional[str] = None  # pending_payment | confirmed | completed | cancelled | no_show
    prepayment_status: Optional[str] = None
    notes: Optional[str] = None
    cancel_reason: Optional[str] = None
    cancelled_by: Optional[str] = None
    client_confirmed: Optional[bool] = None


class AppointmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    client_id: UUID
    service_id: UUID
    start_time: datetime
    end_time: datetime
    status: str
    prepayment_status: str
    prepayment_amount: Decimal
    stripe_payment_intent_id: Optional[str] = None
    stripe_checkout_session_id: Optional[str] = None
    notes: Optional[str] = None
    cancel_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    reminder_24h_sent: bool
    reminder_2h_sent: bool
    client_confirmed: Optional[bool] = None
    source: str
    created_at: datetime

    service: Optional[ServiceResponse] = None
    client: Optional[ClientResponse] = None

    class Config:
        from_attributes = True
