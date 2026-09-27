"""
BeautyCRM — Application Configuration
Uses pydantic-settings to load from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ---- App ----
    app_name: str = "BeautyCRM"
    app_env: str = "development"
    debug: bool = True

    # ---- Database ----
    database_url: str = Field(
        default="postgresql+asyncpg://beautycrm:beautycrm_secret@localhost:5432/beautycrm"
    )
    database_url_sync: str = Field(
        default="postgresql://beautycrm:beautycrm_secret@localhost:5432/beautycrm"
    )

    # ---- Redis ----
    redis_url: str = "redis://localhost:6379/0"

    # ---- Security ----
    secret_key: str = "change-me-to-a-random-64-char-string"
    encryption_key: str = "change-me-to-a-32-byte-hex-key-00112233445566778899aabbccddeeff"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # ---- Stripe ----
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_success_url: str = "https://yourdomain.com/payment/success"
    stripe_cancel_url: str = "https://yourdomain.com/payment/cancel"

    # ---- Telegram ----
    telegram_bot_token: str = ""
    superadmin_telegram_id: int = 0
    webhook_base_url: str = "https://yourdomain.com"

    # ---- Celery ----
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # ---- Slot Lock ----
    slot_lock_ttl_seconds: int = 600  # 10 minutes

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
