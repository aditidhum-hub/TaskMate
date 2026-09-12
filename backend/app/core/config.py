"""Core application configuration using Pydantic BaseSettings."""

import json
import logging
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env files."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General App Settings
    APP_NAME: str = "TaskMate Backend"
    APP_VERSION: str = "0.5.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS Settings
    CORS_ORIGINS: list[str] | str = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # LLM Settings (Nemotron runtime agent - Phase 6)
    LLM_PROVIDER: str = "nemotron"
    LLM_MODEL: str = "nvidia/nemotron-4-340b-instruct"
    LLM_API_KEY: str = ""
    NVIDIA_API_KEY: str = ""
    LLM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_BASE_URL: str = ""
    LLM_TIMEOUT: float = 30.0

    @property
    def effective_api_key(self) -> str:
        """Return the effective API key for the LLM service."""
        return self.NVIDIA_API_KEY or self.LLM_API_KEY

    @property
    def effective_base_url(self) -> str:
        """Return the effective base URL for the LLM service."""
        return self.NVIDIA_BASE_URL or self.LLM_BASE_URL

    # Firebase Settings (Authentication & Firestore - Phase 2 & 3)
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_PRIVATE_KEY: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed]
                except (json.JSONDecodeError, ValueError) as err:
                    logger.debug("Could not parse CORS_ORIGINS as JSON: %s", err)
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
