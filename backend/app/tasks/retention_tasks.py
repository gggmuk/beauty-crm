"""
BeautyCRM — Celery Retention Engine Task
"""

import asyncio

from app.database import async_session_factory
from app.services.retention_service import RetentionService
from app.tasks.celery_app import celery_app


async def _process_retention_scan():
    async with async_session_factory() as session:
        return await RetentionService.scan_and_reactivate(session)


@celery_app.task
def run_daily_retention_scan():
    """Celery task executing daily client retention scan."""
    messages_sent = asyncio.run(_process_retention_scan())
    return f"Retention scan completed. {messages_sent} promo messages sent."
