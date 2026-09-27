"""
BeautyCRM — Retention Engine Service

Scans tenant client bases for clients who haven't visited in 30+ days and have no future appointments.
Sends automated promo/reactivation messages to boost client retention.
"""

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import select, and_, not_, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.appointment import Appointment
from app.models.tenant import Tenant
from app.services.notification_service import NotificationService


class RetentionService:

    @classmethod
    async def scan_and_reactivate(cls, db: AsyncSession) -> int:
        """
        Scan all active tenants and find lost/at-risk clients.
        Sends promo messages and updates client status to 'at_risk'.
        
        Returns total number of reactivation messages sent.
        """
        # Fetch active tenants
        tenants_q = await db.execute(select(Tenant).where(Tenant.is_active == True))
        tenants = tenants_q.scalars().all()

        total_sent = 0
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

        for tenant in tenants:
            # Subquery to check if client has any upcoming appointments
            upcoming_subq = exists().where(
                and_(
                    Appointment.client_id == Client.id,
                    Appointment.status.in_(["pending_payment", "confirmed"]),
                    Appointment.start_time > datetime.now(timezone.utc),
                )
            )

            # Query at-risk clients
            at_risk_q = await db.execute(
                select(Client).where(
                    and_(
                        Client.tenant_id == tenant.id,
                        Client.last_visit_at.is_not(None),
                        Client.last_visit_at < cutoff_date,
                        Client.is_blocked == False,
                        not_(upcoming_subq),
                    )
                )
            )
            at_risk_clients = at_risk_q.scalars().all()

            bot_token = await NotificationService.get_tenant_bot_token(tenant)

            for client in at_risk_clients:
                if not client.telegram_id:
                    continue

                promo_text = (
                    f"Привет, {client.name or 'красотка'}! ✨\n\n"
                    f"Прошел уже месяц с вашего последнего визита к мастеру <b>{tenant.name}</b>.\n"
                    f"Мы скучаем! 💖 Запишитесь на этой неделе и получите подарок/скидку при визите."
                )

                sent = await NotificationService.send_telegram_message(
                    bot_token, client.telegram_id, promo_text
                )
                if sent:
                    client.status = "at_risk"
                    total_sent += 1

            await db.commit()

        return total_sent
