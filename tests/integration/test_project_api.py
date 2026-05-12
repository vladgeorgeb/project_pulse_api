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


def test_project_archive_transition_and_include_archived_filtering(
    client: TestClient,
) -> None:
    token = _register(client, "archive-flow@example.com")
    headers = _headers(token)

    create_response = client.post(
        "/api/v1/projects",
        json={
            "title": "Archive Candidate",
            "client_name": "Acme",
            "status": "active",
            "contract_type": "fixed_price",
            "fixed_price_cents": 125000,
            "payment_cadence": "milestone",
        },
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    created_project = create_response.json()
    assert "archived" not in created_project
    project_id = created_project["id"]

    archive_response = client.put(
        f"/api/v1/projects/{project_id}",
        json={"status": "archived"},
        headers=headers,
    )
    assert archive_response.status_code == 200, archive_response.text
    archived_project = archive_response.json()
    assert archived_project["status"] == "archived"
    assert "archived" not in archived_project

    default_list = client.get("/api/v1/projects", headers=headers)
    assert default_list.status_code == 200, default_list.text
    assert default_list.json()["items"] == []

    include_archived_list = client.get(
        "/api/v1/projects?include_archived=true",
        headers=headers,
    )
    assert include_archived_list.status_code == 200, include_archived_list.text
    archived_items = include_archived_list.json()["items"]
    assert len(archived_items) == 1
    assert archived_items[0]["id"] == project_id
    assert archived_items[0]["status"] == "archived"
    assert "archived" not in archived_items[0]

    unarchive_response = client.put(
        f"/api/v1/projects/{project_id}",
        json={"status": "active"},
        headers=headers,
    )
    assert unarchive_response.status_code == 200, unarchive_response.text
    assert unarchive_response.json()["status"] == "active"

    active_list = client.get("/api/v1/projects", headers=headers)
    assert active_list.status_code == 200, active_list.text
    active_items = active_list.json()["items"]
    assert len(active_items) == 1
    assert active_items[0]["id"] == project_id


def test_dashboard_summary_counts_archived_projects_by_status(
    client: TestClient,
) -> None:
    token = _register(client, "archive-summary@example.com")
    headers = _headers(token)

    active_response = client.post(
        "/api/v1/projects",
        json={
            "title": "Active Project",
            "client_name": "Acme",
            "status": "active",
            "contract_type": "fixed_price",
            "fixed_price_cents": 100000,
            "payment_cadence": "milestone",
        },
        headers=headers,
    )
    assert active_response.status_code == 201, active_response.text

    archived_response = client.post(
        "/api/v1/projects",
        json={
            "title": "Archived Project",
            "client_name": "Beta",
            "status": "archived",
            "contract_type": "fixed_price",
            "fixed_price_cents": 100000,
            "payment_cadence": "milestone",
        },
        headers=headers,
    )
    assert archived_response.status_code == 201, archived_response.text

    summary_response = client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()
    assert summary["total_projects"] == 2
    assert summary["archived_projects"] == 1
    assert summary["active_projects"] == 1
