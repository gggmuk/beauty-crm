"""
BeautyCRM — SubscriptionPlan Model (Тарифные планы)
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class SubscriptionPlan(Base):
    """
    SaaS subscription plans (Free, Pro, Studio).
    Managed by superadmin.
    """

    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True, comment="Plan name")
    description = Column(Text, comment="Plan description")

    # Limits
    max_clients = Column(
        Integer, nullable=True,
        comment="Max number of clients (null = unlimited)"
    )
    max_appointments_month = Column(
        Integer, nullable=True,
        comment="Max appointments per month (null = unlimited)"
    )
    max_bots = Column(
        Integer, default=1,
        comment="Max number of Telegram bots"
    )

    # Pricing
    price_monthly = Column(Numeric(10, 2), default=0, comment="Monthly price")
    price_yearly = Column(Numeric(10, 2), nullable=True, comment="Yearly price (discount)")

    # Feature flags
    features = Column(
        JSONB, default={},
        comment="Additional feature flags as JSON"
    )
    # Example features:
    # {
    #   "retention_engine": true,
    #   "custom_branding": true,
    #   "sms_notifications": false,
    #   "analytics_advanced": true,
    #   "referral_system": true,
    #   "priority_support": false
    # }

    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenants = relationship("Tenant", back_populates="subscription_plan")

    def __repr__(self):
        return f"<SubscriptionPlan {self.name} ({self.price_monthly}/mo)>"
