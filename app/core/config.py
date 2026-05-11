from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR / 'project_pulse.db'}"


def _parse_csv_env(name: str, default: str) -> tuple[str, ...]:
    value = os.getenv(name, default)
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Project Pulse API")
    api_v1_prefix: str = os.getenv("API_V1_PREFIX", "/api/v1")
    secret_key: str = os.getenv("SECRET_KEY", "replace-this-secret-in-production")
    access_token_expire_minutes: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    database_url: str = os.getenv("DATABASE_URL", DATABASE_URL)
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "adminpass123")
    cors_origins: tuple[str, ...] = _parse_csv_env(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
