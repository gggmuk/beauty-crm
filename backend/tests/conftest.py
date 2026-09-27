"""
BeautyCRM — Pytest Configuration & Test Fixtures
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.tenant import Tenant
from app.models.service import Service
from app.models.schedule import Schedule
from app.security import hash_password

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_tenant(test_db: AsyncSession) -> Tenant:
    tenant = Tenant(
        name="Beauty Studio Alpha",
        telegram_user_id=123456789,
        password_hash=hash_password("password123"),
        buffer_minutes=15,
        subscription_status="active",
    )
    test_db.add(tenant)
    await test_db.commit()
    await test_db.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def sample_service(test_db: AsyncSession, sample_tenant: Tenant) -> Service:
    service = Service(
        tenant_id=sample_tenant.id,
        title="Маникюр + Покрытие",
        duration_minutes=90,
        price=2000.00,
        prepayment_amount=500.00,
    )
    test_db.add(service)
    await test_db.commit()
    await test_db.refresh(service)
    return service
