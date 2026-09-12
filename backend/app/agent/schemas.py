"""Structured tool declaration schemas for Nemotron and OpenAI-compatible tool calling."""

from typing import Any

# Tool definition for creating a new task
CREATE_TASK_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "create_task",
        "description": "Create a new personal task in TaskMate. User identity is securely injected by the backend.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Clear and descriptive task title (required, 1-200 characters).",
                },
                "description": {
                    "type": "string",
                    "description": "Optional notes, details, or context about the task.",
                },
                "due_date": {
                    "type": "string",
                    "description": "Optional due date in ISO-8601 format (e.g., 'YYYY-MM-DD').",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Task priority level. Defaults to 'medium'.",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category label (e.g., 'Work', 'Study', 'Personal').",
                },
            },
            "required": ["title"],
            "additionalProperties": False,
        },
    },
}

# Tool definition for listing tasks
LIST_TASKS_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "list_tasks",
        "description": "List existing tasks for the authenticated user with optional status and priority filters.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed"],
                    "description": "Optional status filter ('pending', 'in_progress', 'completed').",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Optional priority filter ('low', 'medium', 'high').",
                },
            },
            "additionalProperties": False,
        },
    },
}

# Tool definition for retrieving a single task
GET_TASK_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_task",
        "description": "Retrieve details of a specific task by its unique task ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The unique identifier of the task to retrieve.",
                },
            },
            "required": ["task_id"],
            "additionalProperties": False,
        },
    },
}

# Tool definition for updating a task
UPDATE_TASK_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "update_task",
        "description": "Update fields of an existing task owned by the authenticated user.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The unique identifier of the task to update.",
                },
                "title": {
                    "type": "string",
                    "description": "Optional updated task title (1-200 characters).",
                },
                "description": {
                    "type": "string",
                    "description": "Optional updated description notes.",
                },
                "due_date": {
                    "type": "string",
                    "description": "Optional updated due date in ISO-8601 format ('YYYY-MM-DD').",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Optional updated priority level.",
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed"],
                    "description": "Optional updated task status.",
                },
                "category": {
                    "type": "string",
                    "description": "Optional updated category label.",
                },
            },
            "required": ["task_id"],
            "additionalProperties": False,
        },
    },
}

# Tool definition for completing a task
COMPLETE_TASK_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "complete_task",
        "description": "Mark an existing task as completed for the authenticated user.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The unique identifier of the task to mark as completed.",
                },
            },
            "required": ["task_id"],
            "additionalProperties": False,
        },
    },
}

# Tool definition for deleting a task
DELETE_TASK_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "delete_task",
        "description": "Permanently delete an existing task owned by the authenticated user.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "The unique identifier of the task to delete.",
                },
            },
            "required": ["task_id"],
            "additionalProperties": False,
        },
    },
}

# Tool definition for calculator
CALCULATE_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Perform safe arithmetic calculations (e.g., '20 + 5 * 2', 'sqrt(144)', 'round(10 / 3, 2)').",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate.",
                },
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
    },
}

# Tool definition for datetime resolution
GET_DATE_TIME_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_date_time",
        "description": "Resolve real-time calendar and clock queries (e.g., 'today', 'tomorrow', 'next Monday', 'in 5 days').",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The temporal query expression to resolve.",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}

# Approved Task Operations
TASK_TOOL_SCHEMAS: list[dict[str, Any]] = [
    CREATE_TASK_SCHEMA,
    LIST_TASKS_SCHEMA,
    GET_TASK_SCHEMA,
    UPDATE_TASK_SCHEMA,
    COMPLETE_TASK_SCHEMA,
    DELETE_TASK_SCHEMA,
]

# Utility Tools
UTILITY_TOOL_SCHEMAS: list[dict[str, Any]] = [
    CALCULATE_SCHEMA,
    GET_DATE_TIME_SCHEMA,
]

# All approved tools exposed to the LLM agent
ALL_TOOL_SCHEMAS: list[dict[str, Any]] = [
    *TASK_TOOL_SCHEMAS,
    *UTILITY_TOOL_SCHEMAS,
]
