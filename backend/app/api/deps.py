"""
BeautyCRM — FastAPI Dependencies
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.tenant import Tenant
from app.security import decode_access_token

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_tenant(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """
    Dependency that extracts JWT bearer token, decodes tenant_id,
    and returns the active Tenant model. Enforces row-level isolation.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
        tenant_id_str: str = payload.get("sub")
        if not tenant_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    tenant = await db.get(Tenant, UUID(tenant_id_str))
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    if not tenant.is_active or tenant.subscription_status == "blocked":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is disabled or blocked",
        )

    return tenant


async def get_superadmin(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Dependency verifying superadmin privileges."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(token)
        if not payload.get("is_superadmin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Superadmin privileges required",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )


async def get_tenant_by_header(
    x_tenant_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[Tenant]:
    """Optional dependency to extract tenant via X-Tenant-ID header (used by TWA)."""
    if not x_tenant_id:
        return None
    try:
        tenant_uuid = UUID(x_tenant_id)
        tenant = await db.get(Tenant, tenant_uuid)
        return tenant
    except ValueError:
        return None
