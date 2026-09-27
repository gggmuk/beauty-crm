"""
BeautyCRM — Appointment Model (Записи)
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Appointment(Base):
    """
    An appointment (booking) linking a client to a service at a specific time slot.
    
    Status lifecycle:
        pending_payment → confirmed → completed
                                    → cancelled
                                    → no_show
    """

    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    client_id = Column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    service_id = Column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Time slot
    start_time = Column(
        DateTime(timezone=True), nullable=False,
        comment="Appointment start datetime"
    )
    end_time = Column(
        DateTime(timezone=True), nullable=False,
        comment="Appointment end datetime"
    )

    # Status
    status = Column(
        String(20), default="pending_payment",
        comment="pending_payment | confirmed | completed | cancelled | no_show"
    )
    prepayment_status = Column(
        String(20), default="none",
        comment="none | pending | paid | refunded"
    )
    prepayment_amount = Column(
        Numeric(10, 2), default=0,
        comment="Actual prepayment amount charged"
    )

    # Payment
    stripe_payment_intent_id = Column(String(255), comment="Stripe PaymentIntent ID")
    stripe_checkout_session_id = Column(String(255), comment="Stripe Checkout Session ID")

    # Notes
    notes = Column(Text, comment="Additional notes from client or master")
    cancel_reason = Column(Text, comment="Reason for cancellation")
    cancelled_at = Column(DateTime(timezone=True))
    cancelled_by = Column(
        String(20), comment="client | master | system"
    )

    # Reminder tracking
    reminder_24h_sent = Column(Boolean, default=False)
    reminder_2h_sent = Column(Boolean, default=False)
    client_confirmed = Column(
        Boolean, nullable=True,
        comment="True if client confirmed via reminder button"
    )

    # Source tracking
    source = Column(
        String(20), default="bot",
        comment="bot | web | manual (walk-in)"
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="appointments")
    client = relationship("Client", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")

    __table_args__ = (
        Index(
            "ix_appointments_tenant_time",
            "tenant_id", "start_time", "end_time",
        ),
        Index(
            "ix_appointments_status",
            "tenant_id", "status",
        ),
    )

    def __repr__(self):
        return f"<Appointment {self.start_time} [{self.status}]>"
