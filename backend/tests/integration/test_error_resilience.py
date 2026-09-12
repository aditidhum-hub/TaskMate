"""End-to-end integration tests for system error resilience and safe error masking (Phase 11)."""

from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from backend.app.agent.agent import TaskMateAgent
from backend.app.api.dependencies import get_current_user
from backend.app.api.routes_chat import get_agent
from backend.app.main import app
from backend.app.services.llm_service import (
    LLMAuthenticationError,
    LLMResponse,
    LLMService,
    LLMTimeoutError,
    ToolCallRequest,
)

TEST_USER_ID = "integration_test_resilience_user"


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    """Ensure dependency overrides are always cleanly restored before and after each test."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Provide a TestClient that does not raise server exceptions to verify 500 handlers."""
    return TestClient(app, raise_server_exceptions=False)


def test_e2e_llm_timeout_resilience(client):
    """Verify that downstream LLM timeout is gracefully handled without 500 crash or stack trace."""
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.chat_completion.side_effect = LLMTimeoutError("Nemotron request timed out after 30s")

    agent = TaskMateAgent(llm_service=mock_llm)
    app.dependency_overrides[get_agent] = lambda: agent
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID

    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer mock-token"},
        json={"message": "Show my tasks"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is False
    assert "timed out" in data["response"].lower()
    assert "traceback" not in response.text.lower()


def test_e2e_llm_auth_failure_resilience(client):
    """Verify that an upstream LLM API key error does not leak raw credentials or system paths."""
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.chat_completion.side_effect = LLMAuthenticationError("Unauthorized: invalid nvidia api key nvapi-12345")

    agent = TaskMateAgent(llm_service=mock_llm)
    app.dependency_overrides[get_agent] = lambda: agent
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID

    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer mock-token"},
        json={"message": "Create a task"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is False
    assert "credentials" in data["response"].lower() or "configuration" in data["response"].lower()
    # Ensure sensitive key did not leak
    assert "nvapi-12345" not in response.text


def test_e2e_arithmetic_error_resilience(client):
    """Verify that an arithmetic error (division by zero) is handled end-to-end and reported truthfully."""
    mock_llm = MagicMock(spec=LLMService)
    turn1 = LLMResponse(
        content=None,
        tool_calls=[
            ToolCallRequest(
                id="call_div_0",
                name="calculate",
                arguments={"expression": "100 / 0"},
            )
        ],
    )
    turn2 = LLMResponse(
        content="I cannot compute that because division by zero is mathematically undefined.",
        tool_calls=[],
    )
    mock_llm.chat_completion.side_effect = [turn1, turn2]

    agent = TaskMateAgent(llm_service=mock_llm)
    app.dependency_overrides[get_agent] = lambda: agent
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID

    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer mock-token"},
        json={"message": "What is 100 / 0?"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert "undefined" in data["response"].lower()
    assert len(data["tool_results"]) == 1
    assert data["tool_results"][0]["success"] is False
    assert "division by zero" in data["tool_results"][0]["error"].lower()


def test_e2e_nonexistent_task_error_resilience(client):
    """Verify that requesting an operation on a non-existent task is handled without an unhandled crash."""
    mock_llm = MagicMock(spec=LLMService)
    turn1 = LLMResponse(
        content=None,
        tool_calls=[
            ToolCallRequest(
                id="call_del_none",
                name="delete_task",
                arguments={"task_id": "ghost_task_id_999"},
            )
        ],
    )
    turn2 = LLMResponse(
        content="Task 'ghost_task_id_999' could not be found to delete.",
        tool_calls=[],
    )
    mock_llm.chat_completion.side_effect = [turn1, turn2]

    mock_service = MagicMock()
    mock_service.delete_task.return_value = False

    agent = TaskMateAgent(llm_service=mock_llm, task_service=mock_service)
    app.dependency_overrides[get_agent] = lambda: agent
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID

    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer mock-token"},
        json={"message": "Delete task ghost_task_id_999"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert "could not be found" in data["response"].lower()
    assert len(data["tool_results"]) == 1
    assert data["tool_results"][0]["success"] is False


def test_e2e_unexpected_agent_crash_sanitized_500(client):
    """Verify that an unexpected crash in agent execution is safely converted to a sanitized 500 error."""
    mock_agent = MagicMock()
    mock_agent.process_message.side_effect = RuntimeError("Fatal memory segmentation or unhandled DB fault")
    app.dependency_overrides[get_agent] = lambda: mock_agent
    app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID

    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer mock-token"},
        json={"message": "Trigger unexpected crash"},
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "detail" in data
    # Verifies that raw exception text does NOT leak
    assert "Fatal memory segmentation" not in response.text
    assert "Traceback" not in response.text


def test_e2e_unauthenticated_request_rejected(client):
    """Verify that requests without authorization fail with 401 when get_current_user is not overridden."""
    # Note: clean_dependency_overrides fixture ensures no overrides are active
    response = client.post(
        "/api/chat",
        json={"message": "Hello without auth"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers.get("WWW-Authenticate") == "Bearer"
