"""
BeautyCRM — Multi-Bot Telegram Update Dispatcher
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import Tenant
from app.bot.handlers.start import handle_start_command
from app.services.notification_service import NotificationService
from app.models.appointment import Appointment
from uuid import UUID


async def dispatch_telegram_update(
    db: AsyncSession, tenant: Tenant, update: dict
):
    """
    Parse incoming raw Telegram update and dispatch to specific handler.
    """
    bot_token = await NotificationService.get_tenant_bot_token(tenant)

    # 1. Message update
    message = update.get("message")
    if message:
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        from_user = message.get("from", {})

        if text.startswith("/start"):
            await handle_start_command(db, tenant, chat_id, from_user)
            return

    # 2. Callback query update (confirmation/cancellation buttons)
    callback_query = update.get("callback_query")
    if callback_query:
        cb_id = callback_query.get("id")
        chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
        data = callback_query.get("data", "")

        if data.startswith("confirm_appt:"):
            appt_id_str = data.split(":")[1]
            appt = await db.get(Appointment, UUID(appt_id_str))
            if appt:
                appt.client_confirmed = True
                await db.commit()
                await NotificationService.send_telegram_message(
                    bot_token, chat_id, "✅ Спасибо! Ваш визит подтвержден."
                )

        elif data.startswith("cancel_appt:"):
            appt_id_str = data.split(":")[1]
            appt = await db.get(Appointment, UUID(appt_id_str))
            if appt:
                appt.status = "cancelled"
                appt.cancelled_by = "client"
                appt.cancel_reason = "Cancelled via reminder button"
                await db.commit()
                await NotificationService.send_telegram_message(
                    bot_token, chat_id, "❌ Ваша запись отменена. Будем рады видеть вас в следующий раз!"
                )

                # Notify master
                if tenant.telegram_user_id:
                    await NotificationService.send_telegram_message(
                        bot_token,
                        tenant.telegram_user_id,
                        f"⚠️ Клиент отменил запись на {appt.start_time.strftime('%d.%m в %H:%M')}",
                    )
