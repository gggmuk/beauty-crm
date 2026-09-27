"""
BeautyCRM — Bot Manager Service

Handles tenant bot setup:
1. Validating token via Telegram getMe
2. Encrypting token with AES-256
3. Registering platform webhook with Telegram
"""

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.tenant import Tenant
from app.security import encrypt_token, generate_bot_token_hash

settings = get_settings()


class BotManagerService:

    @classmethod
    async def validate_bot_token(cls, bot_token: str) -> dict:
        """Call Telegram getMe API to verify token validity."""
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            data = resp.json()
            if not data.get("ok"):
                raise ValueError("Invalid bot token according to Telegram API.")
            return data["result"]

    @classmethod
    async def register_webhook(cls, bot_token: str, webhook_hash: str) -> bool:
        """Register webhook URL with Telegram API."""
        webhook_url = f"{settings.webhook_base_url}/api/v1/bot/webhook/{webhook_hash}"
        url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
        payload = {"url": webhook_url}

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()
            return bool(data.get("ok"))

    @classmethod
    async def setup_tenant_bot(
        cls, db: AsyncSession, tenant: Tenant, bot_token: str
    ) -> Tenant:
        """Validate, encrypt, store token, and register webhook."""
        # 1. Validate with Telegram
        bot_info = await cls.validate_bot_token(bot_token)
        bot_username = bot_info.get("username")

        # 2. Encrypt token with AES-256
        encrypted_token = encrypt_token(bot_token)

        # 3. Generate webhook hash
        webhook_hash = generate_bot_token_hash(bot_token)

        # 4. Register webhook if base URL configured
        if settings.webhook_base_url and "localhost" not in settings.webhook_base_url:
            await cls.register_webhook(bot_token, webhook_hash)

        # 5. Save to tenant
        tenant.bot_token_encrypted = encrypted_token
        tenant.bot_username = bot_username
        tenant.bot_webhook_hash = webhook_hash

        await db.commit()
        await db.refresh(tenant)

        return tenant
