from datetime import date, time, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ScheduleBase(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday ... 6=Sunday")
    start_time: time
    end_time: time
    is_working_day: bool = True


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleResponse(ScheduleBase):
    id: UUID
    tenant_id: UUID

    class Config:
        from_attributes = True


class ScheduleOverrideBase(BaseModel):
    date: date
    is_working: bool = False
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = None


class ScheduleOverrideCreate(ScheduleOverrideBase):
    pass


class ScheduleOverrideResponse(ScheduleOverrideBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class BreakTimeBase(BaseModel):
    day_of_week: Optional[int] = Field(default=None, ge=0, le=6)
    start_time: time
    end_time: time
    label: Optional[str] = None


class BreakTimeCreate(BreakTimeBase):
    pass


class BreakTimeResponse(BreakTimeBase):
    id: UUID
    tenant_id: UUID

    class Config:
        from_attributes = True
