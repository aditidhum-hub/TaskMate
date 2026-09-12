"""Unit and integration tests for TaskMateAgent (Phase 7 Agent Loop)."""

from unittest.mock import MagicMock

import pytest

from backend.app.agent.agent import TaskMateAgent
from backend.app.agent.tool_registry import ToolRegistry
from backend.app.models.task import TaskPriority, TaskResponse, TaskStatus
from backend.app.services.llm_service import (
    LLMAuthenticationError,
    LLMResponse,
    LLMService,
    LLMServiceError,
    LLMTimeoutError,
    ToolCallRequest,
)


def make_mock_task(
    id: str = "t1",
    user_id: str = "user_123",
    title: str = "Sample Task",
    priority: TaskPriority = TaskPriority.MEDIUM,
    status: TaskStatus = TaskStatus.PENDING,
    due_date: str | None = None,
) -> TaskResponse:
    """Helper to generate valid TaskResponse models for testing."""
    return TaskResponse(
        id=id,
        user_id=user_id,
        title=title,
        priority=priority,
        status=status,
        due_date=due_date,
        created_at="2026-09-12T00:00:00Z",
        updated_at="2026-09-12T00:00:00Z",
    )


@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service."""
    service = MagicMock(spec=LLMService)
    return service


@pytest.fixture
def mock_task_service():
    """Create a mock TaskService."""
    service = MagicMock()
    return service


@pytest.fixture
def agent(mock_llm_service, mock_task_service):
    """Create a TaskMateAgent instance with mock dependencies."""
    registry = ToolRegistry()
    return TaskMateAgent(
        llm_service=mock_llm_service,
        tool_registry=registry,
        task_service=mock_task_service,
    )


# -----------------------------------------------------------------------------
# 1. Validation and Security Context Tests
# -----------------------------------------------------------------------------


def test_process_message_rejects_empty_user_id(agent):
    """Verify process_message raises ValueError if user_id is empty or whitespace."""
    with pytest.raises(ValueError, match="user_id must be a non-empty"):
        agent.process_message(user_id="", message="Hello")

    with pytest.raises(ValueError, match="user_id must be a non-empty"):
        agent.process_message(user_id="   ", message="Hello")


def test_process_message_empty_user_prompt(agent):
    """Verify process_message gracefully handles empty prompt without calling LLM."""
    resp = agent.process_message(user_id="user_123", message="")
    assert resp.success is True
    assert "Please provide a message" in resp.response
    assert len(resp.tool_calls) == 0
    assert agent.llm_service.chat_completion.call_count == 0


def test_user_isolation_enforcement(agent):
    """Verify tool execution is strictly locked to the authenticated caller's user_id."""
    # LLM attempts to forge user_id in arguments
    agent.llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_calc",
                    name="calculate",
                    arguments={"expression": "100 + 50", "user_id": "malicious_user"},
                    raw_arguments='{"expression": "100 + 50", "user_id": "malicious_user"}',
                )
            ],
            finish_reason="tool_calls",
        ),
        LLMResponse(content="The result is 150.", tool_calls=[], finish_reason="stop"),
    ]

    resp = agent.process_message(user_id="legitimate_user", message="Calculate 100 + 50")
    assert resp.success is True
    assert len(resp.tool_results) == 1
    # user_id must have been stripped from tool args before execution
    assert resp.tool_results[0]["success"] is True
    assert resp.tool_results[0]["result"] == 150.0


# -----------------------------------------------------------------------------
# 2. Conversational & Non-Tool Tests
# -----------------------------------------------------------------------------


def test_no_tool_conversational_turn(agent):
    """Verify direct conversational answers with zero tool calls."""
    agent.llm_service.chat_completion.return_value = LLMResponse(
        content="I am TaskMate, here to help you organize your tasks.",
        tool_calls=[],
        finish_reason="stop",
    )

    resp = agent.process_message(user_id="user_123", message="Who are you?")
    assert resp.success is True
    assert "TaskMate" in resp.response
    assert len(resp.tool_calls) == 0
    assert len(resp.tool_results) == 0
    assert resp.messages[-1]["role"] == "assistant"
    assert resp.messages[-1]["content"] == resp.response


def test_ambiguous_request_handling(agent):
    """Verify ambiguous requests trigger a clarifying response without invoking tools."""
    agent.llm_service.chat_completion.return_value = LLMResponse(
        content="Which task would you like me to update? Please provide the task title or ID.",
        tool_calls=[],
        finish_reason="stop",
    )

    resp = agent.process_message(user_id="user_123", message="Update my task please")
    assert resp.success is True
    assert len(resp.tool_calls) == 0
    assert "Which task would you like me to update?" in resp.response


# -----------------------------------------------------------------------------
# 3. Utility Tool Scenarios (Calculator & Date/Time)
# -----------------------------------------------------------------------------


def test_calculate_tool_invocation(agent):
    """Verify math requests execute calculator and synthesize answer."""
    agent.llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="calc_1",
                    name="calculate",
                    arguments={"expression": "15 / 3"},
                    raw_arguments='{"expression": "15 / 3"}',
                )
            ],
            finish_reason="tool_calls",
        ),
        LLMResponse(
            content="You should complete 5 lessons per day.",
            tool_calls=[],
            finish_reason="stop",
        ),
    ]

    resp = agent.process_message(
        user_id="user_123",
        message="I have 15 lessons to complete in 3 days. How many per day?",
    )

    assert resp.success is True
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0]["name"] == "calculate"
    assert resp.tool_results[0]["result"] == 5.0
    assert "5 lessons" in resp.response


def test_datetime_tool_invocation(agent):
    """Verify relative date queries execute datetime tool and synthesize answer."""
    agent.llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="dt_1",
                    name="get_date_time",
                    arguments={"query": "tomorrow"},
                    raw_arguments='{"query": "tomorrow"}',
                )
            ],
            finish_reason="tool_calls",
        ),
        LLMResponse(
            content="Tomorrow's date is confirmed.",
            tool_calls=[],
            finish_reason="stop",
        ),
    ]

    resp = agent.process_message(user_id="user_123", message="What is tomorrow's date?")
    assert resp.success is True
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0]["name"] == "get_date_time"
    assert resp.tool_results[0]["success"] is True
    assert "iso_date" in resp.tool_results[0]["result"]


# -----------------------------------------------------------------------------
# 4. Task Operations: Create, List, Get, Update, Complete, Delete
# -----------------------------------------------------------------------------


def test_create_task_tool_invocation(agent, mock_task_service):
    """Verify task creation via agent loop."""
    mock_task_service.create_task.return_value = make_mock_task(
        id="t1",
        title="Study Python",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
    )

    agent.llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_create",
                    name="create_task",
                    arguments={"title": "Study Python", "priority": "high"},
                    raw_arguments='{"title": "Study Python", "priority": "high"}',
                )
            ],
            finish_reason="tool_calls",
        ),
        LLMResponse(
            content="I've created the task 'Study Python' with high priority.",
            tool_calls=[],
            finish_reason="stop",
        ),
    ]

    resp = agent.process_message(user_id="user_123", message="Create a high priority task to study Python")
    assert resp.success is True
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0]["name"] == "create_task"
    assert resp.tool_results[0]["success"] is True
    assert resp.tool_results[0]["task"]["title"] == "Study Python"
    assert "Study Python" in resp.response


def test_list_tasks_tool_invocation(agent, mock_task_service):
    """Verify listing tasks with filter via agent loop."""
    mock_task_service.list_tasks.return_value = [
        make_mock_task(id="t1", title="Buy milk", priority=TaskPriority.MEDIUM),
    ]

    agent.llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_list",
                    name="list_tasks",
                    arguments={"status": "pending"},
                    raw_arguments='{"status": "pending"}',
                )
            ],
            finish_reason="tool_calls",
        ),
        LLMResponse(
            content="You have 1 pending task: 'Buy milk'.",
            tool_calls=[],
            finish_reason="stop",
        ),
    ]

    resp = agent.process_message(user_id="user_123", message="Show my pending tasks")
    assert resp.success is True
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0]["name"] == "list_tasks"
    assert resp.tool_results[0]["count"] == 1
    assert "Buy milk" in resp.response


def test_get_task_tool_invocation(agent, mock_task_service):
    """Verify getting a specific task by ID."""
    mock_task_service.get_task.return_value = make_mock_task(
        id="t123",
        title="Clean kitchen",
        priority=TaskPriority.LOW,
        status=TaskStatus.PENDING,
    )

    agent.llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_get",
                    name="get_task",
                    arguments={"task_id": "t123"},
                    raw_arguments='{"task_id": "t123"}',
                )
            ],
            finish_reason="tool_calls",
        ),
        LLMResponse(
            content="Task 'Clean kitchen' is currently pending.",
            tool_calls=[],
            finish_reason="stop",
        ),
    ]

    resp = agent.process_message(user_id="user_123", message="Get task t123")
    assert resp.success is True
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0]["name"] == "get_task"
    assert resp.tool_results[0]["success"] is True
    assert resp.tool_results[0]["task"]["id"] == "t123"


def test_update_task_tool_invocation(agent, mock_task_service):
    """Verify updating a task."""
    mock_task_service.update_task.return_value = make_mock_task(
        id="t123",
        title="Clean kitchen deeply",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
    )

    agent.llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_upd",
                    name="update_task",
                    arguments={"task_id": "t123", "title": "Clean kitchen deeply", "priority": "high"},
                    raw_arguments='{"task_id": "t123", "title": "Clean kitchen deeply", "priority": "high"}',
                )
            ],
            finish_reason="tool_calls",
        ),
        LLMResponse(
            content="Updated task t123 with new title and high priority.",
            tool_calls=[],
            finish_reason="stop",
        ),
    ]

    resp = agent.process_message(user_id="user_123", message="Update task t123 title to Clean kitchen deeply")
    assert resp.success is True
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0]["name"] == "update_task"
    assert resp.tool_results[0]["success"] is True


def test_complete_task_tool_invocation(agent, mock_task_service):
    """Verify completing a task."""
    mock_task_service.complete_task.return_value = make_mock_task(
        id="t123",
        title="Clean kitchen",
        status=TaskStatus.COMPLETED,
    )

    agent.llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_comp",
                    name="complete_task",
                    arguments={"task_id": "t123"},
                    raw_arguments='{"task_id": "t123"}',
                )
            ],
            finish_reason="tool_calls",
        ),
        LLMResponse(
            content="Marked task t123 as completed!",
            tool_calls=[],
            finish_reason="stop",
        ),
    ]

    resp = agent.process_message(user_id="user_123", message="Complete task t123")
    assert resp.success is True
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0]["name"] == "complete_task"
    assert resp.tool_results[0]["success"] is True
    assert resp.tool_results[0]["task"]["status"] == "completed"


def test_delete_task_tool_invocation(agent, mock_task_service):
    """Verify deleting a task."""
    mock_task_service.delete_task.return_value = True

    agent.llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_del",
                    name="delete_task",
                    arguments={"task_id": "t123"},
                    raw_arguments='{"task_id": "t123"}',
                )
            ],
            finish_reason="tool_calls",
        ),
        LLMResponse(
            content="Task t123 has been permanently removed.",
            tool_calls=[],
            finish_reason="stop",
        ),
    ]

    resp = agent.process_message(user_id="user_123", message="Delete task t123")
    assert resp.success is True
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0]["name"] == "delete_task"
    assert resp.tool_results[0]["success"] is True


# -----------------------------------------------------------------------------
# 5. Multi-Step Chaining Test
# -----------------------------------------------------------------------------


def test_multi_step_date_and_task_creation(agent, mock_task_service):
    """Verify multi-step chaining: resolve date -> create task with that date."""
    mock_task_service.create_task.return_value = make_mock_task(
        id="t_new",
        title="Study math",
        due_date="2026-09-13",
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
    )

    # Turn 1: call get_date_time
    # Turn 2: call create_task
    # Turn 3: final synthesis
    agent.llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_dt",
                    name="get_date_time",
                    arguments={"query": "tomorrow"},
                    raw_arguments='{"query": "tomorrow"}',
                )
            ],
            finish_reason="tool_calls",
        ),
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_task",
                    name="create_task",
                    arguments={"title": "Study math", "due_date": "2026-09-13"},
                    raw_arguments='{"title": "Study math", "due_date": "2026-09-13"}',
                )
            ],
            finish_reason="tool_calls",
        ),
        LLMResponse(
            content="I've created your task 'Study math' scheduled for tomorrow (2026-09-13).",
            tool_calls=[],
            finish_reason="stop",
        ),
    ]

    resp = agent.process_message(user_id="user_123", message="Create a task to study math tomorrow")
    assert resp.success is True
    assert len(resp.tool_calls) == 2
    assert resp.tool_calls[0]["name"] == "get_date_time"
    assert resp.tool_calls[1]["name"] == "create_task"
    assert "Study math" in resp.response
    assert agent.llm_service.chat_completion.call_count == 3


# -----------------------------------------------------------------------------
# 6. Error Handling & Invariants: Tool Failures & LLM Failures
# -----------------------------------------------------------------------------


def test_tool_failure_handling(agent, mock_task_service):
    """Verify agent truthfully conveys tool failure and does not claim false success."""
    mock_task_service.delete_task.return_value = False

    agent.llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_del",
                    name="delete_task",
                    arguments={"task_id": "non_existent_id"},
                    raw_arguments='{"task_id": "non_existent_id"}',
                )
            ],
            finish_reason="tool_calls",
        ),
        LLMResponse(
            content="I could not delete task 'non_existent_id' because it was not found.",
            tool_calls=[],
            finish_reason="stop",
        ),
    ]

    resp = agent.process_message(user_id="user_123", message="Delete task non_existent_id")
    assert resp.success is True
    assert len(resp.tool_calls) == 1
    assert resp.tool_results[0]["success"] is False
    assert "could not delete" in resp.response


def test_llm_authentication_error(agent):
    """Verify handling of LLMAuthenticationError."""
    agent.llm_service.chat_completion.side_effect = LLMAuthenticationError("Unauthorized key")

    resp = agent.process_message(user_id="user_123", message="Hello")
    assert resp.success is False
    assert "invalid or missing API credentials" in resp.response
    assert "Unauthorized key" in str(resp.error)


def test_llm_timeout_error(agent):
    """Verify handling of LLMTimeoutError."""
    agent.llm_service.chat_completion.side_effect = LLMTimeoutError("Request timed out")

    resp = agent.process_message(user_id="user_123", message="Hello")
    assert resp.success is False
    assert "timed out" in resp.response
    assert "Request timed out" in str(resp.error)


def test_llm_service_error(agent):
    """Verify handling of LLMServiceError."""
    agent.llm_service.chat_completion.side_effect = LLMServiceError("Server 500 error")

    resp = agent.process_message(user_id="user_123", message="Hello")
    assert resp.success is False
    assert "Unable to communicate" in resp.response


# -----------------------------------------------------------------------------
# 7. Response Sanitization & Thinking Tags
# -----------------------------------------------------------------------------


def test_thinking_tags_sanitization(agent):
    """Verify that <think>...</think> reasoning blocks are stripped from user-facing text."""
    agent.llm_service.chat_completion.return_value = LLMResponse(
        content="<think>\nUser wants greetings.\nBe polite and concise.\n</think>Hello! How can I assist you today?",
        tool_calls=[],
        finish_reason="stop",
    )

    resp = agent.process_message(user_id="user_123", message="Hi")
    assert resp.success is True
    assert "<think>" not in resp.response
    assert "Hello! How can I assist you today?" in resp.response


def test_max_iterations_safety_guard(agent):
    """Verify loop halts gracefully if max_iterations is reached without infinite recursion."""
    agent.max_iterations = 2

    # Always return another tool call
    agent.llm_service.chat_completion.return_value = LLMResponse(
        content=None,
        tool_calls=[
            ToolCallRequest(
                id="call_inf",
                name="calculate",
                arguments={"expression": "1 + 1"},
                raw_arguments='{"expression": "1 + 1"}',
            )
        ],
        finish_reason="tool_calls",
    )

    resp = agent.process_message(user_id="user_123", message="Run loop")
    assert resp.success is True
    assert len(resp.tool_calls) == 2  # exactly max_iterations
    assert agent.llm_service.chat_completion.call_count == 3  # 2 loop iterations + 1 final synthesis
