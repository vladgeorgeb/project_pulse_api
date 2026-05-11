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
RateLimitBackend = Literal["memory", "redis"]
EmailBackend = Literal["console", "smtp"]


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
    auth_rate_limit_enabled: bool
    auth_rate_limit_backend: RateLimitBackend
    redis_url: str | None
    login_rate_limit_ip_attempts: int
    login_rate_limit_email_attempts: int
    login_rate_limit_window_seconds: int
    register_rate_limit_ip_attempts: int
    register_rate_limit_email_attempts: int
    register_rate_limit_window_seconds: int
    password_reset_token_expire_minutes: int
    email_verification_token_expire_minutes: int
    require_verified_email: bool
    frontend_base_url: str
    email_backend: EmailBackend
    email_from_email: str
    email_from_name: str
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_use_tls: bool
    smtp_use_ssl: bool

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
        auth_rate_limit_backend = (
            os.getenv(
                "AUTH_RATE_LIMIT_BACKEND",
                "redis" if os.getenv("REDIS_URL") else "memory",
            )
            .strip()
            .lower()
        )
        if auth_rate_limit_backend not in {"memory", "redis"}:
            raise RuntimeError("AUTH_RATE_LIMIT_BACKEND must be one of: memory, redis.")
        email_backend = (
            os.getenv(
                "EMAIL_BACKEND", "smtp" if environment == "production" else "console"
            )
            .strip()
            .lower()
        )
        if email_backend not in {"console", "smtp"}:
            raise RuntimeError("EMAIL_BACKEND must be one of: console, smtp.")

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
            auth_rate_limit_enabled=_get_bool_env("AUTH_RATE_LIMIT_ENABLED", True),
            auth_rate_limit_backend=auth_rate_limit_backend,  # type: ignore[arg-type]
            redis_url=os.getenv("REDIS_URL"),
            login_rate_limit_ip_attempts=int(
                os.getenv("LOGIN_RATE_LIMIT_IP_ATTEMPTS", "5")
            ),
            login_rate_limit_email_attempts=int(
                os.getenv("LOGIN_RATE_LIMIT_EMAIL_ATTEMPTS", "5")
            ),
            login_rate_limit_window_seconds=int(
                os.getenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "60")
            ),
            register_rate_limit_ip_attempts=int(
                os.getenv("REGISTER_RATE_LIMIT_IP_ATTEMPTS", "3")
            ),
            register_rate_limit_email_attempts=int(
                os.getenv("REGISTER_RATE_LIMIT_EMAIL_ATTEMPTS", "3")
            ),
            register_rate_limit_window_seconds=int(
                os.getenv("REGISTER_RATE_LIMIT_WINDOW_SECONDS", "60")
            ),
            password_reset_token_expire_minutes=int(
                os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "30")
            ),
            email_verification_token_expire_minutes=int(
                os.getenv("EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES", "1440")
            ),
            require_verified_email=_get_bool_env("REQUIRE_VERIFIED_EMAIL", False),
            frontend_base_url=os.getenv(
                "FRONTEND_BASE_URL",
                "http://localhost:5173",
            ).rstrip("/"),
            email_backend=email_backend,  # type: ignore[arg-type]
            email_from_email=os.getenv("EMAIL_FROM_EMAIL", "noreply@example.com"),
            email_from_name=os.getenv("EMAIL_FROM_NAME", "Project Pulse"),
            smtp_host=os.getenv("SMTP_HOST") or None,
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME") or None,
            smtp_password=os.getenv("SMTP_PASSWORD") or None,
            smtp_use_tls=_get_bool_env("SMTP_USE_TLS", True),
            smtp_use_ssl=_get_bool_env("SMTP_USE_SSL", False),
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
        rate_limit_values = {
            "LOGIN_RATE_LIMIT_IP_ATTEMPTS": self.login_rate_limit_ip_attempts,
            "LOGIN_RATE_LIMIT_EMAIL_ATTEMPTS": self.login_rate_limit_email_attempts,
            "LOGIN_RATE_LIMIT_WINDOW_SECONDS": self.login_rate_limit_window_seconds,
            "REGISTER_RATE_LIMIT_IP_ATTEMPTS": self.register_rate_limit_ip_attempts,
            "REGISTER_RATE_LIMIT_EMAIL_ATTEMPTS": (
                self.register_rate_limit_email_attempts
            ),
            "REGISTER_RATE_LIMIT_WINDOW_SECONDS": (
                self.register_rate_limit_window_seconds
            ),
        }
        invalid_rate_limit_names = [
            name for name, value in rate_limit_values.items() if value <= 0
        ]
        if invalid_rate_limit_names:
            raise RuntimeError(
                f"{invalid_rate_limit_names[0]} must be greater than zero."
            )
        if self.password_reset_token_expire_minutes <= 0:
            raise RuntimeError(
                "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES must be greater than zero."
            )
        if self.email_verification_token_expire_minutes <= 0:
            raise RuntimeError(
                "EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES must be greater than zero."
            )
        if not self.frontend_base_url:
            raise RuntimeError("FRONTEND_BASE_URL must not be empty.")
        if self.smtp_port <= 0:
            raise RuntimeError("SMTP_PORT must be greater than zero.")
        if self.smtp_use_tls and self.smtp_use_ssl:
            raise RuntimeError("Only one of SMTP_USE_TLS or SMTP_USE_SSL can be true.")
        if (self.smtp_username and not self.smtp_password) or (
            self.smtp_password and not self.smtp_username
        ):
            raise RuntimeError(
                "SMTP_USERNAME and SMTP_PASSWORD must be configured together."
            )
        if self.auth_rate_limit_backend == "redis" and not self.redis_url:
            raise RuntimeError(
                "REDIS_URL is required when AUTH_RATE_LIMIT_BACKEND=redis."
            )
        if self.email_backend == "smtp":
            if not self.smtp_host:
                raise RuntimeError("SMTP_HOST is required when EMAIL_BACKEND=smtp.")
            if not self.email_from_email:
                raise RuntimeError(
                    "EMAIL_FROM_EMAIL is required when EMAIL_BACKEND=smtp."
                )
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
            if self.email_backend != "smtp":
                raise RuntimeError("EMAIL_BACKEND=smtp is required in production.")
            if self.database_url.startswith("sqlite"):
                raise RuntimeError("SQLite is not allowed in production.")
            if "*" in self.cors_origins:
                raise RuntimeError(
                    "Wildcard CORS origins are not allowed in production."
                )
            if self.auto_create_tables:
                raise RuntimeError("AUTO_CREATE_TABLES must be false in production.")
            if self.auth_rate_limit_enabled and self.auth_rate_limit_backend != "redis":
                raise RuntimeError(
                    "AUTH_RATE_LIMIT_BACKEND=redis is required in production."
                )
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
