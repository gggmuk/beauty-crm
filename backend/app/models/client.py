"""
BeautyCRM — Client Model (Клиенты мастеров)
"""

import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Client(Base):
    """
    A client of a specific tenant.
    Each client is scoped to one tenant (the same Telegram user
    can be a client of multiple masters — separate Client rows).
    """

    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    telegram_id = Column(
        BigInteger, nullable=False, index=True,
        comment="Client's Telegram user ID"
    )
    name = Column(String(255), comment="Client display name")
    phone = Column(String(20), comment="Phone number")
    email = Column(String(255), comment="Email address")
    avatar_url = Column(Text, comment="Telegram avatar URL")

    # CRM metrics
    total_visits = Column(Integer, default=0, comment="Number of completed visits")
    total_spent = Column(
        Numeric(12, 2), default=0,
        comment="Total amount spent (LTV)"
    )
    last_visit_at = Column(
        DateTime(timezone=True),
        comment="Timestamp of last completed appointment"
    )
    status = Column(
        String(20), default="new",
        comment="new | regular | at_risk | lost"
    )

    # Loyalty
    loyalty_points = Column(Integer, default=0, comment="Accumulated loyalty points")
    referred_by = Column(
        UUID(as_uuid=True), ForeignKey("clients.id"),
        nullable=True, comment="Referral: who invited this client"
    )

    # Notes
    notes = Column(Text, comment="Master's notes about the client")

    # Flags
    is_blocked = Column(Boolean, default=False, comment="Blocked by master")
    no_show_count = Column(Integer, default=0, comment="Number of no-shows")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="clients")
    appointments = relationship("Appointment", back_populates="client")
    referred_clients = relationship("Client", backref="referrer", remote_side="Client.id")

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "telegram_id",
            name="uq_client_per_tenant"
        ),
    )

    @property
    def is_at_risk(self) -> bool:
        """Check if the client hasn't visited in 30+ days."""
        if not self.last_visit_at:
            return False
        from datetime import datetime, timezone, timedelta
        return (datetime.now(timezone.utc) - self.last_visit_at) > timedelta(days=30)

    def __repr__(self):
        return f"<Client {self.name} (visits={self.total_visits}, LTV={self.total_spent})>"
