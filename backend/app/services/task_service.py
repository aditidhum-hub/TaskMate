"""User-scoped Firestore Task Service for TaskMate."""

import logging
from typing import Any

from backend.app.models.task import (
    TaskCreate,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
    generate_iso_timestamp,
)
from backend.app.services.firebase import get_firestore_client

logger = logging.getLogger(__name__)


class TaskService:
    """Service handling CRUD operations for user tasks in Cloud Firestore.

    All operations are strictly partitioned under `users/{user_id}/tasks/{task_id}`
    guaranteeing multi-tenant isolation and security.
    """

    def __init__(self, db: Any = None) -> None:
        """Initialize TaskService with an optional Firestore client.

        Args:
            db: Optional Firestore client instance. If None, resolves via
                `get_firestore_client()`.
        """
        self._db = db

    @property
    def db(self) -> Any:
        """Return the active Firestore database client."""
        if self._db is None:
            self._db = get_firestore_client()
        if self._db is None:
            raise RuntimeError(
                "Firestore database client is unavailable. Ensure Firebase Admin SDK is initialized."
            )
        return self._db

    def _validate_user_id(self, user_id: str) -> str:
        """Validate and normalize user_id."""
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("A valid, non-empty user_id is required.")
        return user_id.strip()

    def _validate_task_id(self, task_id: str) -> str:
        """Validate and normalize task_id."""
        if not task_id or not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("A valid, non-empty task_id is required.")
        return task_id.strip()

    def _get_tasks_collection(self, user_id: str) -> Any:
        """Get the user-isolated Firestore tasks collection reference."""
        valid_uid = self._validate_user_id(user_id)
        return self.db.collection("users").document(valid_uid).collection("tasks")

    def create_task(
        self,
        user_id: str,
        task_data: TaskCreate | dict[str, Any],
    ) -> TaskResponse:
        """Create a new task under users/{user_id}/tasks/{task_id}.

        Args:
            user_id: Authenticated user Firebase UID.
            task_data: Validated TaskCreate model or raw dictionary.

        Returns:
            TaskResponse: The created task with generated ID and timestamps.
        """
        valid_uid = self._validate_user_id(user_id)
        if isinstance(task_data, dict):
            task_create = TaskCreate(**task_data)
        elif isinstance(task_data, TaskCreate):
            task_create = task_data
        else:
            raise TypeError("task_data must be a TaskCreate instance or dict.")

        now = generate_iso_timestamp()
        tasks_ref = self._get_tasks_collection(valid_uid)
        doc_ref = tasks_ref.document()
        task_id = doc_ref.id

        data = task_create.model_dump()
        # Convert enum instances to their string values
        for key, value in data.items():
            if hasattr(value, "value"):
                data[key] = value.value

        payload = {
            "id": task_id,
            "user_id": valid_uid,
            **data,
            "created_at": now,
            "updated_at": now,
        }

        doc_ref.set(payload)
        logger.info("Task created successfully [task_id=%s, user_id=%s]", task_id, valid_uid)
        return TaskResponse(**payload)

    def list_tasks(
        self,
        user_id: str,
        status: str | TaskStatus | None = None,
        priority: str | TaskPriority | None = None,
    ) -> list[TaskResponse]:
        """List tasks owned by user_id with optional status and priority filters.

        Args:
            user_id: Authenticated user Firebase UID.
            status: Optional filter by task status.
            priority: Optional filter by task priority.

        Returns:
            list[TaskResponse]: Filtered list of user tasks.
        """
        tasks_ref = self._get_tasks_collection(user_id)
        query = tasks_ref

        if status is not None:
            status_val = status.value if hasattr(status, "value") else str(status)
            query = query.where("status", "==", status_val)

        if priority is not None:
            priority_val = priority.value if hasattr(priority, "value") else str(priority)
            query = query.where("priority", "==", priority_val)

        docs = query.stream()
        results: list[TaskResponse] = []
        for doc in docs:
            data = doc.to_dict() or {}
            data.setdefault("id", doc.id)
            data.setdefault("user_id", user_id)
            results.append(TaskResponse(**data))

        return results

    def get_task(self, user_id: str, task_id: str) -> TaskResponse | None:
        """Retrieve a specific task document by ID for the given user.

        Args:
            user_id: Authenticated user Firebase UID.
            task_id: Task document ID.

        Returns:
            TaskResponse if found, None if the task does not exist.
        """
        valid_tid = self._validate_task_id(task_id)
        doc_ref = self._get_tasks_collection(user_id).document(valid_tid)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        data = doc.to_dict() or {}
        data.setdefault("id", doc.id)
        data.setdefault("user_id", user_id)
        return TaskResponse(**data)

    def update_task(
        self,
        user_id: str,
        task_id: str,
        update_data: TaskUpdate | dict[str, Any],
    ) -> TaskResponse | None:
        """Update fields of an existing task.

        Args:
            user_id: Authenticated user Firebase UID.
            task_id: Task document ID.
            update_data: TaskUpdate model or dictionary of fields to update.

        Returns:
            TaskResponse with updated values, or None if task not found.
        """
        valid_tid = self._validate_task_id(task_id)

        if isinstance(update_data, dict):
            update_obj = TaskUpdate(**update_data)
        elif isinstance(update_data, TaskUpdate):
            update_obj = update_data
        else:
            raise TypeError("update_data must be a TaskUpdate instance or dict.")

        update_dict = update_obj.model_dump(exclude_unset=True)
        doc_ref = self._get_tasks_collection(user_id).document(valid_tid)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        current_data = doc.to_dict() or {}
        if not update_dict:
            current_data.setdefault("id", doc.id)
            current_data.setdefault("user_id", user_id)
            return TaskResponse(**current_data)

        # Convert enum instances to string values
        for key, value in update_dict.items():
            if hasattr(value, "value"):
                update_dict[key] = value.value

        now = generate_iso_timestamp()
        update_dict["updated_at"] = now

        doc_ref.update(update_dict)
        current_data.update(update_dict)
        current_data.setdefault("id", doc.id)
        current_data.setdefault("user_id", user_id)

        logger.info("Task updated successfully [task_id=%s, user_id=%s]", valid_tid, user_id)
        return TaskResponse(**current_data)

    def complete_task(self, user_id: str, task_id: str) -> TaskResponse | None:
        """Mark a task as completed.

        Args:
            user_id: Authenticated user Firebase UID.
            task_id: Task document ID.

        Returns:
            TaskResponse with status='completed', or None if not found.
        """
        return self.update_task(
            user_id=user_id,
            task_id=task_id,
            update_data=TaskUpdate(status=TaskStatus.COMPLETED),
        )

    def delete_task(self, user_id: str, task_id: str) -> bool:
        """Delete an existing task document.

        Args:
            user_id: Authenticated user Firebase UID.
            task_id: Task document ID.

        Returns:
            bool: True if deleted, False if task did not exist.
        """
        valid_tid = self._validate_task_id(task_id)
        doc_ref = self._get_tasks_collection(user_id).document(valid_tid)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        doc_ref.delete()
        logger.info("Task deleted successfully [task_id=%s, user_id=%s]", valid_tid, user_id)
        return True
