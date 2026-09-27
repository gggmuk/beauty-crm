from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    tenant_id: Optional[str] = None
    telegram_user_id: Optional[int] = None
    is_superadmin: bool = False


class LoginRequest(BaseModel):
    telegram_user_id: int
    password: str


class RegisterTenantRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    telegram_user_id: int
    phone: Optional[str] = None
    email: Optional[str] = None
    password: str = Field(..., min_length=6)
