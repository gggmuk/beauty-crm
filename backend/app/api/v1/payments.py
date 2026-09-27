"""
BeautyCRM — Payments Router (Stripe Integration)
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.payment import PaymentSessionCreate, PaymentSessionResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-session", response_model=PaymentSessionResponse)
async def create_payment_session(
    req: PaymentSessionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create Stripe Checkout session for an appointment prepayment."""
    try:
        session = await PaymentService.create_checkout_session(
            db, req.appointment_id, req.currency
        )
        return session
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
):
    """Stripe webhook receiver."""
    payload = await request.body()
    try:
        await PaymentService.handle_stripe_event(db, payload, stripe_signature)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
