"""
BeautyCRM — Local Bot Runner (Long Polling Mode for Testing)

Use this script for local testing without needing HTTPS webhooks / ngrok.
Usage:
    python run_polling.py --token "YOUR_TELEGRAM_BOT_TOKEN" --tenant-id "YOUR_TENANT_UUID"
"""

import argparse
import asyncio
import logging
from uuid import UUID

import httpx

from app.database import async_session_factory
from app.models.tenant import Tenant
from app.bot.dispatcher import dispatch_telegram_update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot_runner")


async def start_polling(bot_token: str, tenant_id: str):
    logger.info(f"🤖 Starting Telegram Bot polling mode...")

    # Fetch tenant
    async with async_session_factory() as db:
        tenant = await db.get(Tenant, UUID(tenant_id))
        if not tenant:
            logger.error(f"Tenant with ID {tenant_id} not found in database!")
            return

    # Delete webhook first to allow long polling
    async with httpx.AsyncClient() as client:
        await client.post(f"https://api.telegram.org/bot{bot_token}/deleteWebhook")

    offset = 0
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

    logger.info("✅ Bot is online and listening for messages! Open your bot in Telegram and send /start.")

    while True:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, params={"offset": offset, "timeout": 20})
                data = resp.json()

                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        async with async_session_factory() as db:
                            # Refetch tenant in case it changed
                            t = await db.get(Tenant, UUID(tenant_id))
                            await dispatch_telegram_update(db, t, update)

        except Exception as e:
            logger.error(f"Polling error: {e}")
            await asyncio.sleep(3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BeautyCRM Telegram Bot Local Polling")
    parser.add_argument("--token", required=True, help="Telegram Bot Token from @BotFather")
    parser.add_argument("--tenant-id", required=True, help="Tenant UUID from database")
    args = parser.parse_args()

    asyncio.run(start_polling(args.token, args.tenant-id))
