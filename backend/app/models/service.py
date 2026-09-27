"""
BeautyCRM — Service & ServiceCategory Models (Услуги)
"""

import uuid

from sqlalchemy import (
    Boolean,
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
from sqlalchemy.orm import relationship

from app.database import Base


class ServiceCategory(Base):
    """
    Grouping for services (e.g. "Маникюр", "Педикюр", "Брови").
    """

    __tablename__ = "service_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name = Column(String(255), nullable=False, comment="Category name")
    description = Column(Text)
    sort_order = Column(Integer, default=0, comment="Display order")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="service_categories")
    services = relationship("Service", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ServiceCategory {self.name}>"


class Service(Base):
    """
    A service offered by a tenant (e.g. "Маникюр + Покрытие", 90 min, 2000 RUB).
    """

    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("service_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    title = Column(String(255), nullable=False, comment="Service name")
    description = Column(Text, comment="Service description")
    duration_minutes = Column(Integer, nullable=False, comment="Duration in minutes")
    price = Column(Numeric(10, 2), nullable=False, comment="Full price")
    prepayment_amount = Column(
        Numeric(10, 2), default=0,
        comment="Fixed prepayment amount (used if prepayment_percent is null)"
    )
    prepayment_percent = Column(
        Integer, nullable=True,
        comment="Prepayment as percentage of price (overrides prepayment_amount)"
    )
    photo_url = Column(Text, comment="Service photo URL")
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="services")
    category = relationship("ServiceCategory", back_populates="services")
    appointments = relationship("Appointment", back_populates="service")

    @property
    def effective_prepayment(self) -> float:
        """Calculate the actual prepayment amount."""
        if self.prepayment_percent is not None:
            return float(self.price) * self.prepayment_percent / 100
        return float(self.prepayment_amount or 0)

    def __repr__(self):
        return f"<Service {self.title} ({self.duration_minutes}min, {self.price}₽)>"
