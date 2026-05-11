from __future__ import annotations

import pytest

from app.core.config import Settings


def _set_valid_production_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@example.com:5432/app")
    monkeypatch.setenv("SECRET_KEY", "a-very-strong-secret-key-for-production")
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "https://project-pulse.example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "strong-admin-pass123")
    monkeypatch.setenv("AUTH_RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("EMAIL_BACKEND", "smtp")
    monkeypatch.setenv("EMAIL_FROM_EMAIL", "noreply@example.com")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")


def test_production_rejects_insecure_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_valid_production_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", "replace-this-secret-in-production")

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        Settings.from_env()


def test_production_rejects_low_entropy_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_valid_production_env(monkeypatch)
    monkeypatch.setenv("SECRET_KEY", "a" * 40)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        Settings.from_env()


def test_production_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_valid_production_env(monkeypatch)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        Settings.from_env()


def test_production_rejects_wildcard_cors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_valid_production_env(monkeypatch)
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "*")

    with pytest.raises(RuntimeError, match="Wildcard CORS"):
        Settings.from_env()


def test_production_rejects_runtime_table_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_valid_production_env(monkeypatch)
    monkeypatch.setenv("AUTO_CREATE_TABLES", "true")

    with pytest.raises(RuntimeError, match="AUTO_CREATE_TABLES"):
        Settings.from_env()


def test_postgres_url_is_normalized_for_psycopg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_valid_production_env(monkeypatch)

    settings = Settings.from_env()

    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.docs_enabled is False
    assert settings.auto_create_tables is False


def test_production_requires_redis_rate_limit_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_valid_production_env(monkeypatch)
    monkeypatch.setenv("AUTH_RATE_LIMIT_BACKEND", "memory")
    monkeypatch.delenv("REDIS_URL", raising=False)

    with pytest.raises(RuntimeError, match="AUTH_RATE_LIMIT_BACKEND=redis"):
        Settings.from_env()


def test_redis_rate_limit_backend_requires_redis_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_RATE_LIMIT_BACKEND", "redis")
    monkeypatch.delenv("REDIS_URL", raising=False)

    with pytest.raises(RuntimeError, match="REDIS_URL"):
        Settings.from_env()


def test_production_requires_smtp_email_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_valid_production_env(monkeypatch)
    monkeypatch.setenv("EMAIL_BACKEND", "console")

    with pytest.raises(RuntimeError, match="EMAIL_BACKEND=smtp"):
        Settings.from_env()


def test_smtp_email_backend_requires_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EMAIL_BACKEND", "smtp")
    monkeypatch.delenv("SMTP_HOST", raising=False)

    with pytest.raises(RuntimeError, match="SMTP_HOST"):
        Settings.from_env()
