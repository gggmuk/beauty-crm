"""
BeautyCRM — ORM Models Package
Imports all models so Alembic can discover them.
"""

from app.models.tenant import Tenant
from app.models.service import Service, ServiceCategory
from app.models.schedule import Schedule, ScheduleOverride, BreakTime
from app.models.client import Client
from app.models.appointment import Appointment
from app.models.subscription import SubscriptionPlan
from app.models.referral import Referral, LoyaltyTransaction

__all__ = [
    "Tenant",
    "Service",
    "ServiceCategory",
    "Schedule",
    "ScheduleOverride",
    "BreakTime",
    "Client",
    "Appointment",
    "SubscriptionPlan",
    "Referral",
    "LoyaltyTransaction",
]
