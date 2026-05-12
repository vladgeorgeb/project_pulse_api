from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "payments@example.com") -> str:
    response = client.post(
        "/api/v1/auth/register", json={"email": email, "password": "strongpass123"}
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_project(client: TestClient, token: str):
    response = client.post(
        "/api/v1/projects",
        json={
            "title": "Billing Project",
            "client_name": "Acme",
            "status": "active",
            "contract_type": "hourly",
            "hourly_rate_cents": 2800,
            "expected_hours_per_week": 5,
            "payment_cadence": "weekly",
        },
        headers=_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_payment_records_crud_and_validation(client: TestClient) -> None:
    token = _register(client)
    headers = _headers(token)
    project = _create_project(client, token)
    today = date.today()

    missing_due_date = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={"amount_cents": 50000, "currency": "USD", "status": "pending"},
        headers=headers,
    )
    assert missing_due_date.status_code == 422

    paid = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={
            "amount_cents": 70000,
            "currency": "USD",
            "status": "paid",
            "method": "wire",
            "paid_at": datetime.combine(today, datetime.min.time()).isoformat(),
            "period_start": (today - timedelta(days=6)).isoformat(),
            "period_end": today.isoformat(),
        },
        headers=headers,
    )
    assert paid.status_code == 201, paid.text
    assert paid.json()["amount_cents"] == 70000

    pending = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={
            "amount_cents": 35000,
            "currency": "USD",
            "status": "pending",
            "due_date": (today + timedelta(days=5)).isoformat(),
        },
        headers=headers,
    )
    assert pending.status_code == 201, pending.text

    dashboard = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dashboard.status_code == 200, dashboard.text
    summary = dashboard.json()
    assert summary["total_paid_amount"] == 700.0
    assert summary["pending_payment_amount"] == 350.0
    assert summary["next_payment_due_date"] == (today + timedelta(days=5)).isoformat()
