"""
Application configuration.
Loads settings from environment variables and .env file.
"""

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings


# Directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "FinMate"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'finmate.db'}"

    # AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-flash-latest"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = {
        "env_file": (
            str(PROJECT_ROOT / ".env"),
            str(BASE_DIR / ".env"),
        ),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
