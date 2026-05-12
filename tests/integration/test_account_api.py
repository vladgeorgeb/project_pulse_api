from __future__ import annotations

from fastapi.testclient import TestClient


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "strongpass123"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def _login_admin(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "adminpass123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_project(client: TestClient, token: str, title: str, **overrides: object):
    response = client.post(
        "/api/v1/projects",
        json={
            "title": title,
            "client_name": title,
            "contract_type": "fixed_price",
            "fixed_price_cents": 100000,
            "payment_cadence": "milestone",
            **overrides,
        },
        headers=_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_user_can_export_only_their_own_account_data(client: TestClient) -> None:
    first_token = _register(client, "first@example.com")
    second_token = _register(client, "second@example.com")

    workspace_response = client.put(
        "/api/v1/workspaces/me",
        json={
            "name": "Consulting HQ",
            "company_name": "Pulse Consulting",
            "monthly_capacity_hours": 120,
        },
        headers=_headers(first_token),
    )
    assert workspace_response.status_code == 200, workspace_response.text

    first_project = _create_project(
        client,
        first_token,
        "Exported Retainer",
        client_name="Acme",
        contract_type="monthly_retainer",
        monthly_rate_cents=250000,
        payment_cadence="monthly",
        billing_notes="Paid by wire.",
    )
    _create_project(client, second_token, "Other User Project", client_name="Other")

    task_response = client.post(
        f"/api/v1/projects/{first_project['id']}/tasks",
        json={"title": "Export task", "estimated_minutes": 90},
        headers=_headers(first_token),
    )
    assert task_response.status_code == 201, task_response.text

    response = client.get("/api/v1/account/export", headers=_headers(first_token))

    assert response.status_code == 200, response.text
    export = response.json()
    assert export["schema_version"] == 1
    assert isinstance(export["account"]["id"], int)
    assert export["account"]["email"] == "first@example.com"
    assert export["account"]["is_admin"] is False
    assert "password_hash" not in export["account"]
    assert export["business_profile"]["company_name"] == "Pulse Consulting"
    assert export["business_profile"]["workspace_name"] == "Consulting HQ"
    assert export["clients"] == [{"name": "Acme", "project_ids": [first_project["id"]]}]
    assert [project["title"] for project in export["projects"]] == ["Exported Retainer"]
    assert [task["title"] for task in export["tasks"]] == ["Export task"]
    assert len(export["billing"]["payment_records"]) == 0
    assert "Other User Project" not in response.text


def test_user_can_delete_account_with_password_confirmation(
    client: TestClient,
) -> None:
    user_token = _register(client, "delete-me@example.com")
    other_token = _register(client, "other@example.com")
    admin_token = _login_admin(client)

    _create_project(client, user_token, "Delete Me Project")
    other_project = _create_project(client, other_token, "Other Project")
    feedback_response = client.post(
        "/api/v1/feedback",
        json={"category": "idea", "message": "Please keep this feedback around."},
        headers=_headers(user_token),
    )
    assert feedback_response.status_code == 201, feedback_response.text

    wrong_password = client.request(
        "DELETE",
        "/api/v1/account",
        json={"password": "wrongpassword"},
        headers=_headers(user_token),
    )
    assert wrong_password.status_code == 401
    assert (
        client.get("/api/v1/workspaces/me", headers=_headers(user_token)).status_code
        == 200
    )

    response = client.request(
        "DELETE",
        "/api/v1/account",
        json={"password": "strongpass123"},
        headers=_headers(user_token),
    )

    assert response.status_code == 204, response.text
    assert (
        client.get("/api/v1/workspaces/me", headers=_headers(user_token)).status_code
        == 401
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "delete-me@example.com", "password": "strongpass123"},
    )
    assert login_response.status_code == 401

    other_projects = client.get("/api/v1/projects", headers=_headers(other_token))
    assert other_projects.status_code == 200, other_projects.text
    assert [project["id"] for project in other_projects.json()["items"]] == [
        other_project["id"]
    ]

    users = client.get("/api/v1/admin/users", headers=_headers(admin_token)).json()
    assert "delete-me@example.com" not in {user["email"] for user in users}
    assert "other@example.com" in {user["email"] for user in users}
    admin_projects = client.get(
        "/api/v1/admin/projects",
        headers=_headers(admin_token),
    ).json()
    assert [project["title"] for project in admin_projects] == ["Other Project"]
    feedback = client.get(
        "/api/v1/admin/feedback", headers=_headers(admin_token)
    ).json()
    assert len(feedback) == 1
    assert feedback[0]["user_id"] is None


def test_admin_self_deletion_requires_explicit_confirmation(
    client: TestClient,
) -> None:
    admin_token = _login_admin(client)

    response = client.request(
        "DELETE",
        "/api/v1/account",
        json={"password": "adminpass123"},
        headers=_headers(admin_token),
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Admin self-deletion requires confirm_admin_self_deletion=true."
    )
    admin_users = client.get("/api/v1/admin/users", headers=_headers(admin_token))
    assert admin_users.status_code == 200
