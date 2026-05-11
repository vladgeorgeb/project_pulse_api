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
            "budget_cents": 250_000,
            "hourly_rate_cents": 9_000,
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
        },
        headers=headers,
    )
    assert project_response.status_code == 201, project_response.text

    update_project_response = client.put(
        f"/api/v1/admin/projects/{project_response.json()['id']}",
        json={"status": "active", "priority": "urgent", "budget_cents": 900_000},
        headers=headers,
    )
    assert update_project_response.status_code == 200, update_project_response.text
    assert update_project_response.json()["status"] == "active"
    assert update_project_response.json()["priority"] == "urgent"
    assert update_project_response.json()["budget_cents"] == 900_000


def test_non_admin_gets_403_on_admin_routes(client: TestClient) -> None:
    user_token = _register_user(client, "user@example.com")

    response = client.get("/api/v1/admin/users", headers=_headers(user_token))

    assert response.status_code == 403
