from __future__ import annotations

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "user@example.com") -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "strongpass123"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_project(
    client: TestClient,
    token: str,
    title: str,
    **overrides: object,
) -> dict:
    payload = {"title": title, "client_name": title, **overrides}
    response = client.post("/api/v1/projects", json=payload, headers=_headers(token))
    assert response.status_code == 201, response.text
    return response.json()


def test_user_can_create_project_and_tasks(client: TestClient) -> None:
    token = _register(client)

    project_response = client.post(
        "/api/v1/projects",
        json={
            "title": "Client Reporting Dashboard",
            "client_name": "Acme Analytics",
            "description": "Build reporting API foundation.",
            "status": "active",
            "priority": "high",
            "budget_cents": 500_000,
            "hourly_rate_cents": 12_000,
            "contract_type": "fixed_price",
            "billing_status": "unpaid",
            "billing_currency": "usd",
            "agreed_amount": 5000,
            "billing_notes": "Bill after acceptance.",
            "deadline": "2026-06-30",
        },
        headers=_headers(token),
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    assert project["title"] == "Client Reporting Dashboard"
    assert project["contract_type"] == "fixed_price"
    assert project["billing_cycle"] == "monthly"
    assert project["billing_status"] == "unpaid"
    assert project["billing_currency"] == "USD"
    assert project["currency"] == "USD"
    assert project["agreed_amount"] == "5000.00"
    assert project["tasks"] == []
    assert project["progress_percent"] == 0

    task_response = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={
            "title": "Design data model",
            "status": "todo",
            "priority": "high",
            "estimated_minutes": 180,
            "due_date": "2026-05-20",
        },
        headers=_headers(token),
    )
    assert task_response.status_code == 201, task_response.text
    task = task_response.json()
    assert task["title"] == "Design data model"
    assert task["project_id"] == project["id"]

    complete_response = client.post(
        f"/api/v1/tasks/{task['id']}/complete",
        json={"actual_minutes": 150},
        headers=_headers(token),
    )
    assert complete_response.status_code == 200, complete_response.text
    assert complete_response.json()["status"] == "done"
    assert complete_response.json()["actual_minutes"] == 150

    refreshed_response = client.get(
        f"/api/v1/projects/{project['id']}",
        headers=_headers(token),
    )
    assert refreshed_response.status_code == 200, refreshed_response.text
    refreshed = refreshed_response.json()
    assert refreshed["progress_percent"] == 100
    assert refreshed["estimated_hours"] == 3.0
    assert refreshed["actual_hours"] == 2.5


def test_project_filters_and_dashboard_summary(client: TestClient) -> None:
    token = _register(client)
    headers = _headers(token)

    first = client.post(
        "/api/v1/projects",
        json={
            "title": "Internal API Cleanup",
            "client_name": "Internal",
            "status": "active",
            "priority": "urgent",
            "budget_cents": 300_000,
            "hourly_rate_cents": 10_000,
            "contract_type": "monthly_retainer",
            "billing_status": "unpaid",
            "monthly_rate": 3000,
            "deadline": "2026-05-01",
        },
        headers=headers,
    )
    assert first.status_code == 201, first.text
    second = client.post(
        "/api/v1/projects",
        json={
            "title": "Marketing Website",
            "client_name": "Acme",
            "status": "planned",
            "priority": "low",
            "budget_cents": 150_000,
            "hourly_rate_cents": 8_000,
            "billing_status": "paid",
            "deadline": "2026-08-10",
        },
        headers=headers,
    )
    assert second.status_code == 201, second.text
    paid_monthly = client.post(
        "/api/v1/projects",
        json={
            "title": "Platform Support",
            "client_name": "Beta",
            "status": "active",
            "priority": "medium",
            "contract_type": "full_time_monthly",
            "monthly_rate": 2000,
        },
        headers=headers,
    )
    assert paid_monthly.status_code == 201, paid_monthly.text
    overdue_monthly = client.post(
        "/api/v1/projects",
        json={
            "title": "Maintenance Retainer",
            "client_name": "Gamma",
            "status": "active",
            "priority": "medium",
            "contract_type": "monthly_retainer",
            "monthly_rate": 1500,
        },
        headers=headers,
    )
    assert overdue_monthly.status_code == 201, overdue_monthly.text

    task_response = client.post(
        f"/api/v1/projects/{first.json()['id']}/tasks",
        json={
            "title": "Refactor routers",
            "estimated_minutes": 240,
            "actual_minutes": 120,
            "due_date": "2026-04-01",
        },
        headers=headers,
    )
    assert task_response.status_code == 201, task_response.text

    filter_response = client.get(
        "/api/v1/projects",
        params={
            "status": "active",
            "priority": "urgent",
            "client_name": "internal",
            "min_budget_cents": 200_000,
            "max_budget_cents": 400_000,
        },
        headers=headers,
    )
    assert filter_response.status_code == 200, filter_response.text
    projects = filter_response.json()["items"]
    assert len(projects) == 1
    assert projects[0]["title"] == "Internal API Cleanup"

    dashboard_response = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dashboard_response.status_code == 200, dashboard_response.text
    summary = dashboard_response.json()
    assert summary["total_projects"] == 4
    assert summary["active_projects"] == 4
    assert summary["open_tasks"] == 1
    assert summary["estimated_hours"] == 4.0
    assert summary["actual_hours"] == 2.0
    assert summary["billable_value_cents"] == 20_000
    assert summary["active_billable_projects"] == 4
    assert summary["unpaid_projects"] == 0
    assert summary["overdue_payments"] == 0
    assert summary["paid_projects"] == 0
    assert summary["monthly_contract_revenue_estimate"] == 0.0
    assert summary["total_monthly_recurring_amount"] == 0.0
    assert summary["paid_this_month_amount"] == 0.0
    assert summary["pending_payment_amount"] == 0.0
    assert summary["overdue_payment_amount"] == 0.0
    assert summary["active_monthly_contracts"] == 0


def test_cannot_complete_project_with_open_tasks(client: TestClient) -> None:
    token = _register(client)
    headers = _headers(token)

    project = client.post(
        "/api/v1/projects",
        json={"title": "Workflow Demo", "client_name": "Internal"},
        headers=headers,
    ).json()
    task_response = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Open task"},
        headers=headers,
    )
    assert task_response.status_code == 201, task_response.text

    response = client.post(
        f"/api/v1/projects/{project['id']}/complete",
        headers=headers,
    )

    assert response.status_code == 409


def test_project_billing_defaults_and_validation(client: TestClient) -> None:
    token = _register(client)
    headers = _headers(token)

    internal_response = client.post(
        "/api/v1/projects",
        json={
            "title": "Internal Research",
            "client_name": "Internal",
            "contract_type": "internal",
            "billing_status": "unpaid",
        },
        headers=headers,
    )
    assert internal_response.status_code == 201, internal_response.text
    internal_project = internal_response.json()
    assert internal_project["contract_type"] == "internal"
    assert internal_project["billing_status"] == "not_billable"
    assert internal_project["billing_currency"] == "USD"

    monthly_response = client.post(
        "/api/v1/projects",
        json={
            "title": "Monthly Ops",
            "client_name": "Acme",
            "contract_type": "monthly_retainer",
            "monthly_rate": 2500,
            "currency": "eur",
        },
        headers=headers,
    )
    assert monthly_response.status_code == 201, monthly_response.text
    monthly_project = monthly_response.json()
    assert monthly_project["billing_cycle"] == "monthly"
    assert monthly_project["monthly_rate"] == "2500.00"
    assert monthly_project["currency"] == "EUR"
    assert monthly_project["billing_currency"] == "EUR"

    update_with_legacy_monthly_rate = client.put(
        f"/api/v1/projects/{internal_project['id']}",
        json={
            "contract_type": "monthly_retainer",
            "monthly_rate": 1800,
            "billing_status": "partially_paid",
        },
        headers=headers,
    )
    assert update_with_legacy_monthly_rate.status_code == 200
    updated_project = update_with_legacy_monthly_rate.json()
    assert updated_project["monthly_rate"] == "1800.00"
    assert updated_project["billing_status"] == "partially_paid"

    invalid_amount = client.post(
        "/api/v1/projects",
        json={
            "title": "Invalid amount",
            "client_name": "Acme",
            "agreed_amount": -1,
        },
        headers=headers,
    )
    assert invalid_amount.status_code == 422


def test_user_cannot_access_another_users_project(client: TestClient) -> None:
    first_token = _register(client, "first@example.com")
    second_token = _register(client, "second@example.com")

    project_response = client.post(
        "/api/v1/projects",
        json={"title": "Private project", "client_name": "Private"},
        headers=_headers(first_token),
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    response = client.get(
        f"/api/v1/projects/{project_id}",
        headers=_headers(second_token),
    )

    assert response.status_code == 404


def test_project_list_default_pagination(client: TestClient) -> None:
    token = _register(client)

    for index in range(25):
        _create_project(client, token, f"Project {index:02d}")

    response = client.get("/api/v1/projects", headers=_headers(token))

    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload["items"]) == 20
    assert payload["total"] == 25
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert payload["total_pages"] == 2


def test_project_list_defaults_to_priority_then_deadline(client: TestClient) -> None:
    token = _register(client)
    _create_project(
        client,
        token,
        "Invoice Workflow Automation",
        priority="medium",
        deadline="2026-05-23",
    )
    _create_project(
        client,
        token,
        "Monthly Backend Retainer",
        priority="high",
        deadline="2026-06-08",
    )
    _create_project(
        client,
        token,
        "Client CRM Integration",
        priority="medium",
        deadline="2026-07-01",
    )

    response = client.get("/api/v1/projects", headers=_headers(token))

    assert response.status_code == 200, response.text
    assert [project["title"] for project in response.json()["items"]] == [
        "Monthly Backend Retainer",
        "Invoice Workflow Automation",
        "Client CRM Integration",
    ]


def test_project_list_custom_page_and_page_size(client: TestClient) -> None:
    token = _register(client)

    for index in range(7):
        _create_project(client, token, f"Project {index:02d}", deadline="2026-06-01")

    response = client.get(
        "/api/v1/projects",
        params={"page": 2, "page_size": 3, "sort_by": "title", "sort_dir": "asc"},
        headers=_headers(token),
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert [project["title"] for project in payload["items"]] == [
        "Project 03",
        "Project 04",
        "Project 05",
    ]
    assert payload["total"] == 7
    assert payload["page"] == 2
    assert payload["page_size"] == 3
    assert payload["total_pages"] == 3


def test_project_list_sorting_asc_and_desc(client: TestClient) -> None:
    token = _register(client)
    _create_project(client, token, "Bravo", budget_cents=200)
    _create_project(client, token, "Alpha", budget_cents=100)
    _create_project(client, token, "Charlie", budget_cents=300)

    asc_response = client.get(
        "/api/v1/projects",
        params={"sort_by": "title", "sort_dir": "asc"},
        headers=_headers(token),
    )
    desc_response = client.get(
        "/api/v1/projects",
        params={"sort_by": "title", "sort_dir": "desc"},
        headers=_headers(token),
    )

    assert asc_response.status_code == 200, asc_response.text
    assert desc_response.status_code == 200, desc_response.text
    assert [project["title"] for project in asc_response.json()["items"]] == [
        "Alpha",
        "Bravo",
        "Charlie",
    ]
    assert [project["title"] for project in desc_response.json()["items"]] == [
        "Charlie",
        "Bravo",
        "Alpha",
    ]


def test_project_list_rejects_invalid_sort_by(client: TestClient) -> None:
    token = _register(client)
    _create_project(client, token, "Private project")

    response = client.get(
        "/api/v1/projects",
        params={"sort_by": "workspace_id;drop table projects"},
        headers=_headers(token),
    )

    assert response.status_code == 422


def test_project_list_pagination_preserves_user_isolation(client: TestClient) -> None:
    first_token = _register(client, "first-list@example.com")
    second_token = _register(client, "second-list@example.com")
    _create_project(client, first_token, "First private project")
    _create_project(client, second_token, "Second private project")

    response = client.get(
        "/api/v1/projects",
        params={"page": 1, "page_size": 100},
        headers=_headers(first_token),
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["total"] == 1
    assert [project["title"] for project in payload["items"]] == [
        "First private project"
    ]
