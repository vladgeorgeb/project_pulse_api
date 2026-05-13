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


def test_create_paid_payment_without_paid_at_autofills_timestamp(
    client: TestClient,
) -> None:
    token = _register(client, "payments-autofill-create@example.com")
    headers = _headers(token)
    project = _create_project(client, token)

    paid = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={
            "amount_cents": 70000,
            "currency": "USD",
            "status": "paid",
            "method": "wire",
        },
        headers=headers,
    )
    assert paid.status_code == 201, paid.text
    payload = paid.json()
    assert payload["status"] == "paid"
    assert payload["paid_at"] is not None
    assert datetime.fromisoformat(payload["paid_at"])


def test_create_paid_payment_with_explicit_paid_at_is_preserved(
    client: TestClient,
) -> None:
    token = _register(client, "payments-explicit-create@example.com")
    headers = _headers(token)
    project = _create_project(client, token)
    explicit_paid_at = datetime(2026, 1, 15, 10, 30, 0).isoformat()

    paid = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={
            "amount_cents": 81000,
            "currency": "USD",
            "status": "paid",
            "method": "wire",
            "paid_at": explicit_paid_at,
        },
        headers=headers,
    )
    assert paid.status_code == 201, paid.text
    assert paid.json()["paid_at"] == explicit_paid_at


def test_update_pending_payment_to_paid_without_paid_at_autofills_timestamp(
    client: TestClient,
) -> None:
    token = _register(client, "payments-autofill-update@example.com")
    headers = _headers(token)
    project = _create_project(client, token)
    today = date.today()

    pending = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={
            "amount_cents": 62000,
            "currency": "USD",
            "status": "pending",
            "due_date": (today + timedelta(days=7)).isoformat(),
        },
        headers=headers,
    )
    assert pending.status_code == 201, pending.text
    payment_id = pending.json()["id"]
    assert pending.json()["paid_at"] is None

    paid_update = client.put(
        f"/api/v1/projects/{project['id']}/payments/{payment_id}",
        json={"status": "paid"},
        headers=headers,
    )
    assert paid_update.status_code == 200, paid_update.text
    payload = paid_update.json()
    assert payload["status"] == "paid"
    assert payload["paid_at"] is not None
    assert datetime.fromisoformat(payload["paid_at"])


def test_update_paid_payment_with_explicit_paid_at_is_preserved(
    client: TestClient,
) -> None:
    token = _register(client, "payments-explicit-update@example.com")
    headers = _headers(token)
    project = _create_project(client, token)
    today = date.today()

    pending = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={
            "amount_cents": 54000,
            "currency": "USD",
            "status": "pending",
            "due_date": (today + timedelta(days=3)).isoformat(),
        },
        headers=headers,
    )
    assert pending.status_code == 201, pending.text
    payment_id = pending.json()["id"]

    first_paid_at = datetime(2026, 2, 2, 9, 0, 0).isoformat()
    to_paid = client.put(
        f"/api/v1/projects/{project['id']}/payments/{payment_id}",
        json={"status": "paid", "paid_at": first_paid_at},
        headers=headers,
    )
    assert to_paid.status_code == 200, to_paid.text
    assert to_paid.json()["status"] == "paid"
    assert to_paid.json()["paid_at"] == first_paid_at

    second_paid_at = datetime(2026, 2, 3, 11, 45, 0).isoformat()
    paid_update = client.put(
        f"/api/v1/projects/{project['id']}/payments/{payment_id}",
        json={"paid_at": second_paid_at},
        headers=headers,
    )
    assert paid_update.status_code == 200, paid_update.text
    assert paid_update.json()["status"] == "paid"
    assert paid_update.json()["paid_at"] == second_paid_at


def test_payment_record_read_endpoints_and_isolation(client: TestClient) -> None:
    owner_token = _register(client, "payments-owner@example.com")
    other_token = _register(client, "payments-other@example.com")
    owner_headers = _headers(owner_token)
    other_headers = _headers(other_token)
    project = _create_project(client, owner_token)

    created_payment = client.post(
        f"/api/v1/projects/{project['id']}/payments",
        json={
            "amount_cents": 42000,
            "currency": "USD",
            "status": "pending",
            "due_date": (date.today() + timedelta(days=3)).isoformat(),
        },
        headers=owner_headers,
    )
    assert created_payment.status_code == 201, created_payment.text
    payment_record = created_payment.json()

    list_response = client.get(
        f"/api/v1/projects/{project['id']}/payments",
        headers=owner_headers,
    )
    assert list_response.status_code == 200, list_response.text
    payments = list_response.json()
    assert len(payments) == 1
    assert payments[0]["id"] == payment_record["id"]

    detail_response = client.get(
        f"/api/v1/projects/{project['id']}/payments/{payment_record['id']}",
        headers=owner_headers,
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["id"] == payment_record["id"]
    assert detail_response.json()["amount_cents"] == 42000

    assert (
        client.get(
            f"/api/v1/projects/{project['id']}/payments",
            headers=other_headers,
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/projects/{project['id']}/payments/{payment_record['id']}",
            headers=other_headers,
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/projects/{project['id']}/payments/999999",
            headers=owner_headers,
        ).status_code
        == 404
    )
