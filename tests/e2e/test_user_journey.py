from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_full_hourly_project_and_payment_journey(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "journey@example.com", "password": "strongpass123"},
    )
    assert register_response.status_code == 201, register_response.text
    token = register_response.json()["access_token"]
    headers = _headers(token)

    project_response = client.post(
        "/api/v1/projects",
        json={
            "title": "Freelance API Support",
            "client_name": "Acme",
            "status": "active",
            "priority": "high",
            "contract_type": "hourly",
            "billing_currency": "USD",
            "hourly_rate_cents": 2800,
            "expected_hours_per_week": 5,
            "start_date": date.today().isoformat(),
            "estimated_end_date": (date.today() + timedelta(days=90)).isoformat(),
            "payment_cadence": "biweekly",
        },
        headers=headers,
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()

    payment_response = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={
            "amount_cents": 56000,
            "currency": "USD",
            "status": "paid",
            "method": "wire",
            "paid_at": date.today().isoformat() + "T12:00:00",
            "period_start": (date.today() - timedelta(days=13)).isoformat(),
            "period_end": date.today().isoformat(),
        },
        headers=headers,
    )
    assert payment_response.status_code == 201, payment_response.text

    dashboard_response = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dashboard_response.status_code == 200, dashboard_response.text
    dashboard = dashboard_response.json()
    assert dashboard["total_paid_amount"] == 560.0
    assert dashboard["monthly_contract_revenue_estimate"] > 0
