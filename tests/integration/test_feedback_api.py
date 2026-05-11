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


def test_authenticated_user_can_submit_feedback(client: TestClient) -> None:
    token = _register_user(client, "user@example.com")

    response = client.post(
        "/api/v1/feedback",
        json={
            "category": "bug",
            "message": "The project filter panel feels confusing.",
            "page_url": "https://app.example.com/projects?status=active",
        },
        headers={**_headers(token), "User-Agent": "pytest-client"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["category"] == "bug"
    assert body["status"] == "new"
    assert body["message"] == "The project filter panel feels confusing."
    assert body["page_url"] == "https://app.example.com/projects?status=active"
    assert "user_agent" not in body


def test_feedback_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/feedback",
        json={"category": "idea", "message": "Please add calendar reminders."},
    )

    assert response.status_code == 401


def test_feedback_validates_category_and_message_length(client: TestClient) -> None:
    token = _register_user(client, "user@example.com")

    bad_category = client.post(
        "/api/v1/feedback",
        json={"category": "sales", "message": "Please add calendar reminders."},
        headers=_headers(token),
    )
    short_message = client.post(
        "/api/v1/feedback",
        json={"category": "idea", "message": "too short"},
        headers=_headers(token),
    )

    assert bad_category.status_code == 422
    assert short_message.status_code == 422


def test_admin_can_list_feedback_and_normal_user_cannot(client: TestClient) -> None:
    user_token = _register_user(client, "user@example.com")
    submit_response = client.post(
        "/api/v1/feedback",
        json={"category": "question", "message": "How should I track retainers?"},
        headers={**_headers(user_token), "User-Agent": "pytest-client"},
    )
    assert submit_response.status_code == 201, submit_response.text

    normal_user_response = client.get(
        "/api/v1/admin/feedback",
        headers=_headers(user_token),
    )
    assert normal_user_response.status_code == 403

    admin_token = _login_admin(client)
    admin_response = client.get(
        "/api/v1/admin/feedback",
        headers=_headers(admin_token),
    )

    assert admin_response.status_code == 200, admin_response.text
    feedback = admin_response.json()
    assert len(feedback) == 1
    assert feedback[0]["category"] == "question"
    assert feedback[0]["user_id"] is not None
    assert feedback[0]["user_agent"] == "pytest-client"
