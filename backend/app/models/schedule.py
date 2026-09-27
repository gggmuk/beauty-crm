"""
BeautyCRM — Schedule, ScheduleOverride, BreakTime Models (График работы)
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Schedule(Base):
    """
    Weekly recurring schedule for a tenant.
    Defines working hours for each day of the week.
    """

    __tablename__ = "schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    day_of_week = Column(
        Integer, nullable=False,
        comment="0=Monday, 1=Tuesday, ..., 6=Sunday"
    )
    start_time = Column(Time, nullable=False, comment="Work start time")
    end_time = Column(Time, nullable=False, comment="Work end time")
    is_working_day = Column(Boolean, default=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="schedules")

    def __repr__(self):
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day = days[self.day_of_week] if 0 <= self.day_of_week <= 6 else "?"
        return f"<Schedule {day} {self.start_time}-{self.end_time}>"


class ScheduleOverride(Base):
    """
    Date-specific overrides to the weekly schedule.
    Used for holidays, special working days, vacations, etc.
    """

    __tablename__ = "schedule_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    date = Column(Date, nullable=False, comment="The specific date to override")
    is_working = Column(
        Boolean, default=False,
        comment="True = working on this day (even if normally off), False = day off"
    )
    start_time = Column(Time, comment="Override start time (if working)")
    end_time = Column(Time, comment="Override end time (if working)")
    reason = Column(String(255), comment="Reason for override (e.g. 'Holiday')")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="schedule_overrides")

    def __repr__(self):
        status = "WORK" if self.is_working else "OFF"
        return f"<ScheduleOverride {self.date} [{status}]>"


class BreakTime(Base):
    """
    Break periods during a working day (e.g. lunch break).
    Applied weekly by day_of_week, or for all days if day_of_week is null.
    """

    __tablename__ = "break_times"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    day_of_week = Column(
        Integer, nullable=True,
        comment="Specific day (0-6) or null for every day"
    )
    start_time = Column(Time, nullable=False, comment="Break start")
    end_time = Column(Time, nullable=False, comment="Break end")
    label = Column(String(100), comment="e.g. 'Lunch break'")

    # Relationships
    tenant = relationship("Tenant", back_populates="break_times")

    def __repr__(self):
        return f"<BreakTime {self.start_time}-{self.end_time}>"
