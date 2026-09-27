"""
BeautyCRM — Bot Setup & Webhook Router
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant, get_db
from app.models.tenant import Tenant
from app.schemas.tenant import TenantBotSetup, TenantResponse
from app.services.bot_manager import BotManagerService

router = APIRouter(prefix="/bot", tags=["Bot Setup & Webhooks"])


@router.post("/setup", response_model=TenantResponse)
async def setup_bot(
    req: TenantBotSetup,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Connect Telegram Bot Token from @BotFather to tenant account.
    Validates token, encrypts via AES-256, and registers webhook.
    """
    try:
        updated_tenant = await BotManagerService.setup_tenant_bot(
            db, current_tenant, req.bot_token
        )
        return updated_tenant
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/webhook/{webhook_hash}")
async def handle_telegram_webhook(
    webhook_hash: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Multi-bot webhook receiver.
    Routes incoming Telegram update to appropriate tenant based on webhook_hash.
    """
    body = await request.json()

    # Find tenant by webhook_hash
    q = await db.execute(
        select(Tenant).where(Tenant.bot_webhook_hash == webhook_hash)
    )
    tenant = q.scalars().first()
    if not tenant:
        return {"ok": False, "error": "Unknown webhook hash"}

    # Process message / callback query via bot handler dispatcher
    from app.bot.dispatcher import dispatch_telegram_update
    await dispatch_telegram_update(db, tenant, body)

    return {"ok": True}
