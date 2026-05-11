from __future__ import annotations

from fastapi.testclient import TestClient


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_full_project_management_journey(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "journey@example.com", "password": "strongpass123"},
    )
    assert register_response.status_code == 201, register_response.text
    token = register_response.json()["access_token"]
    headers = _headers(token)

    workspace_response = client.put(
        "/api/v1/workspaces/me",
        json={
            "name": "Portfolio Lab",
            "company_name": "George Dev Studio",
            "monthly_capacity_hours": 140,
        },
        headers=headers,
    )
    assert workspace_response.status_code == 200, workspace_response.text
    workspace = workspace_response.json()
    assert workspace["name"] == "Portfolio Lab"
    assert workspace["company_name"] == "George Dev Studio"

    project_response = client.post(
        "/api/v1/projects",
        json={
            "title": "React Dashboard Backend",
            "client_name": "Internal Portfolio",
            "status": "active",
            "priority": "high",
            "budget_cents": 1_000_000,
            "hourly_rate_cents": 10_000,
            "deadline": "2026-07-01",
        },
        headers=headers,
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()

    task_ids: list[int] = []
    for title, estimate in (
        ("Design SQLAlchemy models", 180),
        ("Implement dashboard summary endpoint", 240),
    ):
        task_response = client.post(
            f"/api/v1/projects/{project['id']}/tasks",
            json={
                "title": title,
                "priority": "high",
                "estimated_minutes": estimate,
            },
            headers=headers,
        )
        assert task_response.status_code == 201, task_response.text
        task_ids.append(task_response.json()["id"])

    first_completion = client.post(
        f"/api/v1/tasks/{task_ids[0]}/complete",
        json={"actual_minutes": 150},
        headers=headers,
    )
    assert first_completion.status_code == 200, first_completion.text

    blocked_completion = client.post(
        f"/api/v1/projects/{project['id']}/complete",
        headers=headers,
    )
    assert blocked_completion.status_code == 409

    second_completion = client.post(
        f"/api/v1/tasks/{task_ids[1]}/complete",
        json={"actual_minutes": 210},
        headers=headers,
    )
    assert second_completion.status_code == 200, second_completion.text

    complete_project = client.post(
        f"/api/v1/projects/{project['id']}/complete",
        headers=headers,
    )
    assert complete_project.status_code == 200, complete_project.text
    complete_payload = complete_project.json()
    assert complete_payload["message"] == "Project completed successfully."
    assert complete_payload["project"]["status"] == "completed"
    assert complete_payload["project"]["progress_percent"] == 100

    dashboard_response = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dashboard_response.status_code == 200, dashboard_response.text
    dashboard = dashboard_response.json()
    assert dashboard["total_projects"] == 1
    assert dashboard["completed_projects"] == 1
    assert dashboard["completed_tasks"] == 2
    assert dashboard["actual_hours"] == 6.0
    assert dashboard["billable_value_cents"] == 60_000
