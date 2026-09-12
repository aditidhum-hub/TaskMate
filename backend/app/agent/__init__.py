"""TaskMate Agent module: schemas, tool registry, and LLM orchestration."""

from backend.app.agent.schemas import (
    ALL_TOOL_SCHEMAS,
    CALCULATE_SCHEMA,
    COMPLETE_TASK_SCHEMA,
    CREATE_TASK_SCHEMA,
    DELETE_TASK_SCHEMA,
    GET_DATE_TIME_SCHEMA,
    GET_TASK_SCHEMA,
    LIST_TASKS_SCHEMA,
    TASK_TOOL_SCHEMAS,
    UPDATE_TASK_SCHEMA,
    UTILITY_TOOL_SCHEMAS,
)
from backend.app.agent.tool_registry import ToolRegistry

__all__ = [
    "ALL_TOOL_SCHEMAS",
    "CALCULATE_SCHEMA",
    "COMPLETE_TASK_SCHEMA",
    "CREATE_TASK_SCHEMA",
    "DELETE_TASK_SCHEMA",
    "GET_DATE_TIME_SCHEMA",
    "GET_TASK_SCHEMA",
    "LIST_TASKS_SCHEMA",
    "TASK_TOOL_SCHEMAS",
    "UPDATE_TASK_SCHEMA",
    "UTILITY_TOOL_SCHEMAS",
    "ToolRegistry",
]
