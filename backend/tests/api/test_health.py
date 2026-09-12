"""Tests for the /health and /api/health endpoints."""

from datetime import datetime

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok():
    """Verify GET /health returns HTTP 200 and standard health payload."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "TaskMate Backend"
    assert "timestamp" in data

    # Verify timestamp is valid ISO-8601
    parsed_dt = datetime.fromisoformat(data["timestamp"])
    assert parsed_dt is not None


def test_api_health_endpoint_alias():
    """Verify GET /api/health returns HTTP 200 and identical health payload."""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "TaskMate Backend"
    assert "timestamp" in data


def test_root_endpoint():
    """Verify GET / returns basic service discovery metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "TaskMate Backend"
    assert data["health"] == "/health"
    assert data["docs"] == "/docs"
