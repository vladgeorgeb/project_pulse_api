from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_returns_access_token_and_creates_workspace(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"

    workspace_response = client.get(
        "/api/v1/workspaces/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert workspace_response.status_code == 200, workspace_response.text
    workspace = workspace_response.json()
    assert workspace["name"] == "Dashboard"
    assert workspace["company_name"] == "Independent Contractor"
    assert workspace["projects"] == []


def test_login_returns_access_token(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )
    assert register_response.status_code == 201, register_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "strongpass123"},
    )

    assert login_response.status_code == 200, login_response.text
    assert "access_token" in login_response.json()


def test_duplicate_registration_returns_409(client: TestClient) -> None:
    payload = {"email": "user@example.com", "password": "strongpass123"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409


def test_login_with_wrong_password_returns_401(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "strongpass123"},
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 401
