from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class PaymentSessionCreate(BaseModel):
    appointment_id: UUID
    currency: str = "usd"


class PaymentSessionResponse(BaseModel):
    checkout_url: str
    session_id: str
    amount: Decimal
    currency: str


class StripeWebhookPayload(BaseModel):
    id: str
    type: str
    data: dict
