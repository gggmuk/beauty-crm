from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    welcome_message: Optional[str] = None
    logo_url: Optional[str] = None
    buffer_minutes: int = 15
    cancellation_hours: int = 12
    timezone: str = "Europe/Moscow"


class TenantCreate(TenantBase):
    telegram_user_id: int
    password: str


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    welcome_message: Optional[str] = None
    logo_url: Optional[str] = None
    buffer_minutes: Optional[int] = None
    cancellation_hours: Optional[int] = None
    timezone: Optional[str] = None


class TenantBotSetup(BaseModel):
    bot_token: str = Field(..., description="Raw Telegram bot token from @BotFather")


class TenantResponse(TenantBase):
    id: UUID
    telegram_user_id: int
    bot_username: Optional[str] = None
    subscription_status: str
    subscription_expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
