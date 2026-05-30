"""Application configuration, loaded from environment (see .env.example)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Infra
    database_url: str = "postgresql+psycopg://shighlight:shighlight@localhost:5432/streamhighlighter"
    redis_url: str = "redis://localhost:6379/0"

    # Object storage (S3-compatible)
    storage_endpoint: str | None = None
    storage_region: str = "auto"
    storage_bucket: str = "streamhighlighter-media"
    storage_access_key_id: str | None = None
    storage_secret_access_key: str | None = None

    # Trust boundary: the web tier signs proxied requests with this secret.
    internal_api_secret: str = "change-me"

    # AI / pipeline
    anthropic_api_key: str | None = None
    transcribe_backend: str = "local"  # "local" (faster-whisper) | "openai"
    openai_api_key: str | None = None

    # Source / publish platform credentials
    twitch_api_client_id: str | None = None
    twitch_api_client_secret: str | None = None
    youtube_client_id: str | None = None
    youtube_client_secret: str | None = None
    tiktok_client_key: str | None = None
    tiktok_client_secret: str | None = None
    instagram_app_id: str | None = None
    instagram_app_secret: str | None = None

    @property
    def sqlalchemy_url(self) -> str:
        """Normalize to the psycopg v3 driver SQLAlchemy expects."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
