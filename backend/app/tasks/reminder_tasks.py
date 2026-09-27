"""
BeautyCRM — Celery Reminder Tasks
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_

from app.database import async_session_factory
from app.models.appointment import Appointment
from app.services.notification_service import NotificationService
from app.tasks.celery_app import celery_app


async def _process_reminders():
    now = datetime.now(timezone.utc)
    target_24h_start = now + timedelta(hours=23)
    target_24h_end = now + timedelta(hours=25)

    target_2h_start = now + timedelta(hours=1, minutes=45)
    target_2h_end = now + timedelta(hours=2, minutes=15)

    async with async_session_factory() as session:
        # 1. 24h reminders
        q_24h = await session.execute(
            select(Appointment).where(
                and_(
                    Appointment.status == "confirmed",
                    Appointment.reminder_24h_sent == False,
                    Appointment.start_time >= target_24h_start,
                    Appointment.start_time <= target_24h_end,
                )
            )
        )
        appts_24h = q_24h.scalars().all()
        for appt in appts_24h:
            await NotificationService.send_24h_reminder(session, appt)

        # 2. 2h reminders
        q_2h = await session.execute(
            select(Appointment).where(
                and_(
                    Appointment.status == "confirmed",
                    Appointment.reminder_2h_sent == False,
                    Appointment.start_time >= target_2h_start,
                    Appointment.start_time <= target_2h_end,
                )
            )
        )
        appts_2h = q_2h.scalars().all()
        for appt in appts_2h:
            await NotificationService.send_2h_reminder(session, appt)


@celery_app.task
def check_and_send_reminders():
    """Celery task running async reminder checks."""
    asyncio.run(_process_reminders())
