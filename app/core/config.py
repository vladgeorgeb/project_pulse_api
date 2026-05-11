from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env", override=False)

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

LOCAL_DATABASE_URL = f"sqlite:///{DATA_DIR / 'project_pulse.db'}"
LOCAL_SECRET_KEY = "local-development-secret-change-me"
INSECURE_SECRET_KEYS = {
    "",
    "replace-this-secret-in-production",
    LOCAL_SECRET_KEY,
    "test-secret-key",
}
Environment = Literal["local", "development", "test", "production"]


def _get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    api_v1_prefix: str
    environment: Environment
    secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    database_url: str
    debug: bool
    admin_email: str
    admin_password: str
    cors_origins: tuple[str, ...]
    docs_enabled: bool
    auto_create_tables: bool
    run_startup_migrations: bool
    log_level: str

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @classmethod
    def from_env(cls) -> "Settings":
        environment = os.getenv("ENVIRONMENT", "local").strip().lower()
        if environment not in {"local", "development", "test", "production"}:
            raise RuntimeError(
                "ENVIRONMENT must be one of: local, development, test, production."
            )

        database_url = os.getenv("DATABASE_URL", LOCAL_DATABASE_URL)
        cors_default = "http://localhost:5173,http://127.0.0.1:5173"
        cors_value = os.getenv("BACKEND_CORS_ORIGINS") or os.getenv("CORS_ORIGINS")
        cors_origins = tuple(
            item.strip()
            for item in (cors_value or cors_default).split(",")
            if item.strip()
        )

        settings = cls(
            app_name=os.getenv("APP_NAME", "Project Pulse API"),
            api_v1_prefix=os.getenv("API_V1_PREFIX", "/api/v1"),
            environment=environment,  # type: ignore[arg-type]
            secret_key=os.getenv("SECRET_KEY", LOCAL_SECRET_KEY),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(
                os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
            ),
            database_url=_normalize_database_url(database_url),
            debug=_get_bool_env("DEBUG", False),
            admin_email=os.getenv("ADMIN_EMAIL", "admin@example.com"),
            admin_password=os.getenv("ADMIN_PASSWORD", "adminpass123"),
            cors_origins=cors_origins,
            docs_enabled=_get_bool_env("DOCS_ENABLED", environment != "production"),
            auto_create_tables=_get_bool_env(
                "AUTO_CREATE_TABLES",
                environment != "production",
            ),
            run_startup_migrations=_get_bool_env(
                "RUN_STARTUP_MIGRATIONS",
                environment != "production",
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise RuntimeError(
                "LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL."
            )
        if self.jwt_algorithm != "HS256":
            raise RuntimeError("Only JWT_ALGORITHM=HS256 is currently supported.")
        if self.access_token_expire_minutes <= 0:
            raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero.")
        if not self.cors_origins:
            raise RuntimeError("At least one CORS origin must be configured.")
        if self.is_production:
            if self.debug:
                raise RuntimeError("DEBUG must be false in production.")
            if (
                self.secret_key in INSECURE_SECRET_KEYS
                or len(self.secret_key) < 32
                or len(set(self.secret_key)) < 8
            ):
                raise RuntimeError(
                    "SECRET_KEY must be set to a strong value in production."
                )
            if not os.getenv("DATABASE_URL"):
                raise RuntimeError("DATABASE_URL is required in production.")
            if self.database_url.startswith("sqlite"):
                raise RuntimeError("SQLite is not allowed in production.")
            if "*" in self.cors_origins:
                raise RuntimeError(
                    "Wildcard CORS origins are not allowed in production."
                )
            if self.auto_create_tables:
                raise RuntimeError("AUTO_CREATE_TABLES must be false in production.")
            if not self.admin_email or not self.admin_password:
                raise RuntimeError(
                    "ADMIN_EMAIL and ADMIN_PASSWORD are required in production."
                )
            if (
                self.admin_password == "adminpass123"
                or len(self.admin_password) < 12
                or not any(character.isalpha() for character in self.admin_password)
                or not any(character.isdigit() for character in self.admin_password)
            ):
                raise RuntimeError(
                    "ADMIN_PASSWORD must be strong and must not use a local default."
                )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
