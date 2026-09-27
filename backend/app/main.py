"""
BeautyCRM / BotBuilder SaaS — Backend Main Application
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_v1_router
from app.config import get_settings
from app.database import Base, engine
from app.middleware.tenant_middleware import MultiTenantMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("beautycrm")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler (startup & shutdown)."""
    logger.info("🚀 Starting BeautyCRM SaaS Backend...")

    # Auto-create tables in development mode if needed
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    logger.info("👋 Shutting down BeautyCRM SaaS Backend...")
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Multi-tenant platform for beauty masters, studios, and influencers. "
        "Provides online booking, prepayments, Telegram bot integration, and client retention engine."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Multi-Tenant Context Middleware
app.add_middleware(MultiTenantMiddleware)

# Include API v1 Router
app.include_router(api_v1_router, prefix="/api")


@app.get("/health", tags=["System"])
async def health_check():
    """Healthcheck endpoint for Docker / K8s probes."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.app_env,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
