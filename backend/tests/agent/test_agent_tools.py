"""Comprehensive tests for Nemotron client configuration, LLM service, schemas, and tool execution."""

import json
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from backend.app.agent.schemas import ALL_TOOL_SCHEMAS
from backend.app.agent.tool_registry import ToolRegistry
from backend.app.core.config import Settings
from backend.app.services.llm_service import (
    LLMAuthenticationError,
    LLMInvalidResponseError,
    LLMResponse,
    LLMService,
    LLMTimeoutError,
)
from backend.app.services.task_service import TaskService
from backend.tests.unit.test_task_service import MockFirestore

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_db() -> MockFirestore:
    """Fresh in-memory Firestore mock instance."""
    return MockFirestore()


@pytest.fixture
def task_service(mock_db: MockFirestore) -> TaskService:
    """TaskService wired to the in-memory mock."""
    return TaskService(db=mock_db)


@pytest.fixture
def tool_registry(task_service: TaskService) -> ToolRegistry:
    """ToolRegistry wired to the test TaskService."""
    return ToolRegistry(task_service=task_service)


@pytest.fixture
def test_settings() -> Settings:
    """Settings populated with test credentials."""
    return Settings(
        LLM_PROVIDER="nemotron",
        LLM_MODEL="nvidia/nemotron-4-340b-instruct",
        NVIDIA_API_KEY="test-nvidia-key-12345",
        LLM_BASE_URL="https://integrate.api.nvidia.com/v1",
        LLM_TIMEOUT=10.0,
    )


def make_mock_response(status_code: int, json_data: dict[str, Any] | None = None, text: str = "") -> httpx.Response:
    """Create a mock httpx.Response."""
    request = httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions")
    if json_data is not None:
        content = json.dumps(json_data).encode("utf-8")
        headers = {"Content-Type": "application/json"}
    else:
        content = text.encode("utf-8")
        headers = {"Content-Type": "text/plain"}

    return httpx.Response(status_code=status_code, headers=headers, content=content, request=request)


# -----------------------------------------------------------------------------
# 1. Nemotron Client Configuration Tests
# -----------------------------------------------------------------------------


def test_nemotron_client_configuration(test_settings: Settings):
    """Test 1: Verify Nemotron client configuration and credential resolution."""
    service = LLMService(settings=test_settings)
    assert service.model == "nvidia/nemotron-4-340b-instruct"
    assert service.base_url == "https://integrate.api.nvidia.com/v1"
    assert service.api_key == "test-nvidia-key-12345"

    headers = service._get_headers()
    assert headers["Authorization"] == "Bearer test-nvidia-key-12345"
    assert headers["Content-Type"] == "application/json"


def test_nemotron_client_missing_key_raises_auth_error():
    """Verify that missing API credentials raise LLMAuthenticationError."""
    empty_settings = Settings(
        LLM_PROVIDER="nemotron",
        LLM_API_KEY="",
        NVIDIA_API_KEY="",
    )
    service = LLMService(settings=empty_settings)
    with pytest.raises(LLMAuthenticationError, match="not configured"):
        service.chat_completion(messages=[{"role": "user", "content": "Hello"}])


def test_nemotron_client_fallback_key_resolution():
    """Verify LLM_API_KEY is used if NVIDIA_API_KEY is unset."""
    fallback_settings = Settings(
        LLM_PROVIDER="nemotron",
        LLM_API_KEY="fallback-llm-key",
        NVIDIA_API_KEY="",
    )
    service = LLMService(settings=fallback_settings)
    assert service.api_key == "fallback-llm-key"
    assert service._get_headers()["Authorization"] == "Bearer fallback-llm-key"


# -----------------------------------------------------------------------------
# 2. Successful LLM Connection (Mocked API)
# -----------------------------------------------------------------------------


def test_successful_llm_connection_mocked(test_settings: Settings):
    """Test 2: Successful connection and text response using mocked API call."""
    mock_payload = {
        "id": "chatcmpl-test-001",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! I am TaskMate, your task assistant.",
                },
                "finish_reason": "stop",
            }
        ],
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = make_mock_response(200, mock_payload)

    service = LLMService(settings=test_settings, http_client=mock_client)
    response = service.chat_completion(messages=[{"role": "user", "content": "Hello"}])

    assert isinstance(response, LLMResponse)
    assert response.content == "Hello! I am TaskMate, your task assistant."
    assert not response.has_tool_calls
    assert response.finish_reason == "stop"


# -----------------------------------------------------------------------------
# 3. Structured Tool Call Generation & Parsing
# -----------------------------------------------------------------------------


def test_structured_tool_call_generation_and_parsing(test_settings: Settings):
    """Test 3: Verify structured tool calls from Nemotron response are correctly parsed."""
    mock_payload = {
        "id": "chatcmpl-tool-002",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_12345",
                            "type": "function",
                            "function": {
                                "name": "create_task",
                                "arguments": json.dumps({"title": "Study Python", "priority": "high"}),
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = make_mock_response(200, mock_payload)

    service = LLMService(settings=test_settings, http_client=mock_client)
    response = service.chat_completion(
        messages=[{"role": "user", "content": "Create a high priority task to study Python"}],
        tools=ALL_TOOL_SCHEMAS,
    )

    assert response.has_tool_calls
    assert len(response.tool_calls) == 1
    call = response.tool_calls[0]
    assert call.id == "call_12345"
    assert call.name == "create_task"
    assert call.arguments == {"title": "Study Python", "priority": "high"}


# -----------------------------------------------------------------------------
# 4. create_task Tool Execution
# -----------------------------------------------------------------------------


def test_create_task_tool_execution(tool_registry: ToolRegistry):
    """Test 4: Execute create_task tool through registry and verify persistence."""
    args = {
        "title": "Complete Assignment",
        "description": "Mathematics chapter 5 exercises",
        "priority": "high",
        "category": "Study",
    }
    result = tool_registry.execute_tool("create_task", args, user_id="user_alice")

    assert result["success"] is True
    assert "task" in result
    task = result["task"]
    assert task["title"] == "Complete Assignment"
    assert task["description"] == "Mathematics chapter 5 exercises"
    assert task["priority"] == "high"
    assert task["user_id"] == "user_alice"
    assert task["status"] == "pending"


# -----------------------------------------------------------------------------
# 5. list_tasks Tool Execution
# -----------------------------------------------------------------------------


def test_list_tasks_tool_execution(tool_registry: ToolRegistry):
    """Test 5: Execute list_tasks tool with filtering."""
    # Seed tasks for user_alice
    tool_registry.execute_tool("create_task", {"title": "Task A", "priority": "low"}, user_id="user_alice")
    tool_registry.execute_tool("create_task", {"title": "Task B", "priority": "high"}, user_id="user_alice")

    # List all tasks
    all_res = tool_registry.execute_tool("list_tasks", {}, user_id="user_alice")
    assert all_res["success"] is True
    assert all_res["count"] == 2

    # Filter by priority high
    filtered_res = tool_registry.execute_tool("list_tasks", {"priority": "high"}, user_id="user_alice")
    assert filtered_res["success"] is True
    assert filtered_res["count"] == 1
    assert filtered_res["tasks"][0]["title"] == "Task B"


# -----------------------------------------------------------------------------
# 6. get_task Tool Execution
# -----------------------------------------------------------------------------


def test_get_task_tool_execution(tool_registry: ToolRegistry):
    """Test 6: Execute get_task for valid and invalid task IDs."""
    create_res = tool_registry.execute_tool("create_task", {"title": "Task to Find"}, user_id="user_alice")
    task_id = create_res["task"]["id"]

    # Retrieve valid
    get_res = tool_registry.execute_tool("get_task", {"task_id": task_id}, user_id="user_alice")
    assert get_res["success"] is True
    assert get_res["task"]["id"] == task_id
    assert get_res["task"]["title"] == "Task to Find"

    # Retrieve non-existent
    not_found = tool_registry.execute_tool("get_task", {"task_id": "non_existent_id"}, user_id="user_alice")
    assert not_found["success"] is False
    assert "not found" in not_found["error"].lower()


# -----------------------------------------------------------------------------
# 7. update_task Tool Execution
# -----------------------------------------------------------------------------


def test_update_task_tool_execution(tool_registry: ToolRegistry):
    """Test 7: Execute update_task tool and verify modified attributes."""
    create_res = tool_registry.execute_tool("create_task", {"title": "Initial Title"}, user_id="user_alice")
    task_id = create_res["task"]["id"]

    update_args = {
        "task_id": task_id,
        "title": "Updated Title",
        "priority": "high",
        "description": "Added notes",
    }
    update_res = tool_registry.execute_tool("update_task", update_args, user_id="user_alice")

    assert update_res["success"] is True
    assert update_res["task"]["title"] == "Updated Title"
    assert update_res["task"]["priority"] == "high"
    assert update_res["task"]["description"] == "Added notes"


# -----------------------------------------------------------------------------
# 8. complete_task Tool Execution
# -----------------------------------------------------------------------------


def test_complete_task_tool_execution(tool_registry: ToolRegistry):
    """Test 8: Execute complete_task tool and verify status transition."""
    create_res = tool_registry.execute_tool("create_task", {"title": "Task to Complete"}, user_id="user_alice")
    task_id = create_res["task"]["id"]

    complete_res = tool_registry.execute_tool("complete_task", {"task_id": task_id}, user_id="user_alice")
    assert complete_res["success"] is True
    assert complete_res["task"]["status"] == "completed"


# -----------------------------------------------------------------------------
# 9. delete_task Tool Execution
# -----------------------------------------------------------------------------


def test_delete_task_tool_execution(tool_registry: ToolRegistry):
    """Test 9: Execute delete_task tool and verify task removal."""
    create_res = tool_registry.execute_tool("create_task", {"title": "Task to Delete"}, user_id="user_alice")
    task_id = create_res["task"]["id"]

    delete_res = tool_registry.execute_tool("delete_task", {"task_id": task_id}, user_id="user_alice")
    assert delete_res["success"] is True
    assert delete_res["task_id"] == task_id

    # Verify task no longer exists
    get_res = tool_registry.execute_tool("get_task", {"task_id": task_id}, user_id="user_alice")
    assert get_res["success"] is False


# -----------------------------------------------------------------------------
# 10. Invalid Tool Name
# -----------------------------------------------------------------------------


def test_invalid_tool_name(tool_registry: ToolRegistry):
    """Test 10: Reject unknown tool name gracefully without raising unhandled exceptions."""
    res = tool_registry.execute_tool("drop_database", {"table": "users"}, user_id="user_alice")
    assert res["success"] is False
    assert "unsupported tool" in res["error"].lower()


# -----------------------------------------------------------------------------
# 11. Missing Arguments
# -----------------------------------------------------------------------------


def test_missing_arguments(tool_registry: ToolRegistry):
    """Test 11: Validate required parameters are present."""
    # create_task without title
    res1 = tool_registry.execute_tool("create_task", {}, user_id="user_alice")
    assert res1["success"] is False
    assert "missing required argument 'title'" in res1["error"].lower()

    # complete_task without task_id
    res2 = tool_registry.execute_tool("complete_task", {}, user_id="user_alice")
    assert res2["success"] is False
    assert "missing required argument 'task_id'" in res2["error"].lower()

    # calculate without expression
    res3 = tool_registry.execute_tool("calculate", {}, user_id="user_alice")
    assert res3["success"] is False
    assert "missing required argument 'expression'" in res3["error"].lower()


# -----------------------------------------------------------------------------
# 12. Malformed Tool Call
# -----------------------------------------------------------------------------


def test_malformed_tool_call(tool_registry: ToolRegistry):
    """Test 12: Handle invalid JSON or malformed arguments safely."""
    # Invalid JSON string
    res = tool_registry.execute_tool("create_task", "{malformed_json: true,", user_id="user_alice")
    assert res["success"] is False
    assert "malformed tool arguments json" in res["error"].lower()

    # Non-dict and non-string argument type
    res_type = tool_registry.execute_tool("create_task", 12345, user_id="user_alice")  # type: ignore
    assert res_type["success"] is False
    assert "must be a dict or json string" in res_type["error"].lower()


# -----------------------------------------------------------------------------
# 13. Nemotron API Failure & Timeout
# -----------------------------------------------------------------------------


def test_nemotron_api_failure_and_timeout(test_settings: Settings):
    """Test 13: Handle upstream Nemotron API errors (500, 401, timeout)."""
    mock_client = MagicMock(spec=httpx.Client)

    # Test HTTP 500 Internal Server Error
    mock_client.post.return_value = make_mock_response(500, text="Internal Server Error")
    service = LLMService(settings=test_settings, http_client=mock_client)

    with pytest.raises(LLMInvalidResponseError, match="HTTP 500"):
        service.chat_completion(messages=[{"role": "user", "content": "Test"}])

    # Test HTTP 401 Unauthorized
    mock_client.post.return_value = make_mock_response(401, text="Unauthorized")
    with pytest.raises(LLMAuthenticationError, match="Invalid or unauthorized"):
        service.chat_completion(messages=[{"role": "user", "content": "Test"}])

    # Test Timeout Exception
    mock_client.post.side_effect = httpx.TimeoutException("Connection timed out")
    with pytest.raises(LLMTimeoutError, match="timed out"):
        service.chat_completion(messages=[{"role": "user", "content": "Test"}])


# -----------------------------------------------------------------------------
# 14. User Isolation
# -----------------------------------------------------------------------------


def test_user_isolation(tool_registry: ToolRegistry):
    """Test 14: Ensure User A cannot access or manipulate User B's tasks."""
    # Alice creates a task
    alice_res = tool_registry.execute_tool("create_task", {"title": "Alice's Secret"}, user_id="user_alice")
    alice_task_id = alice_res["task"]["id"]

    # Bob attempts to get Alice's task
    bob_get = tool_registry.execute_tool("get_task", {"task_id": alice_task_id}, user_id="user_bob")
    assert bob_get["success"] is False
    assert "not found" in bob_get["error"].lower()

    # Bob attempts to complete Alice's task
    bob_complete = tool_registry.execute_tool("complete_task", {"task_id": alice_task_id}, user_id="user_bob")
    assert bob_complete["success"] is False

    # Bob attempts to delete Alice's task
    bob_delete = tool_registry.execute_tool("delete_task", {"task_id": alice_task_id}, user_id="user_bob")
    assert bob_delete["success"] is False

    # Bob listing tasks does not show Alice's task
    bob_list = tool_registry.execute_tool("list_tasks", {}, user_id="user_bob")
    assert bob_list["success"] is True
    assert bob_list["count"] == 0


# -----------------------------------------------------------------------------
# 15. User ID Cannot Be Overridden by LLM Input
# -----------------------------------------------------------------------------


def test_user_id_cannot_be_overridden_by_llm(tool_registry: ToolRegistry):
    """Test 15: Injected user_id takes precedence; LLM user_id parameter is stripped."""
    # An LLM output might attempt to specify user_id in arguments
    malicious_args = {
        "title": "Injected Task",
        "user_id": "user_victim",  # Rogue argument from LLM
    }

    result = tool_registry.execute_tool("create_task", malicious_args, user_id="user_authenticated")
    assert result["success"] is True
    task = result["task"]

    # The created task must belong to authenticated user, NOT the injected user
    assert task["user_id"] == "user_authenticated"
    assert task["user_id"] != "user_victim"

    # Verify victim has no tasks
    victim_list = tool_registry.execute_tool("list_tasks", {}, user_id="user_victim")
    assert victim_list["count"] == 0


# -----------------------------------------------------------------------------
# 16. Utility Tools via ToolRegistry
# -----------------------------------------------------------------------------


def test_utility_tools_via_registry(tool_registry: ToolRegistry):
    """Verify Calculator and Date/Time tools execute safely through ToolRegistry."""
    # Test safe calculation
    calc_res = tool_registry.execute_tool("calculate", {"expression": "25 * 4 + 10"}, user_id="user_alice")
    assert calc_res["success"] is True
    assert calc_res["result"] == 110.0

    # Test calculation error
    calc_err = tool_registry.execute_tool("calculate", {"expression": "10 / 0"}, user_id="user_alice")
    assert calc_err["success"] is False
    assert "division by zero" in calc_err["error"].lower()

    # Test date/time resolution
    dt_res = tool_registry.execute_tool("get_date_time", {"query": "tomorrow"}, user_id="user_alice")
    assert dt_res["success"] is True
    assert "iso_date" in dt_res["result"]


# -----------------------------------------------------------------------------
# 17. Complete Conversation Turn Flow
# -----------------------------------------------------------------------------


def test_complete_conversation_turn_flow(test_settings: Settings, tool_registry: ToolRegistry):
    """Verify two-turn conversation flow with tool execution and synthesis."""
    # Turn 1 mock: Nemotron requests create_task
    turn1_payload = {
        "id": "chatcmpl-t1",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_abc",
                            "type": "function",
                            "function": {
                                "name": "create_task",
                                "arguments": json.dumps({"title": "Submit Assignment", "priority": "high"}),
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
    }

    # Turn 2 mock: Nemotron synthesizes response after seeing tool observation
    turn2_payload = {
        "id": "chatcmpl-t2",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "I have created the task 'Submit Assignment' with high priority for you.",
                },
                "finish_reason": "stop",
            }
        ],
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = [
        make_mock_response(200, turn1_payload),
        make_mock_response(200, turn2_payload),
    ]

    service = LLMService(
        settings=test_settings,
        tool_registry=tool_registry,
        http_client=mock_client,
    )

    result = service.run_conversation_turn(
        user_id="user_alice",
        user_prompt="Please create a high priority task to submit my assignment.",
    )

    assert result["success"] is True
    assert "Submit Assignment" in result["response"]
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["name"] == "create_task"
    assert len(result["tool_results"]) == 1
    assert result["tool_results"][0]["success"] is True
    assert result["tool_results"][0]["task"]["title"] == "Submit Assignment"
    assert result["tool_results"][0]["task"]["user_id"] == "user_alice"


def test_conversation_turn_unauthenticated():
    """Verify conversation turn fails cleanly without user_id."""
    service = LLMService()
    result = service.run_conversation_turn(user_id="", user_prompt="Hello")
    assert result["success"] is False
    assert "authentication required" in result["response"].lower()


def test_xml_tool_name_and_arguments_sanitization(tool_registry: ToolRegistry):
    """Verify tool names and arguments containing trailing XML or closing tags from LLM are sanitized."""
    # LLM emits 'list_tasks\n</function' as tool name
    res = tool_registry.execute_tool(
        "list_tasks\n</function",
        '{"status": "pending"}\n</function>',
        user_id="user_alice",
    )
    assert res["success"] is True
    assert "tasks" in res

    # Dotted tool name: 'functions.create_task'
    res2 = tool_registry.execute_tool(
        "functions.create_task",
        '{"title": "Test Dotted Name"}\n</tool_call>',
        user_id="user_alice",
    )
    assert res2["success"] is True
    assert res2["task"]["title"] == "Test Dotted Name"


def test_firestore_disabled_fallback_isolation():
    """Verify that when Firestore is disabled / unavailable, operations fallback to in-memory store cleanly."""
    from backend.app.services.task_service import TaskService
    from unittest.mock import MagicMock

    # Clean up any pre-existing fallback state for these test-scoped user IDs
    # to prevent cross-test pollution from the shared ClassVar dict.
    for uid in ("user_iso_a", "user_iso_b"):
        TaskService._fallback_store.pop(uid, None)

    # Service with no Firestore connection simulation
    service = TaskService(db=None)
    # Monkeypatch _get_tasks_collection to raise Google API permission denied
    mock_coll = MagicMock()
    mock_coll.document.side_effect = RuntimeError("403 Cloud Firestore API disabled")
    mock_coll.stream.side_effect = RuntimeError("403 Cloud Firestore API disabled")
    service._get_tasks_collection = MagicMock(return_value=mock_coll)

    created = service.create_task("user_iso_a", {"title": "Task For User A"})
    assert created.title == "Task For User A"
    assert created.user_id == "user_iso_a"

    # Verify user_iso_b cannot see user_iso_a's tasks
    b_tasks = service.list_tasks("user_iso_b")
    assert len(b_tasks) == 0

    # User A can see their task
    a_tasks = service.list_tasks("user_iso_a")
    assert len(a_tasks) == 1
    assert a_tasks[0].id == created.id

    # Teardown: clear test-scoped entries so subsequent tests start clean
    for uid in ("user_iso_a", "user_iso_b"):
        TaskService._fallback_store.pop(uid, None)
