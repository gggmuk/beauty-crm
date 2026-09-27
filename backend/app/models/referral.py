"""
BeautyCRM — Referral & Loyalty Models
"""

import uuid

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Referral(Base):
    """
    Tracks referral relationships between clients.
    When client A refers client B, client A earns loyalty points.
    """

    __tablename__ = "referrals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    referrer_client_id = Column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False, comment="Client who made the referral"
    )
    referred_client_id = Column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False, comment="New client who was referred"
    )
    referral_code = Column(String(50), comment="Unique referral code used")
    points_awarded = Column(Integer, default=0, comment="Points given to referrer")
    status = Column(
        String(20), default="pending",
        comment="pending | completed | expired"
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))


class LoyaltyTransaction(Base):
    """
    Tracks all loyalty point changes (earned, spent, expired).
    """

    __tablename__ = "loyalty_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    client_id = Column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    points = Column(
        Integer, nullable=False,
        comment="Positive = earned, Negative = spent"
    )
    balance_after = Column(Integer, comment="Points balance after transaction")
    transaction_type = Column(
        String(30), nullable=False,
        comment="visit | referral | bonus | redemption | manual | expiry"
    )
    description = Column(Text, comment="Human-readable description")
    appointment_id = Column(
        UUID(as_uuid=True), ForeignKey("appointments.id"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
