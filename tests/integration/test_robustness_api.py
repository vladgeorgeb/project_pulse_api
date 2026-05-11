from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200, response.text
    assert response.json() == {"status": "ok", "environment": "test"}


def test_configured_cors_origin_is_allowed(client: TestClient) -> None:
    response = client.options(
        "/api/v1/projects",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
