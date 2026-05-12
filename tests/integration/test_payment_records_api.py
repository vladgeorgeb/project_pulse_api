from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str = "payments@example.com") -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "strongpass123"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_project(client: TestClient, token: str, title: str, **overrides: object):
    response = client.post(
        "/api/v1/projects",
        json={"title": title, "client_name": title, **overrides},
        headers=_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_project_payment_records_crud_and_project_sync(client: TestClient) -> None:
    token = _register(client)
    headers = _headers(token)
    today = date.today()
    future_due_date = (today + timedelta(days=7)).isoformat()
    overdue_due_date = (today - timedelta(days=1)).isoformat()
    paid_at = datetime.combine(today, datetime.min.time()).replace(hour=10, minute=30)
    project = _create_project(
        client,
        token,
        "Retainer with history",
        status="active",
        contract_type="monthly_retainer",
        currency="eur",
    )

    create_response = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={
            "amount": 1200,
            "currency": "eur",
            "status": "pending",
            "method": "Bank transfer",
            "due_date": future_due_date,
            "period_start": today.isoformat(),
            "period_end": (today + timedelta(days=30)).isoformat(),
            "notes": "May retainer.",
        },
        headers=headers,
    )
    assert create_response.status_code == 201, create_response.text
    payment = create_response.json()
    assert payment["amount"] == "1200.00"
    assert payment["currency"] == "EUR"
    assert payment["invoice_id"] is None

    project_response = client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    assert project_response.status_code == 200, project_response.text
    synced_project = project_response.json()
    assert [item["id"] for item in synced_project["payment_records"]] == [payment["id"]]
    assert synced_project["payment_records"][0]["is_overdue"] is False

    update_response = client.put(
        f"/api/v1/projects/{project['id']}/payments/{payment['id']}",
        json={
            "status": "paid",
            "paid_at": paid_at.isoformat(),
            "method": "Wire",
            "invoice_id": 42,
        },
        headers=headers,
    )
    assert update_response.status_code == 200, update_response.text
    updated_payment = update_response.json()
    assert updated_payment["status"] == "paid"
    assert updated_payment["method"] == "Wire"
    assert updated_payment["invoice_id"] == 42

    paid_project_response = client.get(
        f"/api/v1/projects/{project['id']}",
        headers=headers,
    )
    assert paid_project_response.status_code == 200, paid_project_response.text
    paid_project = paid_project_response.json()
    assert paid_project["payment_records"][0]["status"] == "paid"

    overdue_response = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={
            "amount": 300,
            "currency": "EUR",
            "status": "pending",
            "due_date": overdue_due_date,
        },
        headers=headers,
    )
    assert overdue_response.status_code == 201, overdue_response.text
    overdue_payment = overdue_response.json()
    assert overdue_payment["status"] == "pending"
    assert overdue_payment["is_overdue"] is True

    overdue_project = client.get(
        f"/api/v1/projects/{project['id']}",
        headers=headers,
    ).json()
    overdue_records = [
        item
        for item in overdue_project["payment_records"]
        if item["id"] == overdue_payment["id"]
    ]
    assert overdue_records[0]["is_overdue"] is True

    list_response = client.get(
        f"/api/v1/projects/{project['id']}/payments",
        headers=headers,
    )
    assert list_response.status_code == 200, list_response.text
    assert [item["id"] for item in list_response.json()] == [
        overdue_payment["id"],
        payment["id"],
    ]

    delete_response = client.delete(
        f"/api/v1/projects/{project['id']}/payments/{overdue_payment['id']}",
        headers=headers,
    )
    assert delete_response.status_code == 204, delete_response.text

    final_project = client.get(
        f"/api/v1/projects/{project['id']}",
        headers=headers,
    ).json()
    assert [item["id"] for item in final_project["payment_records"]] == [payment["id"]]


def test_payment_record_rejects_invalid_status_and_currency(
    client: TestClient,
) -> None:
    token = _register(client)
    project = _create_project(client, token, "Validation payments")
    headers = _headers(token)

    overdue_status_response = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={"amount": 100, "currency": "USD", "status": "overdue"},
        headers=headers,
    )
    assert overdue_status_response.status_code == 422

    invalid_currency_response = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={"amount": 100, "currency": "XYZ", "status": "pending"},
        headers=headers,
    )
    assert invalid_currency_response.status_code == 422


def test_dashboard_payment_metrics_use_payment_history(client: TestClient) -> None:
    token = _register(client)
    headers = _headers(token)
    today = date.today()
    paid_at = datetime.combine(today, datetime.min.time()).replace(hour=9)
    future_due_date = (today + timedelta(days=7)).isoformat()
    overdue_due_date = (today - timedelta(days=1)).isoformat()
    project = _create_project(
        client,
        token,
        "History dashboard",
        status="active",
        contract_type="monthly_retainer",
    )

    for payload in (
        {
            "amount": 700,
            "currency": "USD",
            "status": "paid",
            "paid_at": paid_at.isoformat(),
        },
        {
            "amount": 500,
            "currency": "USD",
            "status": "pending",
            "due_date": future_due_date,
        },
        {
            "amount": 200,
            "currency": "USD",
            "status": "pending",
            "due_date": overdue_due_date,
        },
    ):
        response = client.post(
            f"/api/v1/projects/{project['id']}/payments",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 201, response.text

    dashboard_response = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dashboard_response.status_code == 200, dashboard_response.text
    summary = dashboard_response.json()
    assert summary["total_paid_amount"] == 700.0
    assert summary["paid_this_month_amount"] == 700.0
    assert summary["pending_payment_amount"] == 500.0
    assert summary["overdue_payment_amount"] == 200.0
    assert summary["overdue_payments"] == 1
    assert summary["next_payment_due_date"] == overdue_due_date
    assert summary["next_payment_due_amount"] == 200.0
    assert summary["next_payment_due_currency"] == "USD"
    assert summary["payment_summary_currency"] == "USD"
    assert summary["has_mixed_payment_currencies"] is False
    assert summary["total_monthly_recurring_amount"] == 0.0


def test_dashboard_ignores_project_payment_fields_without_payment_records(
    client: TestClient,
) -> None:
    token = _register(client)
    headers = _headers(token)
    project = _create_project(
        client,
        token,
        "Project fields only",
        status="active",
        contract_type="monthly_retainer",
        monthly_amount=1500,
        payment_status="pending",
        next_payment_due_date=(date.today() + timedelta(days=7)).isoformat(),
    )

    project_response = client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    assert project_response.status_code == 200, project_response.text
    project_payload = project_response.json()
    assert project_payload["payment_records"] == []

    dashboard_response = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dashboard_response.status_code == 200, dashboard_response.text
    summary = dashboard_response.json()
    assert summary["pending_payment_amount"] == 0.0
    assert summary["overdue_payment_amount"] == 0.0
    assert summary["next_payment_due_date"] is None
    assert summary["next_payment_due_amount"] is None


def test_dashboard_uses_payment_records_instead_of_project_amounts(
    client: TestClient,
) -> None:
    token = _register(client)
    headers = _headers(token)
    project = _create_project(
        client,
        token,
        "Record backed billing",
        status="active",
        contract_type="monthly_retainer",
        monthly_amount=2500,
        payment_status="pending",
    )
    response = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={"amount": 400, "currency": "USD", "status": "pending"},
        headers=headers,
    )
    assert response.status_code == 201, response.text

    dashboard_response = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dashboard_response.status_code == 200, dashboard_response.text
    summary = dashboard_response.json()
    assert summary["pending_payment_amount"] == 400.0
    assert summary["total_monthly_recurring_amount"] == 0.0


def test_users_cannot_access_other_users_payment_records(
    client: TestClient,
) -> None:
    first_token = _register(client, "first-payments@example.com")
    second_token = _register(client, "second-payments@example.com")
    first_project = _create_project(client, first_token, "First payments")
    second_project = _create_project(client, second_token, "Second payments")

    payment_response = client.post(
        f"/api/v1/projects/{first_project['id']}/payments",
        json={"amount": 250, "currency": "USD", "status": "pending"},
        headers=_headers(first_token),
    )
    assert payment_response.status_code == 201, payment_response.text
    payment_id = payment_response.json()["id"]

    list_response = client.get(
        f"/api/v1/projects/{first_project['id']}/payments",
        headers=_headers(second_token),
    )
    assert list_response.status_code == 404

    get_response = client.get(
        f"/api/v1/projects/{second_project['id']}/payments/{payment_id}",
        headers=_headers(second_token),
    )
    assert get_response.status_code == 404

    update_response = client.put(
        f"/api/v1/projects/{second_project['id']}/payments/{payment_id}",
        json={"status": "paid"},
        headers=_headers(second_token),
    )
    assert update_response.status_code == 404

    delete_response = client.delete(
        f"/api/v1/projects/{second_project['id']}/payments/{payment_id}",
        headers=_headers(second_token),
    )
    assert delete_response.status_code == 404
