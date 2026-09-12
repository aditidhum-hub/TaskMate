"""Tests for agent loop defensive error handling and truthfulness verification (Phase 11)."""

from unittest.mock import MagicMock

from backend.app.agent.agent import AgentResponse, TaskMateAgent
from backend.app.services.llm_service import (
    LLMAuthenticationError,
    LLMInvalidResponseError,
    LLMResponse,
    LLMService,
    LLMTimeoutError,
    ToolCallRequest,
)


def test_agent_handles_llm_timeout():
    """Verify that an LLM timeout produces a truthful, user-friendly failure response without crashing."""
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.chat_completion.side_effect = LLMTimeoutError("Request to Nemotron timed out after 30s")

    agent = TaskMateAgent(llm_service=mock_llm)
    result: AgentResponse = agent.process_message(user_id="test_user", message="Show my tasks")

    assert result.success is False
    assert "timed out" in result.response.lower()
    assert result.error == "Request to Nemotron timed out after 30s"


def test_agent_handles_llm_auth_error():
    """Verify that an LLM authentication failure produces a clear configuration error response."""
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.chat_completion.side_effect = LLMAuthenticationError("Invalid API key")

    agent = TaskMateAgent(llm_service=mock_llm)
    result: AgentResponse = agent.process_message(user_id="test_user", message="Show my tasks")

    assert result.success is False
    assert "configuration error" in result.response.lower() or "credentials" in result.response.lower()


def test_agent_handles_llm_server_error():
    """Verify that upstream 500/502/503 from provider returns safe communication error."""
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.chat_completion.side_effect = LLMInvalidResponseError("Nemotron API error (HTTP 503)")

    agent = TaskMateAgent(llm_service=mock_llm)
    result: AgentResponse = agent.process_message(user_id="test_user", message="Calculate 5 + 5")

    assert result.success is False
    assert "unable to communicate" in result.response.lower()


def test_agent_truthful_reporting_on_tool_failure():
    """Verify that when a tool execution reports failure, the agent synthesizes that truthfully without claiming success."""
    mock_llm = MagicMock(spec=LLMService)
    # Turn 1: Model requests calculate with division by zero
    turn1_response = LLMResponse(
        content=None,
        tool_calls=[
            ToolCallRequest(
                id="call_div_zero",
                name="calculate",
                arguments={"expression": "100 / 0"},
            )
        ],
    )
    # Turn 2: Model receives tool error observation and explains failure to user truthfully
    turn2_response = LLMResponse(
        content="I cannot perform that calculation because division by zero is undefined.",
        tool_calls=[],
    )
    mock_llm.chat_completion.side_effect = [turn1_response, turn2_response]

    agent = TaskMateAgent(llm_service=mock_llm)
    result: AgentResponse = agent.process_message(user_id="test_user", message="What is 100 divided by 0?")

    assert result.success is True
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0]["name"] == "calculate"
    assert len(result.tool_results) == 1
    assert result.tool_results[0]["success"] is False
    assert "division by zero" in result.tool_results[0]["error"].lower()
    assert "division by zero is undefined" in result.response.lower()


def test_agent_truthful_reporting_on_task_not_found():
    """Verify that when task completion fails because task does not exist, truthfulness is preserved."""
    mock_llm = MagicMock(spec=LLMService)
    turn1 = LLMResponse(
        content=None,
        tool_calls=[
            ToolCallRequest(
                id="call_complete_fake",
                name="complete_task",
                arguments={"task_id": "non_existent_uuid"},
            )
        ],
    )
    turn2 = LLMResponse(
        content="I could not find task 'non_existent_uuid' to mark it as completed.",
        tool_calls=[],
    )
    mock_llm.chat_completion.side_effect = [turn1, turn2]

    # Mock task_service to return None for nonexistent task
    mock_task_service = MagicMock()
    mock_task_service.complete_task.return_value = None

    agent = TaskMateAgent(llm_service=mock_llm, task_service=mock_task_service)
    result = agent.process_message(user_id="test_user", message="Mark task non_existent_uuid as completed")

    assert result.success is True
    assert len(result.tool_results) == 1
    assert result.tool_results[0]["success"] is False
    assert "not found" in result.tool_results[0]["error"].lower()
    assert "could not find" in result.response.lower()


def test_agent_max_iterations_infinite_loop_prevention():
    """Verify that an agent repeatedly requesting tools is bounded at max_iterations (default: 5)."""
    mock_llm = MagicMock(spec=LLMService)
    # Repeatedly return tool requests
    endless_tool_response = LLMResponse(
        content="Still thinking...",
        tool_calls=[
            ToolCallRequest(
                id="call_loop",
                name="get_date_time",
                arguments={"query": "today"},
            )
        ],
    )
    synthesis_response = LLMResponse(
        content="I have gathered the date information after 5 steps.",
        tool_calls=[],
    )
    mock_llm.chat_completion.side_effect = [
        endless_tool_response,
        endless_tool_response,
        endless_tool_response,
        endless_tool_response,
        endless_tool_response,
        synthesis_response,
    ]

    agent = TaskMateAgent(llm_service=mock_llm)
    result = agent.process_message(user_id="test_user", message="Loop query")

    # Bounded to exactly 5 iterations of tool execution
    assert len(result.tool_calls) == 5
    assert result.success is True
    assert "5 steps" in result.response
