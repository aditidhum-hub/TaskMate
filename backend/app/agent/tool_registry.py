"""Tool registry providing schema discovery, argument validation, and secure execution."""

import json
import logging
from typing import Any

from backend.app.agent.schemas import (
    ALL_TOOL_SCHEMAS,
    TASK_TOOL_SCHEMAS,
    UTILITY_TOOL_SCHEMAS,
)
from backend.app.services.task_service import TaskService
from backend.app.tools.calculator import calculate
from backend.app.tools.datetime_tool import resolve_date_time
from backend.app.tools.task_tool import TaskTool

logger = logging.getLogger(__name__)

# Set of approved tool names
TASK_OPERATIONS = {
    "create_task",
    "list_tasks",
    "get_task",
    "update_task",
    "complete_task",
    "delete_task",
}

UTILITY_OPERATIONS = {
    "calculate",
    "get_date_time",
}

APPROVED_OPERATIONS = TASK_OPERATIONS | UTILITY_OPERATIONS

# Required parameters for validation
REQUIRED_PARAMETERS: dict[str, list[str]] = {
    "create_task": ["title"],
    "list_tasks": [],
    "get_task": ["task_id"],
    "update_task": ["task_id"],
    "complete_task": ["task_id"],
    "delete_task": ["task_id"],
    "calculate": ["expression"],
    "get_date_time": ["query"],
}


class ToolRegistry:
    """Registry managing approved tools, schemas, argument validation, and execution."""

    def __init__(self, task_service: TaskService | None = None) -> None:
        """Initialize ToolRegistry.

        Args:
            task_service: Optional TaskService instance passed down to TaskTool.
        """
        self.task_service = task_service

    @staticmethod
    def get_tool_schemas(include_utilities: bool = True) -> list[dict[str, Any]]:
        """Return the JSON schema definitions for registered tools.

        Args:
            include_utilities: Whether to include calculator and datetime tools.

        Returns:
            list[dict[str, Any]]: List of tool schemas in OpenAI-compatible format.
        """
        if include_utilities:
            return list(ALL_TOOL_SCHEMAS)
        return list(TASK_TOOL_SCHEMAS)

    @staticmethod
    def get_task_tool_schemas() -> list[dict[str, Any]]:
        """Return only the task-specific tool schemas."""
        return list(TASK_TOOL_SCHEMAS)

    @staticmethod
    def get_utility_tool_schemas() -> list[dict[str, Any]]:
        """Return only the utility tool schemas."""
        return list(UTILITY_TOOL_SCHEMAS)

    def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | str,
        user_id: str,
        task_service: TaskService | None = None,
    ) -> dict[str, Any]:
        """Validate and execute an approved tool.

        Security invariants enforced:
        - Authenticated user_id is injected by backend, NEVER trusted from arguments.
        - Any 'user_id' provided in arguments is stripped immediately.
        - Unknown tools or missing required arguments return structured errors without crashing.

        Args:
            tool_name: The name of the tool to execute.
            arguments: Tool arguments as a dictionary or JSON string.
            user_id: The authenticated user's Firebase UID.
            task_service: Optional TaskService override for testing.

        Returns:
            dict[str, Any]: Structured execution outcome.
        """
        if not tool_name or not isinstance(tool_name, str):
            return {
                "success": False,
                "error": "Invalid or missing tool name.",
            }

        cleaned_tool_name = tool_name.strip()
        if cleaned_tool_name not in APPROVED_OPERATIONS:
            return {
                "success": False,
                "error": f"Unsupported tool '{tool_name}'. Approved tools: {sorted(APPROVED_OPERATIONS)}",
            }

        # Validate authenticated user context for task operations
        if cleaned_tool_name in TASK_OPERATIONS and (not user_id or not isinstance(user_id, str) or not user_id.strip()):
            return {
                "success": False,
                "error": "Authentication required: a valid user_id must be provided to execute task operations.",
            }

        # Parse string arguments if received as JSON string from LLM
        if isinstance(arguments, str):
            try:
                parsed_args = json.loads(arguments) if arguments.strip() else {}
                if not isinstance(parsed_args, dict):
                    return {
                        "success": False,
                        "error": f"Tool arguments must be a JSON object, got {type(parsed_args).__name__}.",
                    }
            except json.JSONDecodeError as err:
                return {
                    "success": False,
                    "error": f"Malformed tool arguments JSON: {err}",
                }
        elif isinstance(arguments, dict):
            parsed_args = dict(arguments)
        else:
            return {
                "success": False,
                "error": f"Tool arguments must be a dict or JSON string, got {type(arguments).__name__}.",
            }

        # SECURITY DEFENSE: Strip any user_id passed by the LLM
        if "user_id" in parsed_args:
            logger.warning("LLM attempted to specify 'user_id'; stripping parameter to enforce tenant isolation.")
            parsed_args.pop("user_id", None)

        # Validate required parameters
        required_fields = REQUIRED_PARAMETERS.get(cleaned_tool_name, [])
        for field in required_fields:
            if field not in parsed_args or parsed_args[field] is None:
                return {
                    "success": False,
                    "error": f"Missing required argument '{field}' for tool '{cleaned_tool_name}'.",
                }
            if isinstance(parsed_args[field], str) and not parsed_args[field].strip():
                return {
                    "success": False,
                    "error": f"Required argument '{field}' cannot be empty or whitespace.",
                }

        # Execute approved task operations
        if cleaned_tool_name in TASK_OPERATIONS:
            try:
                service = task_service or self.task_service
                task_tool = TaskTool(user_id=user_id.strip(), task_service=service)
                return task_tool.execute(cleaned_tool_name, **parsed_args)
            except Exception:
                logger.exception("Error executing TaskTool operation '%s'", cleaned_tool_name)
                return {
                    "success": False,
                    "error": "Task execution failed.",
                }

        # Execute utility: calculate
        if cleaned_tool_name == "calculate":
            try:
                result = calculate(str(parsed_args["expression"]))
                return {
                    "success": True,
                    "result": result,
                    "expression": parsed_args["expression"],
                }
            except (ValueError, TypeError, ZeroDivisionError) as err:
                return {
                    "success": False,
                    "error": f"Calculation error: {err}",
                }

        # Execute utility: get_date_time
        if cleaned_tool_name == "get_date_time":
            try:
                result = resolve_date_time(str(parsed_args["query"]))
                return {
                    "success": True,
                    "result": result,
                }
            except (ValueError, TypeError) as err:
                return {
                    "success": False,
                    "error": f"Date/time resolution error: {err}",
                }

        return {
            "success": False,
            "error": f"Unhandled tool '{cleaned_tool_name}'.",
        }
