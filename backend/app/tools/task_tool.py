"""Agent-facing Task Tool wrapping TaskService with user context and structured responses."""

import logging
from typing import Any

from pydantic import ValidationError

from backend.app.models.task import TaskCreate, TaskPriority, TaskStatus, TaskUpdate
from backend.app.services.task_service import TaskService

logger = logging.getLogger(__name__)


class TaskTool:
    """Agent tool wrapper for user-scoped task operations.

    Ensures that the authenticated user context is securely injected into every
    database operation and formats responses as structured dictionaries suitable
    for LLM observation and decision-making.
    """

    def __init__(self, user_id: str, task_service: TaskService | None = None) -> None:
        """Initialize TaskTool bound to an authenticated user.

        Args:
            user_id: Authenticated user Firebase UID.
            task_service: Optional TaskService instance. Defaults to a new instance.

        Raises:
            ValueError: If user_id is empty or invalid.
        """
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("A valid, non-empty user_id is required to initialize TaskTool.")
        self.user_id = user_id.strip()
        self.task_service = task_service or TaskService()

    def create_task(
        self,
        title: str,
        description: str | None = None,
        due_date: str | None = None,
        priority: str = "medium",
        category: str | None = None,
    ) -> dict[str, Any]:
        """Create a new task for the authenticated user.

        Args:
            title: Task title (required, 1-200 chars).
            description: Optional details or notes.
            due_date: Optional ISO date string.
            priority: Priority level ('low', 'medium', 'high'). Defaults to 'medium'.
            category: Optional category label.

        Returns:
            dict[str, Any]: Structured outcome with 'success', 'task', or 'error'.
        """
        try:
            # Parse priority string to enum if valid
            priority_enum = TaskPriority(priority.lower()) if isinstance(priority, str) else priority
            task_data = TaskCreate(
                title=title,
                description=description,
                due_date=due_date,
                priority=priority_enum,
                category=category,
            )
            created = self.task_service.create_task(self.user_id, task_data)
            return {
                "success": True,
                "task": created.model_dump(),
                "message": f"Task '{created.title}' created successfully with ID '{created.id}'.",
            }
        except (ValueError, TypeError, ValidationError) as err:
            logger.warning("Failed to create task via TaskTool: %s", err)
            return {"success": False, "error": str(err)}

    def list_tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
    ) -> dict[str, Any]:
        """List tasks for the authenticated user with optional filtering.

        Args:
            status: Optional filter by status ('pending', 'in_progress', 'completed').
            priority: Optional filter by priority ('low', 'medium', 'high').

        Returns:
            dict[str, Any]: Structured outcome with 'success', 'tasks', and 'count'.
        """
        try:
            status_filter = TaskStatus(status.lower()) if status else None
            priority_filter = TaskPriority(priority.lower()) if priority else None

            tasks = self.task_service.list_tasks(
                self.user_id,
                status=status_filter,
                priority=priority_filter,
            )
            return {
                "success": True,
                "tasks": [t.model_dump() for t in tasks],
                "count": len(tasks),
            }
        except (ValueError, TypeError) as err:
            logger.warning("Failed to list tasks via TaskTool: %s", err)
            return {"success": False, "error": str(err)}

    def get_task(self, task_id: str) -> dict[str, Any]:
        """Retrieve a specific task by ID for the authenticated user.

        Args:
            task_id: Unique task identifier.

        Returns:
            dict[str, Any]: Structured outcome with 'success' and 'task' or 'error'.
        """
        try:
            task = self.task_service.get_task(self.user_id, task_id)
            if task is None:
                return {
                    "success": False,
                    "error": f"Task with ID '{task_id}' was not found.",
                }
            return {"success": True, "task": task.model_dump()}
        except (ValueError, TypeError) as err:
            logger.warning("Failed to get task via TaskTool: %s", err)
            return {"success": False, "error": str(err)}

    def update_task(
        self,
        task_id: str,
        title: str | None = None,
        description: str | None = None,
        due_date: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Update fields of an existing task owned by the authenticated user.

        Args:
            task_id: Unique task identifier.
            title: Optional updated title.
            description: Optional updated description.
            due_date: Optional updated due date.
            priority: Optional updated priority level.
            status: Optional updated status state.
            category: Optional updated category.

        Returns:
            dict[str, Any]: Structured outcome with 'success', 'task', or 'error'.
        """
        try:
            update_kwargs: dict[str, Any] = {}
            if title is not None:
                update_kwargs["title"] = title
            if description is not None:
                update_kwargs["description"] = description
            if due_date is not None:
                update_kwargs["due_date"] = due_date
            if priority is not None:
                update_kwargs["priority"] = TaskPriority(priority.lower())
            if status is not None:
                update_kwargs["status"] = TaskStatus(status.lower())
            if category is not None:
                update_kwargs["category"] = category

            update_data = TaskUpdate(**update_kwargs)
            updated = self.task_service.update_task(self.user_id, task_id, update_data)
            if updated is None:
                return {
                    "success": False,
                    "error": f"Task with ID '{task_id}' was not found or could not be updated.",
                }
            return {
                "success": True,
                "task": updated.model_dump(),
                "message": f"Task '{updated.title}' updated successfully.",
            }
        except (ValueError, TypeError, ValidationError) as err:
            logger.warning("Failed to update task via TaskTool: %s", err)
            return {"success": False, "error": str(err)}

    def complete_task(self, task_id: str) -> dict[str, Any]:
        """Mark a task as completed for the authenticated user.

        Args:
            task_id: Unique task identifier.

        Returns:
            dict[str, Any]: Structured outcome with 'success', 'task', or 'error'.
        """
        try:
            task = self.task_service.complete_task(self.user_id, task_id)
            if task is None:
                return {
                    "success": False,
                    "error": f"Task with ID '{task_id}' was not found.",
                }
            return {
                "success": True,
                "task": task.model_dump(),
                "message": f"Task '{task.title}' marked as completed.",
            }
        except (ValueError, TypeError) as err:
            logger.warning("Failed to complete task via TaskTool: %s", err)
            return {"success": False, "error": str(err)}

    def delete_task(self, task_id: str) -> dict[str, Any]:
        """Delete an existing task owned by the authenticated user.

        Args:
            task_id: Unique task identifier.

        Returns:
            dict[str, Any]: Structured outcome with 'success', 'task_id', or 'error'.
        """
        try:
            deleted = self.task_service.delete_task(self.user_id, task_id)
            if not deleted:
                return {
                    "success": False,
                    "error": f"Task with ID '{task_id}' was not found.",
                }
            return {
                "success": True,
                "task_id": task_id,
                "message": f"Task '{task_id}' deleted successfully.",
            }
        except (ValueError, TypeError) as err:
            logger.warning("Failed to delete task via TaskTool: %s", err)
            return {"success": False, "error": str(err)}

    def execute(self, operation: str, **kwargs: Any) -> dict[str, Any]:
        """Dynamically dispatch a named task operation with keyword arguments.

        Args:
            operation: Name of the operation ('create_task', 'list_tasks', 'get_task',
                       'update_task', 'complete_task', 'delete_task').
            **kwargs: Arguments corresponding to the operation method.

        Returns:
            dict[str, Any]: Structured operation outcome.
        """
        operations = {
            "create_task": self.create_task,
            "list_tasks": self.list_tasks,
            "get_task": self.get_task,
            "update_task": self.update_task,
            "complete_task": self.complete_task,
            "delete_task": self.delete_task,
        }
        handler = operations.get(operation)
        if not handler:
            return {
                "success": False,
                "error": f"Unsupported task operation '{operation}'. Approved operations: {list(operations.keys())}",
            }

        return handler(**kwargs)
