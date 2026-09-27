from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.services import router as services_router
from app.api.v1.schedules import router as schedules_router
from app.api.v1.appointments import router as appointments_router
from app.api.v1.clients import router as clients_router
from app.api.v1.bot import router as bot_router
from app.api.v1.payments import router as payments_router
from app.api.v1.superadmin import router as superadmin_router

api_v1_router = APIRouter(prefix="/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(tenants_router)
api_v1_router.include_router(services_router)
api_v1_router.include_router(schedules_router)
api_v1_router.include_router(appointments_router)
api_v1_router.include_router(clients_router)
api_v1_router.include_router(bot_router)
api_v1_router.include_router(payments_router)
api_v1_router.include_router(superadmin_router)
