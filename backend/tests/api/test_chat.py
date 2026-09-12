"""Automated test suite for FastAPI /api/chat endpoint (Phase 8 API Layer)."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from backend.app.agent.agent import AgentResponse
from backend.app.api.dependencies import get_current_user
from backend.app.api.routes_chat import get_agent
from backend.app.main import app


@pytest.fixture
def client():
    """Create FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def mock_agent():
    """Create a mock TaskMateAgent."""
    agent = MagicMock()
    return agent


# -----------------------------------------------------------------------------
# 1. Health & Unprotected Route Tests
# -----------------------------------------------------------------------------


def test_health_endpoint(client):
    """Verify GET /health returns HTTP 200 with service metadata."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert "TaskMate" in data["service"]


def test_api_health_endpoint_alias(client):
    """Verify GET /api/health alias returns HTTP 200."""
    response = client.get("/api/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ok"


# -----------------------------------------------------------------------------
# 2. Authentication & Authorization Boundary Tests
# -----------------------------------------------------------------------------


def test_chat_missing_auth_header_returns_401(client):
    """Verify POST /api/chat without Authorization header returns HTTP 401."""
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Authentication required" in response.json()["detail"]


def test_chat_non_bearer_scheme_returns_401(client):
    """Verify non-Bearer Authorization scheme returns HTTP 401."""
    response = client.post(
        "/api/chat",
        json={"message": "Hello"},
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Bearer" in response.json()["detail"]


def test_chat_invalid_token_returns_401(client):
    """Verify invalid or unverified Bearer token returns HTTP 401."""
    with patch("backend.app.api.dependencies.verify_firebase_token") as mock_verify:
        from fastapi import HTTPException

        mock_verify.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase ID token",
        )
        response = client.post(
            "/api/chat",
            json={"message": "Hello"},
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# -----------------------------------------------------------------------------
# 3. Request Validation Tests
# -----------------------------------------------------------------------------


def test_chat_empty_message_returns_422(client):
    """Verify empty string message is rejected with HTTP 422."""
    app.dependency_overrides[get_current_user] = lambda: "test_user_123"
    try:
        response = client.post("/api/chat", json={"message": ""})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    finally:
        app.dependency_overrides.clear()


def test_chat_whitespace_only_message_returns_422(client):
    """Verify whitespace-only message is rejected with HTTP 422."""
    app.dependency_overrides[get_current_user] = lambda: "test_user_123"
    try:
        response = client.post("/api/chat", json={"message": "    \n   "})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "whitespace" in response.text
    finally:
        app.dependency_overrides.clear()


def test_chat_missing_message_field_returns_422(client):
    """Verify payload without message field is rejected with HTTP 422."""
    app.dependency_overrides[get_current_user] = lambda: "test_user_123"
    try:
        response = client.post("/api/chat", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    finally:
        app.dependency_overrides.clear()


def test_chat_forbids_extra_fields(client):
    """Verify unexpected extra fields are rejected with HTTP 422."""
    app.dependency_overrides[get_current_user] = lambda: "test_user_123"
    try:
        response = client.post(
            "/api/chat",
            json={"message": "Hello", "unapproved_field": "injected"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 4. Successful Chat Execution Scenarios
# -----------------------------------------------------------------------------


def test_chat_conversational_turn_success(client, mock_agent):
    """Verify conversational turn without tools returns HTTP 200 with ChatResponse."""
    mock_agent.process_message.return_value = AgentResponse(
        success=True,
        response="Hello! I am TaskMate, your task management assistant.",
        tool_calls=[],
        tool_results=[],
        messages=[
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hello! I am TaskMate, your task management assistant."},
        ],
    )

    app.dependency_overrides[get_current_user] = lambda: "verified_user_123"
    app.dependency_overrides[get_agent] = lambda: mock_agent

    try:
        response = client.post("/api/chat", json={"message": "Hello!"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["response"] == "Hello! I am TaskMate, your task management assistant."
        assert data["tool_used"] is None
        assert data["created_task"] is None
        assert data["tool_calls"] == []
        assert data["tool_results"] == []
        assert len(data["messages"]) == 2

        # Verify agent was called with authenticated user_id
        mock_agent.process_message.assert_called_once_with(
            user_id="verified_user_123",
            message="Hello!",
            message_history=None,
        )
    finally:
        app.dependency_overrides.clear()


def test_chat_with_tool_call_success(client, mock_agent):
    """Verify turn involving utility tool returns populated tool_used and tool_calls."""
    mock_agent.process_message.return_value = AgentResponse(
        success=True,
        response="15 divided by 3 is 5.",
        tool_calls=[{"id": "c1", "name": "calculate", "arguments": {"expression": "15 / 3"}}],
        tool_results=[{"success": True, "result": 5.0}],
        messages=[],
    )

    app.dependency_overrides[get_current_user] = lambda: "verified_user_123"
    app.dependency_overrides[get_agent] = lambda: mock_agent

    try:
        response = client.post("/api/chat", json={"message": "What is 15 / 3?"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["tool_used"] == "calculate"
        assert len(data["tool_calls"]) == 1
        assert data["tool_calls"][0]["name"] == "calculate"
        assert data["created_task"] is None
    finally:
        app.dependency_overrides.clear()


def test_chat_with_create_task_success(client, mock_agent):
    """Verify turn involving task creation returns populated created_task."""
    mock_task = {
        "id": "task_abc",
        "title": "Study Python",
        "priority": "high",
        "status": "pending",
        "due_date": "2026-09-13",
    }
    mock_agent.process_message.return_value = AgentResponse(
        success=True,
        response="I've created your task 'Study Python'.",
        tool_calls=[{"id": "c2", "name": "create_task", "arguments": {"title": "Study Python"}}],
        tool_results=[{"success": True, "task": mock_task}],
        messages=[],
    )

    app.dependency_overrides[get_current_user] = lambda: "verified_user_123"
    app.dependency_overrides[get_agent] = lambda: mock_agent

    try:
        response = client.post("/api/chat", json={"message": "Create task to study Python"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["tool_used"] == "create_task"
        assert data["created_task"] == mock_task
    finally:
        app.dependency_overrides.clear()


def test_chat_preserves_message_history(client, mock_agent):
    """Verify client-supplied message_history is passed cleanly to agent."""
    mock_agent.process_message.return_value = AgentResponse(
        success=True,
        response="Paris is indeed the capital.",
        tool_calls=[],
        tool_results=[],
        messages=[],
    )

    app.dependency_overrides[get_current_user] = lambda: "verified_user_123"
    app.dependency_overrides[get_agent] = lambda: mock_agent

    history = [
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "Paris"},
    ]

    try:
        response = client.post(
            "/api/chat",
            json={"message": "Are you sure?", "message_history": history},
        )
        assert response.status_code == status.HTTP_200_OK
        mock_agent.process_message.assert_called_once_with(
            user_id="verified_user_123",
            message="Are you sure?",
            message_history=history,
        )
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 5. Error & Exception Handling Tests
# -----------------------------------------------------------------------------


def test_chat_agent_unexpected_exception_returns_500(client, mock_agent):
    """Verify unhandled exception in agent execution returns sanitized HTTP 500."""
    mock_agent.process_message.side_effect = RuntimeError("Database connection crashed")

    app.dependency_overrides[get_current_user] = lambda: "verified_user_123"
    app.dependency_overrides[get_agent] = lambda: mock_agent

    try:
        response = client.post("/api/chat", json={"message": "Hello"})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        # Stack trace or internal DB details must NOT leak
        assert "Database connection crashed" not in response.text
        assert "internal error" in response.text.lower()
    finally:
        app.dependency_overrides.clear()


def test_chat_agent_value_error_returns_422(client, mock_agent):
    """Verify ValueError in agent returns HTTP 422."""
    mock_agent.process_message.side_effect = ValueError("Invalid operation arguments")

    app.dependency_overrides[get_current_user] = lambda: "verified_user_123"
    app.dependency_overrides[get_agent] = lambda: mock_agent

    try:
        response = client.post("/api/chat", json={"message": "Hello"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Invalid operation arguments" in response.text
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 6. CORS Configuration Tests
# -----------------------------------------------------------------------------


def test_cors_headers_on_preflight(client):
    """Verify CORS preflight OPTIONS request returns configured origin headers."""
    response = client.options(
        "/api/chat",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in response.headers.get("access-control-allow-methods", "")
