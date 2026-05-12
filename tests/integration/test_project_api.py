from __future__ import annotations

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "user@example.com") -> str:
    response = client.post(
        "/api/v1/auth/register", json={"email": email, "password": "strongpass123"}
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_hourly_project_creation_and_derived_fields(client: TestClient) -> None:
    token = _register(client)
    response = client.post(
        "/api/v1/projects",
        json={
            "title": "Client API Support",
            "client_name": "Acme",
            "contract_type": "hourly",
            "billing_currency": "usd",
            "hourly_rate_cents": 2800,
            "expected_hours_per_week": 5,
            "payment_cadence": "biweekly",
            "status": "active",
        },
        headers=_headers(token),
    )
    assert response.status_code == 201, response.text
    project = response.json()
    assert project["contract_type"] == "hourly"
    assert project["billing_currency"] == "USD"
    assert project["expected_weekly_income_cents"] == 14000
    assert project["expected_monthly_income_cents"] is not None


def test_contract_validation_rules(client: TestClient) -> None:
    token = _register(client)
    headers = _headers(token)

    missing_hourly_rate = client.post(
        "/api/v1/projects",
        json={
            "title": "Invalid hourly",
            "client_name": "Acme",
            "contract_type": "hourly",
            "payment_cadence": "weekly",
        },
        headers=headers,
    )
    assert missing_hourly_rate.status_code == 422

    valid_non_billable = client.post(
        "/api/v1/projects",
        json={
            "title": "Internal RnD",
            "client_name": "Internal",
            "contract_type": "non_billable",
            "payment_cadence": "none",
        },
        headers=headers,
    )
    assert valid_non_billable.status_code == 201, valid_non_billable.text

    invalid_non_billable_cadence = client.post(
        "/api/v1/projects",
        json={
            "title": "Invalid non billable",
            "client_name": "Internal",
            "contract_type": "non_billable",
            "payment_cadence": "monthly",
        },
        headers=headers,
    )
    assert invalid_non_billable_cadence.status_code == 422


def test_project_filters_and_dashboard_summary(client: TestClient) -> None:
    token = _register(client)
    headers = _headers(token)
    client.post(
        "/api/v1/projects",
        json={
            "title": "Hourly Support",
            "client_name": "Acme",
            "status": "active",
            "priority": "high",
            "contract_type": "hourly",
            "hourly_rate_cents": 2800,
            "expected_hours_per_week": 5,
            "payment_cadence": "weekly",
        },
        headers=headers,
    )
    client.post(
        "/api/v1/projects",
        json={
            "title": "Retainer",
            "client_name": "Beta",
            "status": "active",
            "contract_type": "monthly_retainer",
            "monthly_rate_cents": 300000,
            "payment_cadence": "monthly",
        },
        headers=headers,
    )
    client.post(
        "/api/v1/projects",
        json={
            "title": "Non Billable",
            "client_name": "Internal",
            "status": "active",
            "contract_type": "non_billable",
            "payment_cadence": "none",
        },
        headers=headers,
    )
    summary_response = client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()
    assert summary["active_billable_projects"] == 2
    assert summary["monthly_contract_revenue_estimate"] > 0
