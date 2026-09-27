"""
BeautyCRM — Appointment API Tests
"""

import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from app.models.tenant import Tenant
from app.models.service import Service


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_and_login_tenant(client: AsyncClient):
    # Register
    reg_payload = {
        "name": "Studio Elegance",
        "telegram_user_id": 987654321,
        "phone": "+79990001122",
        "password": "secretpassword",
    }
    res_reg = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res_reg.status_code == 201
    assert res_reg.json()["name"] == "Studio Elegance"

    # Login
    login_payload = {
        "telegram_user_id": 987654321,
        "password": "secretpassword",
    }
    res_login = await client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()


@pytest.mark.asyncio
async def test_create_appointment(
    client: AsyncClient, sample_tenant: Tenant, sample_service: Service
):
    start_time = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=14, minute=0, second=0, microsecond=0
    )

    booking_payload = {
        "service_id": str(sample_service.id),
        "start_time": start_time.isoformat(),
        "client_name": "Елена",
        "client_phone": "+79001234567",
        "client_telegram_id": 11223344,
        "notes": "Первый визит",
    }

    url = f"/api/v1/appointments?tenant_id={sample_tenant.id}"
    res = await client.post(url, json=booking_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["tenant_id"] == str(sample_tenant.id)
    assert data["status"] == "pending_payment"
    assert float(data["prepayment_amount"]) == 500.00
