"""
BeautyCRM — Auth Router
Registration and login for beauty masters / studio owners.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.tenant import Tenant
from app.schemas.auth import LoginRequest, RegisterTenantRequest, Token
from app.schemas.tenant import TenantResponse
from app.security import (
    create_access_token,
    hash_password,
    verify_password,
    generate_bot_token_hash,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()


@router.post("/register", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def register_tenant(
    req: RegisterTenantRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new beauty master / studio tenant."""
    # Check if telegram_user_id already exists
    existing_q = await db.execute(
        select(Tenant).where(Tenant.telegram_user_id == req.telegram_user_id)
    )
    if existing_q.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A master with this Telegram ID is already registered.",
        )

    tenant = Tenant(
        name=req.name,
        telegram_user_id=req.telegram_user_id,
        phone=req.phone,
        email=req.email,
        password_hash=hash_password(req.password),
        subscription_status="free",
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.post("/login", response_model=Token)
async def login_tenant(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate a master using telegram_user_id and password."""
    # Superadmin bypass check
    if (
        req.telegram_user_id == settings.superadmin_telegram_id
        and req.password == settings.secret_key
    ):
        token = create_access_token(
            data={"sub": "superadmin", "is_superadmin": True}
        )
        return Token(access_token=token)

    q = await db.execute(
        select(Tenant).where(Tenant.telegram_user_id == req.telegram_user_id)
    )
    tenant = q.scalars().first()

    if not tenant or not tenant.password_hash or not verify_password(req.password, tenant.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram ID or password.",
        )

    if not tenant.is_active or tenant.subscription_status == "blocked":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is disabled or blocked.",
        )

    token = create_access_token(
        data={"sub": str(tenant.id), "telegram_user_id": tenant.telegram_user_id}
    )
    return Token(access_token=token)
