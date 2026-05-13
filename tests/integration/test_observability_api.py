from __future__ import annotations

import logging

from fastapi.testclient import TestClient

from app.core.observability import REQUEST_ID_HEADER


def _headers(token: str, request_id: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if request_id is not None:
        headers[REQUEST_ID_HEADER] = request_id
    return headers


def _register(client: TestClient, email: str = "user@example.com") -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "strongpass123"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _login_admin(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "adminpass123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _records_for_event(caplog, event: str):
    return [
        record for record in caplog.records if getattr(record, "event", None) == event
    ]


def test_request_id_header_and_request_log(
    client: TestClient,
    caplog,
) -> None:
    request_id = "test-request-id"

    with caplog.at_level(logging.INFO):
        response = client.get("/health", headers={REQUEST_ID_HEADER: request_id})

    assert response.status_code == 200, response.text
    assert response.headers[REQUEST_ID_HEADER] == request_id

    records = _records_for_event(caplog, "api.request")
    assert records
    record = records[-1]
    assert record.method == "GET"
    assert record.path == "/health"
    assert record.status_code == 200
    assert record.request_id == request_id
    assert record.user_id is None


def test_authenticated_request_log_includes_user_id(
    client: TestClient,
    caplog,
) -> None:
    token = _register(client, email="identity@example.com")
    request_id = "auth-request-id"
    caplog.clear()

    with caplog.at_level(logging.INFO):
        response = client.get(
            "/api/v1/auth/me",
            headers=_headers(token, request_id),
        )

    assert response.status_code == 200, response.text
    records = _records_for_event(caplog, "api.request")
    assert records
    record = records[-1]
    assert record.path == "/api/v1/auth/me"
    assert record.request_id == request_id
    assert record.user_id == response.json()["id"]


def test_login_failure_logs_safe_business_event(
    client: TestClient,
    caplog,
) -> None:
    _register(client, email="login-failure@example.com")
    caplog.clear()

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "login-failure@example.com",
                "password": "wrongpassword",
            },
            headers={REQUEST_ID_HEADER: "login-failure-request-id"},
        )

    assert response.status_code == 401
    records = _records_for_event(caplog, "login_failed")
    assert records
    record = records[-1]
    assert record.request_id == "login-failure-request-id"
    assert record.user_id is None
    assert record.reason == "invalid_credentials"
    assert not hasattr(record, "password")
    assert not hasattr(record, "username")


def test_admin_internal_endpoint_logs_business_event(
    client: TestClient,
    caplog,
) -> None:
    admin_token = _login_admin(client)
    request_id = "admin-internal-request-id"
    caplog.clear()

    with caplog.at_level(logging.INFO):
        response = client.get(
            "/api/v1/admin/users",
            headers=_headers(admin_token, request_id),
        )

    assert response.status_code == 200, response.text
    records = _records_for_event(caplog, "admin_internal_endpoint_used")
    assert records
    record = records[-1]
    assert record.method == "GET"
    assert record.path == "/api/v1/admin/users"
    assert record.request_id == request_id
    assert isinstance(record.user_id, int)
