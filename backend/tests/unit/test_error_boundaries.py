"""Unit tests for tool boundary conditions and defensive error handling (Phase 11)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from backend.app.services.task_service import TaskService
from backend.app.tools.calculator import MAX_EXPRESSION_LENGTH, calculate
from backend.app.tools.datetime_tool import resolve_date_time
from backend.app.tools.task_tool import TaskTool

# -----------------------------------------------------------------------------
# 1. Calculator Tool Boundary Conditions
# -----------------------------------------------------------------------------


def test_calculator_division_by_zero():
    """Verify that division by zero raises ZeroDivisionError with informative message."""
    with pytest.raises(ZeroDivisionError, match="Division by zero is undefined"):
        calculate("10 / 0")


def test_calculator_modulo_by_zero():
    """Verify that modulo by zero raises ZeroDivisionError."""
    with pytest.raises(ZeroDivisionError, match="Modulo by zero is undefined"):
        calculate("10 % 0")


def test_calculator_floor_division_by_zero():
    """Verify that floor division by zero raises ZeroDivisionError."""
    with pytest.raises(ZeroDivisionError, match="Division by zero is undefined"):
        calculate("10 // 0")


def test_calculator_zero_raised_to_negative_power():
    """Verify that zero raised to a negative power raises ZeroDivisionError."""
    with pytest.raises(ZeroDivisionError, match="Zero cannot be raised to a negative power"):
        calculate("0 ** -2")


def test_calculator_syntax_errors():
    """Verify that invalid syntax raises ValueError."""
    with pytest.raises(ValueError, match="Invalid arithmetic syntax"):
        calculate("2 + * 3")

    with pytest.raises(ValueError, match="Invalid arithmetic syntax"):
        calculate("((((1 + 2)")


def test_calculator_empty_and_whitespace():
    """Verify that empty or whitespace-only expressions raise ValueError."""
    with pytest.raises(ValueError, match="Expression cannot be empty"):
        calculate("")

    with pytest.raises(ValueError, match="Expression cannot be empty or solely whitespace"):
        calculate("    \n\t  ")


def test_calculator_exceeds_max_length():
    """Verify that expressions exceeding MAX_EXPRESSION_LENGTH raise ValueError."""
    long_expr = "1 + " * (MAX_EXPRESSION_LENGTH // 4 + 10) + "1"
    with pytest.raises(ValueError, match="exceeds maximum allowed length"):
        calculate(long_expr)


def test_calculator_disallowed_variable_lookups():
    """Verify that variable names are rejected."""
    with pytest.raises(ValueError, match="Variable lookups .* are disallowed"):
        calculate("x + 5")

    with pytest.raises(ValueError, match="Variable lookups .* are disallowed"):
        calculate("__builtins__")


def test_calculator_disallowed_functions():
    """Verify that non-whitelisted function calls are rejected."""
    with pytest.raises(ValueError, match="Function 'eval' is not allowed"):
        calculate("eval('1 + 1')")

    with pytest.raises(ValueError, match="Function 'open' is not allowed"):
        calculate("open('/etc/passwd')")


def test_calculator_disallowed_attribute_access():
    """Verify that attribute lookups are disallowed."""
    with pytest.raises(ValueError, match="Unsupported syntax construct: Attribute|Direct function calls only"):
        calculate("(1).__class__.__name__")


def test_calculator_unsupported_operators():
    """Verify that bitwise and unsupported syntax operators are rejected."""
    with pytest.raises(ValueError, match="Unsupported unary operator|Unsupported syntax construct"):
        calculate("~5")


def test_calculator_sqrt_negative():
    """Verify that square root of negative numbers raises ValueError."""
    with pytest.raises(ValueError, match="Square root of a negative number is undefined"):
        calculate("sqrt(-4)")


def test_calculator_function_invalid_argument_counts():
    """Verify that functions reject invalid argument counts."""
    with pytest.raises(ValueError, match="sqrt.* takes exactly 1 argument"):
        calculate("sqrt(4, 9)")

    with pytest.raises(ValueError, match="round.* takes 1 or 2 arguments"):
        calculate("round(1, 2, 3)")


def test_calculator_numerical_overflow():
    """Verify that calculations resulting in float overflow raise ValueError."""
    with pytest.raises(ValueError, match="numerical overflow"):
        calculate("10 ** 1000")


# -----------------------------------------------------------------------------
# 2. Date/Time Tool Boundary Conditions
# -----------------------------------------------------------------------------


def test_datetime_unrecognized_queries():
    """Verify that unrecognized date queries return safe fallback with informative relative description."""
    anchor = datetime(2026, 9, 12, 12, 0, 0, tzinfo=timezone.utc)
    result = resolve_date_time("some day far into the future", anchor=anchor)
    assert result["iso_date"] == "2026-09-12"
    assert "Unrecognized date query" in result["relative_description"]


def test_datetime_empty_and_none_queries():
    """Verify that empty, None, or whitespace queries fallback cleanly to anchor time."""
    anchor = datetime(2026, 9, 12, 12, 0, 0, tzinfo=timezone.utc)
    result_none = resolve_date_time(None, anchor=anchor)
    assert result_none["iso_date"] == "2026-09-12"
    assert result_none["relative_description"] == "Today"

    result_empty = resolve_date_time("   ", anchor=anchor)
    assert result_empty["iso_date"] == "2026-09-12"
    assert result_empty["relative_description"] == "Today"


def test_datetime_invalid_calendar_dates():
    """Verify that invalid dates (e.g. Feb 30) fall back gracefully without unhandled exception."""
    anchor = datetime(2026, 9, 12, 12, 0, 0, tzinfo=timezone.utc)
    result = resolve_date_time("2026-02-30", anchor=anchor)
    assert result["iso_date"] == "2026-09-12"
    assert "Unrecognized date query" in result["relative_description"]


# -----------------------------------------------------------------------------
# 3. Task Tool Boundary Conditions & Tenant Isolation
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_task_service():
    """Provide a mock TaskService for boundary condition tests."""
    return MagicMock(spec=TaskService)


def test_task_tool_nonexistent_task_get(mock_task_service):
    """Verify get_task with non-existent ID returns clean error dict."""
    mock_task_service.get_task.return_value = None
    tool = TaskTool(user_id="user_123", task_service=mock_task_service)

    result = tool.get_task(task_id="non_existent_id")
    assert result["success"] is False
    assert "not found" in result["error"].lower()


def test_task_tool_nonexistent_task_update(mock_task_service):
    """Verify update_task with non-existent ID returns clean error dict."""
    mock_task_service.update_task.return_value = None
    tool = TaskTool(user_id="user_123", task_service=mock_task_service)

    result = tool.update_task(task_id="non_existent_id", title="New Title")
    assert result["success"] is False
    assert "not found" in result["error"].lower()


def test_task_tool_nonexistent_task_complete(mock_task_service):
    """Verify complete_task with non-existent ID returns clean error dict."""
    mock_task_service.complete_task.return_value = None
    tool = TaskTool(user_id="user_123", task_service=mock_task_service)

    result = tool.complete_task(task_id="non_existent_id")
    assert result["success"] is False
    assert "not found" in result["error"].lower()


def test_task_tool_nonexistent_task_delete(mock_task_service):
    """Verify delete_task with non-existent ID returns clean error dict."""
    mock_task_service.delete_task.return_value = False
    tool = TaskTool(user_id="user_123", task_service=mock_task_service)

    result = tool.delete_task(task_id="non_existent_id")
    assert result["success"] is False
    assert "not found" in result["error"].lower()


def test_task_tool_empty_task_id_rejection():
    """Verify that empty or whitespace task_id returns error via TaskService validation."""
    real_service = TaskService(db=MagicMock())
    tool = TaskTool(user_id="user_123", task_service=real_service)

    result = tool.get_task(task_id="   ")
    assert result["success"] is False
    assert "task_id" in result["error"].lower()


def test_task_tool_tenant_isolation(mock_task_service):
    """Verify TaskTool enforces the bound user_id and passes it to task_service."""
    mock_task_service.get_task.return_value = None
    tool = TaskTool(user_id="authenticated_user_abc", task_service=mock_task_service)

    tool.get_task(task_id="task_123")
    mock_task_service.get_task.assert_called_once_with("authenticated_user_abc", "task_123")
