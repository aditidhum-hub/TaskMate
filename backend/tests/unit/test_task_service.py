"""Unit tests for Pydantic Task models and Firestore TaskService."""

import uuid
from typing import Any

import pytest
from pydantic import ValidationError

from backend.app.models.task import (
    TaskCreate,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
    generate_iso_timestamp,
)
from backend.app.services.task_service import TaskService

# ---------------------------------------------------------------------------
# In-Memory Firestore Mock for Realistic, Fast Offline Unit Testing
# ---------------------------------------------------------------------------


class MockDocSnapshot:
    """Mock document snapshot mirroring google.cloud.firestore.DocumentSnapshot."""

    def __init__(self, doc_id: str, data: dict[str, Any] | None) -> None:
        self.id = doc_id
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict[str, Any] | None:
        if self._data is None:
            return None
        return dict(self._data)


class MockDocRef:
    """Mock document reference mirroring google.cloud.firestore.DocumentReference."""

    def __init__(self, collection: "MockCollectionRef", doc_id: str) -> None:
        self.collection = collection
        self.id = doc_id

    def get(self) -> MockDocSnapshot:
        store = self.collection.database.store
        data = store.get(self.collection.path, {}).get(self.id)
        return MockDocSnapshot(self.id, data)

    def set(self, payload: dict[str, Any]) -> None:
        store = self.collection.database.store
        if self.collection.path not in store:
            store[self.collection.path] = {}
        store[self.collection.path][self.id] = dict(payload)

    def update(self, payload: dict[str, Any]) -> None:
        store = self.collection.database.store
        target = store.get(self.collection.path, {}).get(self.id)
        if target is None:
            raise KeyError(f"Document {self.id} does not exist.")
        target.update(payload)

    def delete(self) -> None:
        store = self.collection.database.store
        if self.collection.path in store and self.id in store[self.collection.path]:
            del store[self.collection.path][self.id]


class MockQuery:
    """Mock query for where() filtering."""

    def __init__(self, collection: "MockCollectionRef", filters: list[tuple[str, str, Any]]) -> None:
        self.collection = collection
        self.filters = filters

    def where(self, field: str, op: str, value: Any) -> "MockQuery":
        new_filters = list(self.filters)
        new_filters.append((field, op, value))
        return MockQuery(self.collection, new_filters)

    def stream(self):
        store = self.collection.database.store
        docs_dict = store.get(self.collection.path, {})
        for doc_id, data in list(docs_dict.items()):
            match = True
            for field, op, val in self.filters:
                if op == "==" and data.get(field) != val:
                    match = False
                    break
            if match:
                yield MockDocSnapshot(doc_id, data)


class MockCollectionRef:
    """Mock collection reference mirroring google.cloud.firestore.CollectionReference."""

    def __init__(self, database: "MockFirestore", path: str) -> None:
        self.database = database
        self.path = path

    def document(self, doc_id: str | None = None) -> MockDocRef:
        if doc_id is None:
            doc_id = f"mock-doc-{uuid.uuid4().hex[:8]}"
        return MockDocRef(self, doc_id)

    def where(self, field: str, op: str, value: Any) -> MockQuery:
        return MockQuery(self, [(field, op, value)])

    def stream(self):
        return MockQuery(self, []).stream()


class MockUserDocRef:
    """Mock intermediate reference for `users/{user_id}`."""

    def __init__(self, database: "MockFirestore", user_id: str) -> None:
        self.database = database
        self.user_id = user_id

    def collection(self, name: str) -> MockCollectionRef:
        if name != "tasks":
            raise ValueError(f"Unexpected subcollection {name}")
        return MockCollectionRef(self.database, f"users/{self.user_id}/tasks")


class MockFirestore:
    """In-memory mock representing the Firestore client root."""

    def __init__(self) -> None:
        # Structure: { "users/<user_id>/tasks": { "<task_id>": { ...doc data... } } }
        self.store: dict[str, dict[str, dict[str, Any]]] = {}

    def collection(self, name: str) -> Any:
        if name != "users":
            raise ValueError(f"Top-level collection must be 'users', got {name}")

        class UserCollectionSelector:
            def __init__(self, parent: "MockFirestore") -> None:
                self.parent = parent

            def document(self, user_id: str) -> MockUserDocRef:
                return MockUserDocRef(self.parent, user_id)

        return UserCollectionSelector(self)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db() -> MockFirestore:
    """Provide a fresh in-memory Firestore client for each test."""
    return MockFirestore()


@pytest.fixture
def task_service(mock_db: MockFirestore) -> TaskService:
    """Provide a TaskService instance configured with the in-memory mock."""
    return TaskService(db=mock_db)


# ---------------------------------------------------------------------------
# Model Validation Tests
# ---------------------------------------------------------------------------


def test_task_create_valid_defaults():
    """Verify TaskCreate accepts a valid title and applies default values."""
    task = TaskCreate(title="Study Python")
    assert task.title == "Study Python"
    assert task.priority == TaskPriority.MEDIUM
    assert task.status == TaskStatus.PENDING
    assert task.description is None
    assert task.due_date is None
    assert task.category is None


def test_task_create_custom_fields():
    """Verify TaskCreate correctly sets all explicit fields."""
    task = TaskCreate(
        title="Deploy Backend",
        description="Deploy FastAPI to Cloud Run",
        due_date="2026-09-15",
        priority=TaskPriority.HIGH,
        status=TaskStatus.IN_PROGRESS,
        category="DevOps",
    )
    assert task.title == "Deploy Backend"
    assert task.description == "Deploy FastAPI to Cloud Run"
    assert task.due_date == "2026-09-15"
    assert task.priority == TaskPriority.HIGH
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.category == "DevOps"


def test_task_create_strips_title_whitespace():
    """Verify title with surrounding whitespace is cleanly stripped."""
    task = TaskCreate(title="   Clean Title   ")
    assert task.title == "Clean Title"


def test_task_create_rejects_empty_or_whitespace_title():
    """Verify empty or whitespace-only titles raise validation errors."""
    with pytest.raises(ValidationError):
        TaskCreate(title="")
    with pytest.raises(ValidationError):
        TaskCreate(title="   ")


def test_task_create_rejects_title_exceeding_max_length():
    """Verify titles longer than 200 characters are rejected."""
    long_title = "A" * 201
    with pytest.raises(ValidationError):
        TaskCreate(title=long_title)


def test_task_update_validation():
    """Verify TaskUpdate validates non-empty title if provided."""
    update = TaskUpdate(title="New Valid Title")
    assert update.title == "New Valid Title"

    with pytest.raises(ValidationError):
        TaskUpdate(title="   ")


def test_task_response_fields():
    """Verify TaskResponse requires id, user_id, timestamps, and title."""
    now = generate_iso_timestamp()
    resp = TaskResponse(
        id="task-123",
        user_id="user-abc",
        title="Test Task",
        priority=TaskPriority.LOW,
        status=TaskStatus.PENDING,
        created_at=now,
        updated_at=now,
    )
    assert resp.id == "task-123"
    assert resp.user_id == "user-abc"
    assert resp.title == "Test Task"
    assert resp.priority == TaskPriority.LOW
    assert resp.status == TaskStatus.PENDING


# ---------------------------------------------------------------------------
# TaskService CRUD Tests
# ---------------------------------------------------------------------------


def test_create_task_success(task_service: TaskService):
    """Verify task creation stores document in user path and returns TaskResponse."""
    user_id = "user_123"
    task_input = TaskCreate(title="Finish Assignment", priority=TaskPriority.HIGH)

    created = task_service.create_task(user_id=user_id, task_data=task_input)

    assert isinstance(created, TaskResponse)
    assert created.user_id == user_id
    assert created.title == "Finish Assignment"
    assert created.priority == TaskPriority.HIGH
    assert created.status == TaskStatus.PENDING
    assert created.id.startswith("mock-doc-")
    assert created.created_at is not None
    assert created.updated_at is not None


def test_create_task_from_dict(task_service: TaskService):
    """Verify task creation works when passing raw dictionary input."""
    user_id = "user_123"
    created = task_service.create_task(
        user_id=user_id,
        task_data={"title": "From Dict", "description": "Notes here"},
    )
    assert created.title == "From Dict"
    assert created.description == "Notes here"


def test_list_tasks_empty(task_service: TaskService):
    """Verify listing tasks for a user with no tasks returns empty list."""
    tasks = task_service.list_tasks(user_id="user_empty")
    assert tasks == []


def test_list_tasks_unfiltered(task_service: TaskService):
    """Verify list_tasks returns all tasks for the user."""
    user_id = "user_456"
    task_service.create_task(user_id, TaskCreate(title="Task 1"))
    task_service.create_task(user_id, TaskCreate(title="Task 2"))

    tasks = task_service.list_tasks(user_id)
    assert len(tasks) == 2
    titles = {t.title for t in tasks}
    assert titles == {"Task 1", "Task 2"}


def test_list_tasks_filter_by_status(task_service: TaskService):
    """Verify list_tasks filters by status."""
    user_id = "user_456"
    t1 = task_service.create_task(user_id, TaskCreate(title="Pending Task"))
    t2 = task_service.create_task(user_id, TaskCreate(title="Completed Task"))
    task_service.complete_task(user_id, t2.id)

    pending_tasks = task_service.list_tasks(user_id, status=TaskStatus.PENDING)
    assert len(pending_tasks) == 1
    assert pending_tasks[0].id == t1.id

    completed_tasks = task_service.list_tasks(user_id, status="completed")
    assert len(completed_tasks) == 1
    assert completed_tasks[0].id == t2.id


def test_list_tasks_filter_by_priority(task_service: TaskService):
    """Verify list_tasks filters by priority."""
    user_id = "user_456"
    t_high = task_service.create_task(user_id, TaskCreate(title="Urgent", priority=TaskPriority.HIGH))
    task_service.create_task(user_id, TaskCreate(title="Normal", priority=TaskPriority.MEDIUM))

    high_tasks = task_service.list_tasks(user_id, priority=TaskPriority.HIGH)
    assert len(high_tasks) == 1
    assert high_tasks[0].id == t_high.id


def test_get_task_success(task_service: TaskService):
    """Verify get_task retrieves the created task."""
    user_id = "user_789"
    created = task_service.create_task(user_id, TaskCreate(title="Target Task"))

    fetched = task_service.get_task(user_id, created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == "Target Task"
    assert fetched.user_id == user_id


def test_get_task_not_found(task_service: TaskService):
    """Verify get_task returns None when task does not exist."""
    result = task_service.get_task("user_789", "non_existent_id")
    assert result is None


def test_update_task_success(task_service: TaskService):
    """Verify updating fields modifies document and updates timestamp."""
    user_id = "user_update"
    created = task_service.create_task(user_id, TaskCreate(title="Initial Title"))

    updated = task_service.update_task(
        user_id=user_id,
        task_id=created.id,
        update_data=TaskUpdate(
            title="Updated Title",
            priority=TaskPriority.HIGH,
            description="Added description",
        ),
    )

    assert updated is not None
    assert updated.title == "Updated Title"
    assert updated.priority == TaskPriority.HIGH
    assert updated.description == "Added description"
    assert updated.updated_at >= created.updated_at


def test_update_task_not_found(task_service: TaskService):
    """Verify updating nonexistent task returns None."""
    result = task_service.update_task(
        user_id="user_update",
        task_id="no_such_task",
        update_data=TaskUpdate(title="Does Not Matter"),
    )
    assert result is None


def test_update_task_empty_dict(task_service: TaskService):
    """Verify updating with empty dict returns current task unchanged."""
    user_id = "user_update"
    created = task_service.create_task(user_id, TaskCreate(title="Stable Title"))

    result = task_service.update_task(user_id=user_id, task_id=created.id, update_data={})
    assert result is not None
    assert result.title == "Stable Title"


def test_complete_task_success(task_service: TaskService):
    """Verify complete_task sets status to completed."""
    user_id = "user_complete"
    created = task_service.create_task(user_id, TaskCreate(title="Do Laundry"))
    assert created.status == TaskStatus.PENDING

    completed = task_service.complete_task(user_id, created.id)
    assert completed is not None
    assert completed.status == TaskStatus.COMPLETED


def test_delete_task_success(task_service: TaskService):
    """Verify delete_task removes the document and returns True."""
    user_id = "user_delete"
    created = task_service.create_task(user_id, TaskCreate(title="Delete Me"))

    deleted = task_service.delete_task(user_id, created.id)
    assert deleted is True

    # Verify task is no longer found
    assert task_service.get_task(user_id, created.id) is None


def test_delete_task_not_found(task_service: TaskService):
    """Verify delete_task returns False if task did not exist."""
    deleted = task_service.delete_task("user_delete", "missing_task_id")
    assert deleted is False


# ---------------------------------------------------------------------------
# Tenant Isolation & Security Boundary Tests
# ---------------------------------------------------------------------------


def test_tenant_isolation_cross_user_access(task_service: TaskService):
    """Security test: User A must never access, list, update, or delete User B's task."""
    user_a = "user_alice_111"
    user_b = "user_bob_222"

    # Alice creates a task
    alice_task = task_service.create_task(user_a, TaskCreate(title="Alice Private Task"))

    # Bob lists tasks - should see 0 tasks
    bob_tasks = task_service.list_tasks(user_b)
    assert len(bob_tasks) == 0

    # Bob attempts to get Alice's task by ID
    bob_fetched = task_service.get_task(user_b, alice_task.id)
    assert bob_fetched is None

    # Bob attempts to update Alice's task
    bob_update = task_service.update_task(
        user_b,
        alice_task.id,
        TaskUpdate(title="Bob Hack"),
    )
    assert bob_update is None

    # Alice's task title remains unchanged
    alice_check = task_service.get_task(user_a, alice_task.id)
    assert alice_check is not None
    assert alice_check.title == "Alice Private Task"

    # Bob attempts to delete Alice's task
    bob_delete = task_service.delete_task(user_b, alice_task.id)
    assert bob_delete is False

    # Alice's task still exists
    assert task_service.get_task(user_a, alice_task.id) is not None


def test_invalid_user_id_raises_value_error(task_service: TaskService):
    """Verify that empty or whitespace user_id raises ValueError."""
    with pytest.raises(ValueError, match="A valid, non-empty user_id is required"):
        task_service.create_task("", TaskCreate(title="Title"))

    with pytest.raises(ValueError, match="A valid, non-empty user_id is required"):
        task_service.list_tasks("   ")

    with pytest.raises(ValueError, match="A valid, non-empty user_id is required"):
        task_service.get_task(None, "task-1")  # type: ignore


def test_invalid_task_id_raises_value_error(task_service: TaskService):
    """Verify that empty or whitespace task_id raises ValueError."""
    with pytest.raises(ValueError, match="A valid, non-empty task_id is required"):
        task_service.get_task("user-1", "")

    with pytest.raises(ValueError, match="A valid, non-empty task_id is required"):
        task_service.delete_task("user-1", "   ")


def test_uninitialized_db_raises_runtime_error(monkeypatch):
    """Verify RuntimeError is raised if Firestore client is requested but unconfigured."""
    service = TaskService(db=None)
    # Mock get_firestore_client to return None
    monkeypatch.setattr("backend.app.services.task_service.get_firestore_client", lambda: None)

    with pytest.raises(RuntimeError, match="Firestore database client is unavailable"):
        _ = service.db
