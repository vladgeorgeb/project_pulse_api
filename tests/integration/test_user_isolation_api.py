from __future__ import annotations

from fastapi.testclient import TestClient

from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "strongpass123"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_project(client: TestClient, token: str, title: str) -> dict:
    response = client.post(
        "/api/v1/projects",
        json={
            "title": title,
            "client_name": title,
            "contract_type": "fixed_price",
            "fixed_price_cents": 100000,
            "payment_cadence": "milestone",
        },
        headers=_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_user_owned_projects_tasks_and_dashboard_are_isolated(
    client: TestClient,
) -> None:
    first_token = _register(client, "first@example.com")
    second_token = _register(client, "second@example.com")
    first_headers = _headers(first_token)
    second_headers = _headers(second_token)

    first_project = _create_project(client, first_token, "First private project")
    second_project = _create_project(client, second_token, "Second private project")

    second_task_response = client.post(
        f"/api/v1/projects/{second_project['id']}/tasks",
        json={"title": "Second private task", "estimated_minutes": 90},
        headers=second_headers,
    )
    assert second_task_response.status_code == 201, second_task_response.text
    second_task = second_task_response.json()

    first_list = client.get("/api/v1/projects", headers=first_headers)
    assert first_list.status_code == 200, first_list.text
    first_titles = {project["title"] for project in first_list.json()["items"]}
    assert first_titles == {"First private project"}

    assert (
        client.get(
            f"/api/v1/projects/{second_project['id']}",
            headers=first_headers,
        ).status_code
        == 404
    )
    assert (
        client.put(
            f"/api/v1/projects/{second_project['id']}",
            json={"title": "Cross-user update"},
            headers=first_headers,
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/v1/projects/{second_project['id']}",
            headers=first_headers,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/projects/{second_project['id']}/tasks",
            json={"title": "Cross-user task"},
            headers=first_headers,
        ).status_code
        == 404
    )
    assert (
        client.put(
            f"/api/v1/tasks/{second_task['id']}",
            json={"title": "Cross-user task update"},
            headers=first_headers,
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/v1/tasks/{second_task['id']}",
            headers=first_headers,
        ).status_code
        == 404
    )

    first_summary = client.get("/api/v1/dashboard/summary", headers=first_headers)
    second_summary = client.get("/api/v1/dashboard/summary", headers=second_headers)
    assert first_summary.status_code == 200, first_summary.text
    assert second_summary.status_code == 200, second_summary.text
    assert first_summary.json()["total_projects"] == 1
    assert first_summary.json()["open_tasks"] == 0
    assert second_summary.json()["total_projects"] == 1
    assert second_summary.json()["open_tasks"] == 1

    second_detail = client.get(
        f"/api/v1/projects/{second_project['id']}",
        headers=second_headers,
    )
    assert second_detail.status_code == 200, second_detail.text
    assert second_detail.json()["title"] == "Second private project"
    assert first_project["id"] != second_project["id"]


def test_user_owned_endpoints_do_not_use_unscoped_id_repository_methods(
    client: TestClient,
    monkeypatch,
) -> None:
    def fail_project_get_by_id(*_: object, **__: object) -> None:
        raise AssertionError("User-owned project endpoints must use scoped lookups.")

    def fail_task_get_by_id(*_: object, **__: object) -> None:
        raise AssertionError("User-owned task endpoints must use scoped lookups.")

    monkeypatch.setattr(ProjectRepository, "get_by_id", fail_project_get_by_id)
    monkeypatch.setattr(TaskRepository, "get_by_id", fail_task_get_by_id)

    token = _register(client, "scoped@example.com")
    headers = _headers(token)

    project_response = client.post(
        "/api/v1/projects",
        json={
            "title": "Scoped project",
            "client_name": "Scoped client",
            "contract_type": "fixed_price",
            "fixed_price_cents": 100000,
            "payment_cadence": "milestone",
        },
        headers=headers,
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()

    task_response = client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Scoped task"},
        headers=headers,
    )
    assert task_response.status_code == 201, task_response.text
    task = task_response.json()

    assert (
        client.get(f"/api/v1/projects/{project['id']}", headers=headers).status_code
        == 200
    )
    assert (
        client.put(
            f"/api/v1/projects/{project['id']}",
            json={"title": "Scoped project updated"},
            headers=headers,
        ).status_code
        == 200
    )
    assert (
        client.put(
            f"/api/v1/tasks/{task['id']}",
            json={"title": "Scoped task updated"},
            headers=headers,
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/tasks/{task['id']}/complete",
            json={"actual_minutes": 30},
            headers=headers,
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/projects/{project['id']}/complete",
            headers=headers,
        ).status_code
        == 200
    )
    assert (
        client.delete(f"/api/v1/tasks/{task['id']}", headers=headers).status_code == 204
    )
    assert (
        client.delete(f"/api/v1/projects/{project['id']}", headers=headers).status_code
        == 204
    )
