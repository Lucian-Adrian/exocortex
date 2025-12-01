"""
Configuration management for Exo.

Loads settings from environment variables with validation.
Uses pydantic-settings for type-safe configuration.
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Find .env file relative to this file
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required: Supabase connection
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Required: Gemini AI
    GEMINI_API_KEY: str

    # Optional: Gemini model configuration (hot-swappable)
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"

    # Optional: API settings
    EXO_API_KEY: str | None = None
    EXO_DEBUG: bool = False

    # Optional: LLMOps
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Settings are loaded once and cached for the application lifetime.
    Call `get_settings.cache_clear()` to reload from environment.
    """
    return Settings()


# Convenience alias for direct import
settings = get_settings()
