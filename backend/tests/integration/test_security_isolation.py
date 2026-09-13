"""Security & Tenant Isolation Integration Test Suite (Phase 12).

Verifies strict single-user tenant isolation:
1. Cross-User Read Isolation: User A cannot read User B's task.
2. Cross-User Update Isolation: User A cannot update User B's task.
3. Cross-User Delete Isolation: User A cannot delete User B's task.
4. Cross-User List Isolation: User A's queries never return User B's tasks.
5. Parameter Forgery Defense: Client or LLM supplying foreign user_id cannot escape authenticated user context.
6. Cryptographic Token Enforcement: Missing, forged, or malformed authentication tokens are rejected with 401.
7. CORS Origin Enforcement: Unapproved origins are rejected by CORS headers.
"""

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from backend.app.agent.agent import TaskMateAgent
from backend.app.agent.tool_registry import ToolRegistry
from backend.app.api.dependencies import get_current_user
from backend.app.api.routes_chat import get_agent
from backend.app.main import app
from backend.app.models.task import TaskCreate, TaskPriority
from backend.app.services.llm_service import (
    LLMResponse,
    LLMService,
    ToolCallRequest,
)
from backend.app.services.task_service import TaskService

# ---------------------------------------------------------------------------
# In-Memory Hermetic Firestore Mock for Multi-Tenant Testing
# ---------------------------------------------------------------------------


class MockDocSnapshot:
    """Mock Firestore Document Snapshot."""

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
    """Mock Firestore Document Reference."""

    def __init__(self, collection: "MockCollectionRef", doc_id: str) -> None:
        self.collection = collection
        self.id = doc_id

    def set(self, data: dict[str, Any]) -> None:
        self.collection.database.store.setdefault(self.collection.path, {})[self.id] = dict(data)

    def get(self) -> MockDocSnapshot:
        store = self.collection.database.store.get(self.collection.path, {})
        data = store.get(self.id)
        return MockDocSnapshot(self.id, data)

    def update(self, data: dict[str, Any]) -> None:
        store = self.collection.database.store.get(self.collection.path, {})
        if self.id in store:
            store[self.id].update(data)

    def delete(self) -> None:
        store = self.collection.database.store.get(self.collection.path, {})
        store.pop(self.id, None)


class MockQuery:
    """Mock Firestore Query."""

    def __init__(self, collection: "MockCollectionRef", filters: list[tuple[str, str, Any]]) -> None:
        self.collection = collection
        self.filters = filters

    def where(self, field: str, op: str, value: Any) -> "MockQuery":
        return MockQuery(self.collection, self.filters + [(field, op, value)])

    def stream(self):
        store = self.collection.database.store.get(self.collection.path, {})
        for doc_id, data in list(store.items()):
            matches = True
            for field, op, val in self.filters:
                if op == "==" and data.get(field) != val:
                    matches = False
                    break
            if matches:
                yield MockDocSnapshot(doc_id, data)


class MockCollectionRef:
    """Mock Firestore Collection Reference."""

    def __init__(self, database: "MockFirestore", path: str) -> None:
        self.database = database
        self.path = path

    def document(self, doc_id: str | None = None) -> MockDocRef:
        if doc_id is None:
            import uuid

            doc_id = f"task_{uuid.uuid4().hex[:8]}"
        return MockDocRef(self, doc_id)

    def where(self, field: str, op: str, value: Any) -> MockQuery:
        return MockQuery(self, [(field, op, value)])

    def stream(self):
        return MockQuery(self, []).stream()


class MockUserDocRef:
    """Mock Firestore User Document Reference."""

    def __init__(self, database: "MockFirestore", user_id: str) -> None:
        self.database = database
        self.user_id = user_id

    def collection(self, name: str) -> MockCollectionRef:
        if name != "tasks":
            raise ValueError(f"Unexpected subcollection {name}")
        return MockCollectionRef(self.database, f"users/{self.user_id}/tasks")


class MockFirestore:
    """Mock Firestore Root Client."""

    def __init__(self) -> None:
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


@pytest.fixture(autouse=True)
def clean_overrides():
    """Ensure clean dependency overrides per test."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db():
    return MockFirestore()


@pytest.fixture
def task_service(mock_db):
    return TaskService(db=mock_db)


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Tests: Cross-User Isolation
# ---------------------------------------------------------------------------


def test_cross_user_read_isolation(task_service):
    """User B cannot read User A's task directly via task service."""
    # Setup User A's task
    user_a_task = task_service.create_task(
        "user_a",
        TaskCreate(title="User A Secret Task", priority=TaskPriority.HIGH),
    )

    # User B attempts to read User A's task
    read_result = task_service.get_task("user_b", user_a_task.id)
    assert read_result is None, "User B must not be able to retrieve User A's task"


def test_cross_user_update_isolation(task_service):
    """User B cannot update User A's task."""
    user_a_task = task_service.create_task(
        "user_a",
        TaskCreate(title="Original Title", priority=TaskPriority.LOW),
    )

    # User B attempts to modify User A's task
    update_result = task_service.update_task(
        "user_b",
        user_a_task.id,
        {"title": "Compromised Title"},
    )
    assert update_result is None, "User B must not be able to update User A's task"

    # Verify User A's task remains untouched
    intact_task = task_service.get_task("user_a", user_a_task.id)
    assert intact_task is not None
    assert intact_task.title == "Original Title"


def test_cross_user_delete_isolation(task_service):
    """User B cannot delete User A's task."""
    user_a_task = task_service.create_task(
        "user_a",
        TaskCreate(title="User A Critical Task", priority=TaskPriority.HIGH),
    )

    # User B attempts to delete User A's task
    delete_result = task_service.delete_task("user_b", user_a_task.id)
    assert delete_result is False, "User B must not be able to delete User A's task"

    # Verify User A's task still exists
    intact_task = task_service.get_task("user_a", user_a_task.id)
    assert intact_task is not None
    assert intact_task.title == "User A Critical Task"


def test_cross_user_list_isolation(task_service):
    """User queries list_tasks and strictly receives only their own tasks."""
    # User A has 2 tasks
    task_service.create_task("user_a", TaskCreate(title="Task A1"))
    task_service.create_task("user_a", TaskCreate(title="Task A2"))

    # User B has 1 task
    task_service.create_task("user_b", TaskCreate(title="Task B1"))

    # User A listing
    user_a_tasks = task_service.list_tasks("user_a")
    assert len(user_a_tasks) == 2
    assert all(t.user_id == "user_a" for t in user_a_tasks)
    assert not any(t.title == "Task B1" for t in user_a_tasks)

    # User B listing
    user_b_tasks = task_service.list_tasks("user_b")
    assert len(user_b_tasks) == 1
    assert user_b_tasks[0].title == "Task B1"
    assert user_b_tasks[0].user_id == "user_b"


# ---------------------------------------------------------------------------
# Tests: Parameter Forgery & LLM Jailbreak Defense
# ---------------------------------------------------------------------------


def test_llm_parameter_forgery_defense(client, task_service):
    """If LLM or client attempts to pass a foreign user_id in tool arguments, ToolRegistry strips it."""
    mock_llm = MagicMock(spec=LLMService)
    # LLM attempts to forge user_id="victim_user_b"
    turn1 = LLMResponse(
        content=None,
        tool_calls=[
            ToolCallRequest(
                id="call_forged_create",
                name="create_task",
                arguments={
                    "title": "Injected Task",
                    "user_id": "victim_user_b",  # Forged parameter
                },
            )
        ],
    )
    turn2 = LLMResponse(
        content="Task created successfully.",
        tool_calls=[],
    )
    mock_llm.chat_completion.side_effect = [turn1, turn2]

    agent = TaskMateAgent(
        llm_service=mock_llm,
        tool_registry=ToolRegistry(task_service=task_service),
        task_service=task_service,
    )

    app.dependency_overrides[get_agent] = lambda: agent
    app.dependency_overrides[get_current_user] = lambda: "authenticated_user_a"

    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer valid-token"},
        json={"message": "Create task for victim_user_b"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True

    # SECURITY VERIFICATION:
    # 1. The task must NOT exist under victim_user_b
    victim_tasks = task_service.list_tasks("victim_user_b")
    assert len(victim_tasks) == 0, "Forged user_id must NOT write to victim's storage"

    # 2. The task MUST exist strictly under authenticated_user_a
    user_a_tasks = task_service.list_tasks("authenticated_user_a")
    assert len(user_a_tasks) == 1
    assert user_a_tasks[0].title == "Injected Task"
    assert user_a_tasks[0].user_id == "authenticated_user_a"


# ---------------------------------------------------------------------------
# Tests: Token Enforcement & Authentication Boundaries
# ---------------------------------------------------------------------------


def test_missing_auth_token_rejected(client):
    """Missing Authorization header must return HTTP 401."""
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers.get("WWW-Authenticate") == "Bearer"


def test_invalid_auth_scheme_rejected(client):
    """Non-Bearer scheme must return HTTP 401."""
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
        json={"message": "Hello"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers.get("WWW-Authenticate") == "Bearer"


def test_forged_unverified_token_rejected(client):
    """Synthesized or fabricated JWT token must return HTTP 401."""
    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer forged.unsigned.token"},
        json={"message": "Hello"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers.get("WWW-Authenticate") == "Bearer"


# ---------------------------------------------------------------------------
# Tests: CORS Origin Restrictions
# ---------------------------------------------------------------------------


def test_cors_disallowed_origin_rejected(client):
    """Preflight request from an unapproved origin must not receive Access-Control-Allow-Origin."""
    response = client.options(
        "/api/chat",
        headers={
            "Origin": "http://malicious-attacker.site",
            "Access-Control-Request-Method": "POST",
        },
    )
    # When an origin is not in CORS_ORIGINS, FastAPI CORSMiddleware does NOT set Access-Control-Allow-Origin
    assert response.headers.get("access-control-allow-origin") is None
