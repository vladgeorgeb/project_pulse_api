from __future__ import annotations

from fastapi.testclient import TestClient


def _login_admin(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "adminpass123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _register_user(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "strongpass123"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_login_and_list_users(client: TestClient) -> None:
    _register_user(client, "user@example.com")
    admin_token = _login_admin(client)

    response = client.get("/api/v1/admin/users", headers=_headers(admin_token))

    assert response.status_code == 200, response.text
    users = response.json()
    assert all("password_hash" not in item for item in users)
    emails = {item["email"] for item in users}
    assert "admin@example.com" in emails
    assert "user@example.com" in emails


def test_admin_can_create_project_and_task(client: TestClient) -> None:
    _register_user(client, "owner@example.com")
    admin_token = _login_admin(client)
    headers = _headers(admin_token)

    workspaces_response = client.get("/api/v1/admin/workspaces", headers=headers)
    assert workspaces_response.status_code == 200, workspaces_response.text
    owner_workspace_id = next(
        item["id"]
        for item in workspaces_response.json()
        if item["company_name"] == "Independent Contractor"
    )

    project_response = client.post(
        "/api/v1/admin/projects",
        json={
            "workspace_id": owner_workspace_id,
            "title": "Admin Seeded Project",
            "client_name": "Admin Client",
            "status": "active",
            "priority": "medium",
            "contract_type": "hourly",
            "hourly_rate_cents": 9000,
            "payment_cadence": "weekly",
        },
        headers=headers,
    )
    assert project_response.status_code == 201, project_response.text
    project_id = project_response.json()["id"]

    task_response = client.post(
        "/api/v1/admin/tasks",
        json={
            "project_id": project_id,
            "title": "Admin task",
            "status": "todo",
            "priority": "high",
            "estimated_minutes": 60,
        },
        headers=headers,
    )
    assert task_response.status_code == 201, task_response.text
    assert task_response.json()["project_id"] == project_id


def test_admin_task_update_cannot_bypass_invalid_status_transition(
    client: TestClient,
) -> None:
    _register_user(client, "task-transition-parity@example.com")
    admin_token = _login_admin(client)
    headers = _headers(admin_token)

    workspace = client.get("/api/v1/admin/workspaces", headers=headers).json()[0]
    project_response = client.post(
        "/api/v1/admin/projects",
        json={
            "workspace_id": workspace["id"],
            "title": "Transition Project",
            "client_name": "Admin Client",
            "contract_type": "fixed_price",
            "fixed_price_cents": 100000,
            "payment_cadence": "milestone",
        },
        headers=headers,
    )
    assert project_response.status_code == 201, project_response.text

    task_response = client.post(
        "/api/v1/admin/tasks",
        json={
            "project_id": project_response.json()["id"],
            "title": "Closed task",
            "status": "done",
            "priority": "medium",
            "estimated_minutes": 60,
        },
        headers=headers,
    )
    assert task_response.status_code == 201, task_response.text
    task_id = task_response.json()["id"]

    invalid_update = client.put(
        f"/api/v1/admin/tasks/{task_id}",
        json={"status": "todo"},
        headers=headers,
    )

    assert invalid_update.status_code == 409
    assert invalid_update.json()["detail"] == "Cannot move task from 'done' to 'todo'."

    unchanged_task = client.get(f"/api/v1/admin/tasks/{task_id}", headers=headers)
    assert unchanged_task.status_code == 200, unchanged_task.text
    assert unchanged_task.json()["status"] == "done"


def test_admin_can_update_workspace_and_project(client: TestClient) -> None:
    _register_user(client, "owner@example.com")
    admin_token = _login_admin(client)
    headers = _headers(admin_token)

    workspace = client.get("/api/v1/admin/workspaces", headers=headers).json()[0]
    update_workspace_response = client.put(
        f"/api/v1/admin/workspaces/{workspace['id']}",
        json={"name": "Ops Workspace", "monthly_capacity_hours": 160},
        headers=headers,
    )
    assert update_workspace_response.status_code == 200, update_workspace_response.text
    assert update_workspace_response.json()["name"] == "Ops Workspace"
    assert update_workspace_response.json()["monthly_capacity_hours"] == 160

    project_response = client.post(
        "/api/v1/admin/projects",
        json={
            "workspace_id": workspace["id"],
            "title": "Needs Update",
            "client_name": "Admin",
            "contract_type": "fixed_price",
            "fixed_price_cents": 150000,
            "payment_cadence": "milestone",
        },
        headers=headers,
    )
    assert project_response.status_code == 201, project_response.text

    update_project_response = client.put(
        f"/api/v1/admin/projects/{project_response.json()['id']}",
        json={"status": "active", "priority": "urgent", "hourly_rate_cents": 10000},
        headers=headers,
    )
    assert update_project_response.status_code == 200, update_project_response.text
    assert update_project_response.json()["status"] == "active"
    assert update_project_response.json()["priority"] == "urgent"
    assert update_project_response.json()["hourly_rate_cents"] == 10000


def test_non_admin_gets_403_on_admin_routes(client: TestClient) -> None:
    user_token = _register_user(client, "user@example.com")

    response = client.get("/api/v1/admin/users", headers=_headers(user_token))

    assert response.status_code == 403


def test_admin_feedback_route_requires_admin_user(client: TestClient) -> None:
    user_token = _register_user(client, "feedback-non-admin@example.com")

    response = client.get("/api/v1/admin/feedback", headers=_headers(user_token))

    assert response.status_code == 403
    assert response.json()["detail"] == "Administrator privileges required."


def test_admin_user_create_conflict_and_missing_workspace_owner_errors(
    client: TestClient,
) -> None:
    _register_user(client, "admin-conflict@example.com")
    admin_token = _login_admin(client)
    headers = _headers(admin_token)

    duplicate_user = client.post(
        "/api/v1/admin/users",
        json={
            "email": "admin-conflict@example.com",
            "password": "strongpass123",
            "is_admin": False,
        },
        headers=headers,
    )
    assert duplicate_user.status_code == 409

    invalid_workspace = client.post(
        "/api/v1/admin/workspaces",
        json={
            "user_id": 999999,
            "name": "Missing owner",
            "company_name": "Nowhere",
            "monthly_capacity_hours": 120,
        },
        headers=headers,
    )
    assert invalid_workspace.status_code == 404
    assert invalid_workspace.json()["detail"] == "User not found."


def test_admin_project_contract_rate_validation_parity(client: TestClient) -> None:
    _register_user(client, "contract-parity@example.com")
    admin_token = _login_admin(client)
    headers = _headers(admin_token)

    workspace = client.get("/api/v1/admin/workspaces", headers=headers).json()[0]

    invalid_create = client.post(
        "/api/v1/admin/projects",
        json={
            "workspace_id": workspace["id"],
            "title": "Invalid hourly",
            "client_name": "Acme",
            "contract_type": "hourly",
            "payment_cadence": "weekly",
        },
        headers=headers,
    )
    assert invalid_create.status_code == 422

    valid_create = client.post(
        "/api/v1/admin/projects",
        json={
            "workspace_id": workspace["id"],
            "title": "Valid fixed",
            "client_name": "Acme",
            "contract_type": "fixed_price",
            "fixed_price_cents": 200000,
            "payment_cadence": "milestone",
        },
        headers=headers,
    )
    assert valid_create.status_code == 201, valid_create.text

    invalid_update = client.put(
        f"/api/v1/admin/projects/{valid_create.json()['id']}",
        json={"contract_type": "monthly_retainer"},
        headers=headers,
    )
    assert invalid_update.status_code == 422


def test_admin_project_non_billable_cadence_validation_parity(
    client: TestClient,
) -> None:
    _register_user(client, "cadence-parity@example.com")
    admin_token = _login_admin(client)
    headers = _headers(admin_token)

    workspace = client.get("/api/v1/admin/workspaces", headers=headers).json()[0]

    invalid_create = client.post(
        "/api/v1/admin/projects",
        json={
            "workspace_id": workspace["id"],
            "title": "Invalid non billable cadence",
            "client_name": "Internal",
            "contract_type": "non_billable",
            "payment_cadence": "monthly",
        },
        headers=headers,
    )
    assert invalid_create.status_code == 422

    valid_create = client.post(
        "/api/v1/admin/projects",
        json={
            "workspace_id": workspace["id"],
            "title": "Billable baseline",
            "client_name": "Acme",
            "contract_type": "fixed_price",
            "fixed_price_cents": 200000,
            "payment_cadence": "milestone",
        },
        headers=headers,
    )
    assert valid_create.status_code == 201, valid_create.text

    invalid_update = client.put(
        f"/api/v1/admin/projects/{valid_create.json()['id']}",
        json={"payment_cadence": "none"},
        headers=headers,
    )
    assert invalid_update.status_code == 422


def test_admin_project_date_range_validation_parity(client: TestClient) -> None:
    _register_user(client, "date-range-parity@example.com")
    admin_token = _login_admin(client)
    headers = _headers(admin_token)

    workspace = client.get("/api/v1/admin/workspaces", headers=headers).json()[0]

    invalid_create = client.post(
        "/api/v1/admin/projects",
        json={
            "workspace_id": workspace["id"],
            "title": "Invalid dates",
            "client_name": "Acme",
            "contract_type": "fixed_price",
            "fixed_price_cents": 200000,
            "payment_cadence": "milestone",
            "start_date": "2026-05-20",
            "estimated_end_date": "2026-05-10",
        },
        headers=headers,
    )
    assert invalid_create.status_code == 422

    valid_create = client.post(
        "/api/v1/admin/projects",
        json={
            "workspace_id": workspace["id"],
            "title": "Valid dates",
            "client_name": "Acme",
            "contract_type": "fixed_price",
            "fixed_price_cents": 200000,
            "payment_cadence": "milestone",
            "start_date": "2026-05-01",
            "estimated_end_date": "2026-05-15",
        },
        headers=headers,
    )
    assert valid_create.status_code == 201, valid_create.text

    invalid_update = client.put(
        f"/api/v1/admin/projects/{valid_create.json()['id']}",
        json={
            "start_date": "2026-05-30",
            "estimated_end_date": "2026-05-10",
        },
        headers=headers,
    )
    assert invalid_update.status_code == 422


def test_admin_cannot_complete_project_with_open_tasks(client: TestClient) -> None:
    _register_user(client, "completion-parity@example.com")
    admin_token = _login_admin(client)
    headers = _headers(admin_token)

    workspace = client.get("/api/v1/admin/workspaces", headers=headers).json()[0]
    create_project_response = client.post(
        "/api/v1/admin/projects",
        json={
            "workspace_id": workspace["id"],
            "title": "Open task project",
            "client_name": "Acme",
            "status": "active",
            "contract_type": "fixed_price",
            "fixed_price_cents": 100000,
            "payment_cadence": "milestone",
        },
        headers=headers,
    )
    assert create_project_response.status_code == 201, create_project_response.text
    project_id = create_project_response.json()["id"]

    create_task_response = client.post(
        "/api/v1/admin/tasks",
        json={
            "project_id": project_id,
            "title": "Still open",
            "status": "todo",
            "priority": "medium",
            "estimated_minutes": 30,
        },
        headers=headers,
    )
    assert create_task_response.status_code == 201, create_task_response.text

    complete_update_response = client.put(
        f"/api/v1/admin/projects/{project_id}",
        json={"status": "completed"},
        headers=headers,
    )
    assert complete_update_response.status_code == 409
