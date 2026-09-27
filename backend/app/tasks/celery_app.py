"""
BeautyCRM — Celery Application & Schedule Setup
"""

from celery import Celery
from celery.schedules import crontab
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "beautycrm",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.reminder_tasks",
        "app.tasks.retention_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Celery Beat Periodic Tasks Schedule
celery_app.conf.beat_schedule = {
    # Check 24h & 2h reminders every 15 minutes
    "check-reminders-every-15-min": {
        "task": "app.tasks.reminder_tasks.check_and_send_reminders",
        "schedule": 900.0,  # 15 minutes in seconds
    },
    # Scan lost/at-risk clients daily at 10:00 UTC
    "daily-retention-scan": {
        "task": "app.tasks.retention_tasks.run_daily_retention_scan",
        "schedule": crontab(hour=10, minute=0),
    },
}
