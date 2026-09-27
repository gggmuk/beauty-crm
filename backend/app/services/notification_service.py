"""
BeautyCRM — Telegram Notification Service

Sends automated Telegram messages to clients and masters:
1. Appointment Confirmation (Client + Master)
2. 24-hour reminder with [Confirm] / [Cancel] buttons
3. 2-hour reminder with address
4. Reactivation promo messages (Retention)
"""

import logging
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.appointment import Appointment
from app.models.client import Client
from app.models.service import Service
from app.models.tenant import Tenant
from app.security import decrypt_token

logger = logging.getLogger(__name__)
settings = get_settings()


class NotificationService:

    @classmethod
    async def send_telegram_message(
        cls,
        bot_token: str,
        chat_id: int,
        text: str,
        reply_markup: dict = None,
    ) -> bool:
        """Send a Telegram message via HTTP API."""
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, json=payload)
                return resp.status_code == 200
            except Exception as e:
                logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
                return False

    @classmethod
    async def get_tenant_bot_token(cls, tenant: Tenant) -> str:
        """Decrypt tenant's bot token or fallback to platform bot token."""
        if tenant.bot_token_encrypted:
            try:
                return decrypt_token(tenant.bot_token_encrypted)
            except Exception:
                pass
        return settings.telegram_bot_token

    @classmethod
    async def notify_appointment_confirmed(
        cls, db: AsyncSession, appointment: Appointment
    ):
        """Notify client and master when an appointment is confirmed."""
        tenant = await db.get(Tenant, appointment.tenant_id)
        client = await db.get(Client, appointment.client_id)
        service = await db.get(Service, appointment.service_id)

        if not tenant or not client or not service:
            return

        bot_token = await cls.get_tenant_bot_token(tenant)
        start_str = appointment.start_time.strftime("%d.%m.%Y в %H:%M")

        # 1. Message to Client
        client_text = (
            f"✅ <b>Запись подтверждена!</b>\n\n"
            f"💅 <b>Услуга:</b> {service.title}\n"
            f"🕒 <b>Дата и время:</b> {start_str}\n"
            f"💰 <b>Стоимость:</b> {service.price} ₽\n"
            f"📍 <b>Мастер:</b> {tenant.name}\n\n"
            f"Ждем вас!"
        )
        if client.telegram_id:
            await cls.send_telegram_message(bot_token, client.telegram_id, client_text)

        # 2. Push-notification to Master
        master_text = (
            f"🔔 <b>Новая запись!</b>\n\n"
            f"👤 <b>Клиент:</b> {client.name or 'Без имени'} ({client.phone or 'без телефона'})\n"
            f"💅 <b>Услуга:</b> {service.title}\n"
            f"🕒 <b>Время:</b> {start_str}\n"
            f"💵 <b>Предоплата:</b> {appointment.prepayment_amount} ₽"
        )
        if tenant.telegram_user_id:
            await cls.send_telegram_message(bot_token, tenant.telegram_user_id, master_text)

    @classmethod
    async def send_24h_reminder(cls, db: AsyncSession, appointment: Appointment):
        """Send 24-hour reminder with interactive confirmation buttons."""
        tenant = await db.get(Tenant, appointment.tenant_id)
        client = await db.get(Client, appointment.client_id)
        service = await db.get(Service, appointment.service_id)

        if not tenant or not client or not service or not client.telegram_id:
            return

        bot_token = await cls.get_tenant_bot_token(tenant)
        start_str = appointment.start_time.strftime("%H:%M")

        text = (
            f"⏰ <b>Напоминание о визите завтра!</b>\n\n"
            f"Завтра в <b>{start_str}</b> у вас запись на <b>{service.title}</b>.\n"
            f"Пожалуйста, подтвердите визит:"
        )

        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "✅ Подтверждаю",
                        "callback_data": f"confirm_appt:{appointment.id}",
                    },
                    {
                        "text": "❌ Не смогу приехать",
                        "callback_data": f"cancel_appt:{appointment.id}",
                    },
                ]
            ]
        }

        success = await cls.send_telegram_message(
            bot_token, client.telegram_id, text, reply_markup=keyboard
        )
        if success:
            appointment.reminder_24h_sent = True
            await db.commit()

    @classmethod
    async def send_2h_reminder(cls, db: AsyncSession, appointment: Appointment):
        """Send 2-hour reminder."""
        tenant = await db.get(Tenant, appointment.tenant_id)
        client = await db.get(Client, appointment.client_id)
        service = await db.get(Service, appointment.service_id)

        if not tenant or not client or not service or not client.telegram_id:
            return

        bot_token = await cls.get_tenant_bot_token(tenant)
        start_str = appointment.start_time.strftime("%H:%M")

        text = (
            f"🚕 <b>Визит через 2 часа!</b>\n\n"
            f"Сегодня в <b>{start_str}</b> ждем вас на <b>{service.title}</b>.\n"
            f"До встречи!"
        )

        success = await cls.send_telegram_message(
            bot_token, client.telegram_id, text
        )
        if success:
            appointment.reminder_2h_sent = True
            await db.commit()
