"""
BeautyCRM — Payment Service (Stripe Integration)

Handles creating Stripe Checkout sessions for prepayment and processing Stripe webhooks.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.appointment import Appointment
from app.models.service import Service
from app.models.tenant import Tenant
from app.schemas.payment import PaymentSessionResponse

settings = get_settings()

if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


class PaymentService:

    @classmethod
    async def create_checkout_session(
        cls,
        db: AsyncSession,
        appointment_id: UUID,
        currency: str = "usd",
    ) -> PaymentSessionResponse:
        """Create a Stripe Checkout Session for an appointment's prepayment."""
        if not settings.stripe_secret_key:
            raise ValueError("Stripe API key is not configured.")

        # Fetch appointment
        appt = await db.get(Appointment, appointment_id)
        if not appt:
            raise ValueError("Appointment not found")

        if appt.status not in ["pending_payment"]:
            raise ValueError(f"Appointment status '{appt.status}' cannot be paid.")

        # Fetch service details
        service = await db.get(Service, appt.service_id)
        tenant = await db.get(Tenant, appt.tenant_id)

        prepayment = Decimal(str(appt.prepayment_amount))
        if prepayment <= 0 and service:
            prepayment = Decimal(str(service.effective_prepayment))

        if prepayment <= 0:
            raise ValueError("Prepayment amount must be greater than 0.")

        # Amount in cents/smallest currency unit
        amount_cents = int(prepayment * 100)

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {
                            "name": f"Prepayment: {service.title if service else 'Beauty Service'}",
                            "description": f"Master: {tenant.name if tenant else 'Beauty Studio'}",
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{settings.stripe_success_url}?session_id={{CHECKOUT_SESSION_ID}}&appointment_id={appointment_id}",
            cancel_url=f"{settings.stripe_cancel_url}?appointment_id={appointment_id}",
            client_reference_id=str(appointment_id),
            metadata={
                "appointment_id": str(appointment_id),
                "tenant_id": str(appt.tenant_id),
                "client_id": str(appt.client_id),
            },
        )

        # Save session ID on appointment
        appt.stripe_checkout_session_id = session.id
        await db.commit()

        return PaymentSessionResponse(
            checkout_url=session.url,
            session_id=session.id,
            amount=prepayment,
            currency=currency.lower(),
        )

    @classmethod
    async def handle_stripe_event(
        cls, db: AsyncSession, event_payload: bytes, sig_header: str
    ) -> bool:
        """Process incoming Stripe webhook event."""
        if not settings.stripe_webhook_secret:
            raise ValueError("Stripe webhook secret not configured.")

        try:
            event = stripe.Webhook.construct_event(
                event_payload, sig_header, settings.stripe_webhook_secret
            )
        except Exception as e:
            raise ValueError(f"Webhook signature verification failed: {e}")

        event_type = event.get("type")
        data_object = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            session_id = data_object.get("id")
            appointment_id_str = data_object.get("client_reference_id") or data_object.get("metadata", {}).get("appointment_id")

            if appointment_id_str:
                appt_id = UUID(appointment_id_str)
                appt = await db.get(Appointment, appt_id)
                if appt:
                    appt.status = "confirmed"
                    appt.prepayment_status = "paid"
                    appt.stripe_payment_intent_id = data_object.get("payment_intent")
                    await db.commit()

                    # Release Redis lock if any
                    from app.services.slot_service import SlotService
                    await SlotService.unlock_slot(appt.tenant_id, appt.start_time)

                    # Send notification via Bot
                    from app.services.notification_service import NotificationService
                    await NotificationService.notify_appointment_confirmed(db, appt)
                    return True

        elif event_type == "payment_intent.payment_failed":
            payment_intent_id = data_object.get("id")
            q = await db.execute(
                select(Appointment).where(
                    Appointment.stripe_payment_intent_id == payment_intent_id
                )
            )
            appt = q.scalars().first()
            if appt:
                appt.status = "cancelled"
                appt.cancel_reason = "Payment failed"
                await db.commit()

        return True
