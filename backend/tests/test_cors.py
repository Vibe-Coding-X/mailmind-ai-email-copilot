from fastapi.testclient import TestClient

from app.main import app


def test_cors_allows_localhost_frontend_with_credentials() -> None:
    client = TestClient(app)
    origin = "http://localhost:3000"

    response = client.get("/health", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_allows_loopback_ip_frontend() -> None:
    client = TestClient(app)
    origin = "http://127.0.0.1:3000"

    response = client.get("/health", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_cors_preflight_allows_credentialed_request() -> None:
    client = TestClient(app)
    origin = "http://localhost:3000"

    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_does_not_reflect_unlisted_origin() -> None:
    client = TestClient(app)

    response = client.get(
        "/health", headers={"Origin": "http://evil.example.com"}
    )

    # Unlisted origins must not be echoed back as allowed.
    assert (
        response.headers.get("access-control-allow-origin")
        != "http://evil.example.com"
    )
