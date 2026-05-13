from __future__ import annotations

import re
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import create_access_token, hash_auth_token
from app.models.auth_token import AuthToken
from app.models.user import User
from app.services.auth_token_service import (
    EMAIL_VERIFICATION_PURPOSE,
    PASSWORD_RESET_PURPOSE,
    utc_now_naive,
)
from app.services.email_service import EmailService, local_email_outbox
from tests.conftest import TestingSessionLocal


def _extract_last_email_token() -> str:
    assert local_email_outbox
    match = re.search(r"https?://\S+", local_email_outbox[-1].text_body)
    assert match is not None
    query = parse_qs(urlparse(match.group(0)).query)
    return query["token"][0]


def _expire_token(raw_token: str, purpose: str) -> None:
    token_hash = hash_auth_token(raw_token, purpose=purpose)
    with TestingSessionLocal() as db:
        auth_token = db.execute(
            select(AuthToken).where(AuthToken.token_hash == token_hash)
        ).scalar_one()
        auth_token.expires_at = utc_now_naive() - timedelta(minutes=1)
        db.commit()


def test_register_returns_access_token_and_creates_workspace(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"

    workspace_response = client.get(
        "/api/v1/workspaces/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert workspace_response.status_code == 200, workspace_response.text
    workspace = workspace_response.json()
    assert workspace["name"] == "Dashboard"
    assert workspace["company_name"] == "Independent Contractor"
    assert workspace["projects"] == []


def test_register_creates_email_confirmation_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )

    assert response.status_code == 201, response.text
    raw_token = _extract_last_email_token()
    token_hash = hash_auth_token(raw_token, purpose=EMAIL_VERIFICATION_PURPOSE)

    with TestingSessionLocal() as db:
        user = db.execute(
            select(User).where(User.email == "user@example.com")
        ).scalar_one()
        auth_token = db.execute(
            select(AuthToken).where(
                AuthToken.user_id == user.id,
                AuthToken.purpose == EMAIL_VERIFICATION_PURPOSE,
            )
        ).scalar_one()
        assert user.email_verified is False
        assert user.email_verified_at is None
        assert auth_token.token_hash == token_hash
        assert auth_token.token_hash != raw_token


def test_auth_me_returns_current_user_identity(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "identity@example.com", "password": "strongpass123"},
    )
    assert register_response.status_code == 201, register_response.text
    token = register_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200, me_response.text
    body = me_response.json()
    assert body["email"] == "identity@example.com"
    assert body["is_admin"] is False
    assert body["email_verified"] is False


def test_confirm_email_marks_user_verified(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )
    assert response.status_code == 201, response.text
    raw_token = _extract_last_email_token()

    confirm_response = client.post(
        "/api/v1/auth/email/confirm",
        json={"token": raw_token},
    )

    assert confirm_response.status_code == 200, confirm_response.text
    with TestingSessionLocal() as db:
        user = db.execute(
            select(User).where(User.email == "user@example.com")
        ).scalar_one()
        assert user.email_verified is True
        assert user.email_verified_at is not None

    reused_response = client.post(
        "/api/v1/auth/email/confirm",
        json={"token": raw_token},
    )
    assert reused_response.status_code == 200, reused_response.text


def test_login_can_require_verified_email(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv("REQUIRE_VERIFIED_EMAIL", "true")
    get_settings.cache_clear()
    try:
        register_response = client.post(
            "/api/v1/auth/register",
            json={"email": "user@example.com", "password": "strongpass123"},
        )
        assert register_response.status_code == 202, register_response.text
        register_body = register_response.json()
        assert register_body == {
            "email_verification_required": True,
            "message": (
                "Email verification is required before login. "
                "Please check your email."
            ),
        }
        assert "access_token" not in register_body
        raw_token = _extract_last_email_token()

        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "user@example.com", "password": "strongpass123"},
        )
        assert login_response.status_code == 401

        confirm_response = client.post(
            "/api/v1/auth/email/confirm",
            json={"token": raw_token},
        )
        assert confirm_response.status_code == 200, confirm_response.text

        verified_login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "user@example.com", "password": "strongpass123"},
        )
        assert verified_login_response.status_code == 200, verified_login_response.text
    finally:
        get_settings.cache_clear()


def test_login_returns_access_token(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )
    assert register_response.status_code == 201, register_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "strongpass123"},
    )

    assert login_response.status_code == 200, login_response.text
    assert "access_token" in login_response.json()


def test_password_reset_request_does_not_reveal_email_existence(
    client: TestClient,
) -> None:
    existing_register = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )
    assert existing_register.status_code == 201, existing_register.text
    local_email_outbox.clear()

    existing_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "user@example.com"},
    )
    missing_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "missing@example.com"},
    )

    assert existing_response.status_code == 202, existing_response.text
    assert missing_response.status_code == 202, missing_response.text
    assert existing_response.json() == missing_response.json()
    assert len(local_email_outbox) == 1


def test_password_reset_request_for_missing_email_sends_no_email(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "missing@example.com"},
    )

    assert response.status_code == 202, response.text
    assert response.json() == {
        "message": (
            "If an account exists for that email, "
            "password reset instructions have been sent."
        )
    }
    assert local_email_outbox == []


def test_password_reset_request_for_existing_email_sends_email(
    client: TestClient,
) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )
    assert register_response.status_code == 201, register_response.text
    local_email_outbox.clear()

    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "user@example.com"},
    )

    assert response.status_code == 202, response.text
    assert len(local_email_outbox) == 1


def test_password_reset_request_hides_email_delivery_failure(
    client: TestClient,
    monkeypatch,
) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )
    assert register_response.status_code == 201, register_response.text
    local_email_outbox.clear()

    def fail_delivery(self, *, to_email: str, token: str) -> None:
        raise RuntimeError("SMTP unavailable")

    monkeypatch.setattr(EmailService, "send_password_reset_email", fail_delivery)

    existing_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "user@example.com"},
    )
    missing_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "missing@example.com"},
    )

    assert existing_response.status_code == 202, existing_response.text
    assert missing_response.status_code == 202, missing_response.text
    assert existing_response.json() == missing_response.json()
    assert local_email_outbox == []


def test_password_reset_valid_token_updates_password(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )
    assert register_response.status_code == 201, register_response.text
    local_email_outbox.clear()

    request_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "user@example.com"},
    )
    assert request_response.status_code == 202, request_response.text
    raw_token = _extract_last_email_token()
    token_hash = hash_auth_token(raw_token, purpose=PASSWORD_RESET_PURPOSE)

    with TestingSessionLocal() as db:
        auth_token = db.execute(
            select(AuthToken).where(AuthToken.token_hash == token_hash)
        ).scalar_one()
        assert auth_token.token_hash != raw_token
        assert auth_token.used_at is None

    confirm_response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "newstrongpass123"},
    )

    assert confirm_response.status_code == 200, confirm_response.text
    old_login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "strongpass123"},
    )
    assert old_login_response.status_code == 401
    new_login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "newstrongpass123"},
    )
    assert new_login_response.status_code == 200, new_login_response.text


def test_password_reset_expired_token_is_rejected(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )
    assert register_response.status_code == 201, register_response.text
    local_email_outbox.clear()
    request_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "user@example.com"},
    )
    assert request_response.status_code == 202, request_response.text
    raw_token = _extract_last_email_token()
    _expire_token(raw_token, PASSWORD_RESET_PURPOSE)

    confirm_response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "newstrongpass123"},
    )

    assert confirm_response.status_code == 400
    old_login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "strongpass123"},
    )
    assert old_login_response.status_code == 200, old_login_response.text


def test_password_reset_reused_token_is_rejected(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )
    assert register_response.status_code == 201, register_response.text
    local_email_outbox.clear()
    request_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "user@example.com"},
    )
    assert request_response.status_code == 202, request_response.text
    raw_token = _extract_last_email_token()

    first_confirm_response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "newstrongpass123"},
    )
    second_confirm_response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "otherstrongpass123"},
    )

    assert first_confirm_response.status_code == 200, first_confirm_response.text
    assert second_confirm_response.status_code == 400
    new_login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "newstrongpass123"},
    )
    assert new_login_response.status_code == 200, new_login_response.text
    other_login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "otherstrongpass123"},
    )
    assert other_login_response.status_code == 401


def test_password_reset_invalid_token_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "not-a-real-token", "new_password": "newstrongpass123"},
    )

    assert response.status_code == 400


def test_duplicate_registration_returns_409(client: TestClient) -> None:
    payload = {"email": "user@example.com", "password": "strongpass123"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409


def test_weak_password_registration_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "password"},
    )

    assert response.status_code == 422


def test_login_with_wrong_password_returns_401(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 401


def test_login_rate_limit_applies_by_email_without_leaking_existence(
    client: TestClient,
) -> None:
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "missing@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "missing@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 429
    assert response.json()["detail"] == "Too many attempts. Please try again later."
    assert "Retry-After" in response.headers


def test_register_rate_limit_applies_by_ip(client: TestClient) -> None:
    for index in range(3):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"user-{index}@example.com",
                "password": "strongpass123",
            },
        )
        assert response.status_code == 201, response.text

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "user-4@example.com", "password": "strongpass123"},
    )

    assert response.status_code == 429
    assert response.json()["detail"] == "Too many attempts. Please try again later."
    assert "Retry-After" in response.headers


def test_invalid_token_returns_401(client: TestClient) -> None:
    response = client.get(
        "/api/v1/workspaces/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401


def test_expired_token_returns_401(client: TestClient) -> None:
    token = create_access_token("1", expires_delta=timedelta(minutes=-1))

    response = client.get(
        "/api/v1/workspaces/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_token_for_missing_user_returns_401(client: TestClient) -> None:
    token = create_access_token("999999")

    response = client.get(
        "/api/v1/workspaces/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_verified_email_required_blocks_authenticated_request(
    client: TestClient,
    monkeypatch,
) -> None:
    monkeypatch.setenv("REQUIRE_VERIFIED_EMAIL", "true")
    get_settings.cache_clear()
    try:
        register_response = client.post(
            "/api/v1/auth/register",
            json={"email": "blocked@example.com", "password": "strongpass123"},
        )
        assert register_response.status_code == 202, register_response.text

        token = create_access_token("2")
        response = client.get(
            "/api/v1/workspaces/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "Email address must be verified."
    finally:
        get_settings.cache_clear()


def test_protected_endpoint_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/projects")

    assert response.status_code == 401
