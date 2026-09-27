"""
BeautyCRM — Tenant Model (Мастера / Студии)
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Tenant(Base):
    """
    Represents a beauty master or studio — the core entity for multi-tenancy.
    All data in the system is scoped to a tenant via tenant_id FK.
    """

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, comment="Master/studio name")
    phone = Column(String(20), comment="Contact phone number")
    email = Column(String(255), comment="Contact email")
    telegram_user_id = Column(
        BigInteger, unique=True, nullable=False, index=True,
        comment="Telegram user ID of the master"
    )
    password_hash = Column(String(255), comment="Hashed password for web login")

    # Bot configuration
    bot_token_encrypted = Column(Text, comment="AES-256 encrypted Telegram bot token")
    bot_username = Column(String(100), comment="Bot @username")
    bot_webhook_hash = Column(String(64), unique=True, comment="URL-safe hash for webhook routing")
    welcome_message = Column(
        Text,
        default="Добро пожаловать! 👋 Здесь вы можете записаться на услугу.",
        comment="Bot welcome message"
    )
    logo_url = Column(Text, comment="Studio/master logo URL")

    # Subscription
    subscription_plan_id = Column(
        UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=True
    )
    subscription_status = Column(
        String(20), default="free",
        comment="free | active | expired | blocked"
    )
    subscription_expires_at = Column(DateTime(timezone=True))

    # Settings
    is_active = Column(Boolean, default=True)
    buffer_minutes = Column(
        Integer, default=15,
        comment="Buffer time between appointments (e.g. for sanitization)"
    )
    cancellation_hours = Column(
        Integer, default=12,
        comment="Minimum hours before appointment start for client cancellation"
    )
    timezone = Column(String(50), default="Europe/Moscow")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    services = relationship("Service", back_populates="tenant", cascade="all, delete-orphan")
    service_categories = relationship("ServiceCategory", back_populates="tenant", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="tenant", cascade="all, delete-orphan")
    schedule_overrides = relationship("ScheduleOverride", back_populates="tenant", cascade="all, delete-orphan")
    break_times = relationship("BreakTime", back_populates="tenant", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="tenant", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="tenant", cascade="all, delete-orphan")
    subscription_plan = relationship("SubscriptionPlan", back_populates="tenants")

    def __repr__(self):
        return f"<Tenant {self.name} ({self.id})>"
