"""
BeautyCRM — Telegram Bot /start handler
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import Tenant
from app.models.client import Client
from app.services.notification_service import NotificationService
from sqlalchemy import select, and_


async def handle_start_command(
    db: AsyncSession, tenant: Tenant, chat_id: int, user_info: dict
):
    """Handle /start command in client bot."""
    telegram_id = user_info.get("id")
    first_name = user_info.get("first_name", "")
    last_name = user_info.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip()

    # Find or auto-register client record
    q = await db.execute(
        select(Client).where(
            and_(
                Client.tenant_id == tenant.id,
                Client.telegram_id == telegram_id,
            )
        )
    )
    client = q.scalars().first()
    if not client:
        client = Client(
            tenant_id=tenant.id,
            telegram_id=telegram_id,
            name=full_name or "Клиент Telegram",
        )
        db.add(client)
        await db.commit()

    welcome_text = (
        f"👋 <b>{tenant.name}</b>\n\n"
        f"{tenant.welcome_message or 'Добро пожаловать в онлайн-запись!'}\n\n"
        f"Нажмите на кнопку ниже, чтобы выбрать услугу и время."
    )

    # Keyboard with WebApp button or booking link
    web_app_url = f"https://t.me/{tenant.bot_username}/app?startapp={tenant.id}" if tenant.bot_username else None

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "💅 Записаться на услугу",
                    "web_app": {"url": f"https://yourdomain.com/twa?tenant_id={tenant.id}"},
                }
            ],
            [
                {"text": "📋 Мои записи", "callback_data": "my_bookings"},
                {"text": "🎁 Активировать Бонус", "callback_data": "my_bonuses"},
            ],
        ]
    }

    bot_token = await NotificationService.get_tenant_bot_token(tenant)
    await NotificationService.send_telegram_message(
        bot_token, chat_id, welcome_text, reply_markup=keyboard
    )
