"""End-to-end integration tests for Phase 10 (Frontend + Backend Integration).

Verifies the four canonical conversational workflows:
1. Creation: "Create a high priority task to study Python tomorrow."
2. Query: "Show my pending tasks."
3. Calculation: "I have 30 chapters and 6 days. How many per day?"
4. Completion: "Mark task 'study Python' as completed."
Along with multi-tenant isolation and authentication enforcement.
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
from backend.app.models.task import (
    TaskCreate,
    TaskPriority,
    TaskStatus,
)
from backend.app.services.llm_service import (
    LLMResponse,
    LLMService,
    ToolCallRequest,
)
from backend.app.services.task_service import TaskService

# ---------------------------------------------------------------------------
# Realistic In-Memory Firestore Mock for Hermetic Integration Testing
# ---------------------------------------------------------------------------


class MockDocSnapshot:
    """Mock snapshot mirroring google.cloud.firestore.DocumentSnapshot."""

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
    """Mock reference mirroring google.cloud.firestore.DocumentReference."""

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

    def __init__(
        self, collection: "MockCollectionRef", filters: list[tuple[str, str, Any]]
    ) -> None:
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
            import uuid

            doc_id = f"mock_task_{uuid.uuid4().hex[:8]}"
        return MockDocRef(self, doc_id)

    def where(self, field: str, op: str, value: Any) -> MockQuery:
        return MockQuery(self, [(field, op, value)])

    def stream(self):
        return MockQuery(self, []).stream()


class MockUserDocRef:
    """Mock reference for users/{user_id}."""

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
def mock_db():
    """Provide a fresh in-memory Firestore client."""
    return MockFirestore()


@pytest.fixture
def task_service(mock_db):
    """Provide a real TaskService wired to the in-memory MockFirestore."""
    return TaskService(db=mock_db)


@pytest.fixture
def mock_llm_service():
    """Provide a mock LLMService for deterministic agent completions."""
    service = MagicMock(spec=LLMService)
    return service


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Canonical Verification Scenarios
# ---------------------------------------------------------------------------


def test_scenario_1_creation_flow(client, mock_db, task_service, mock_llm_service):
    """Scenario 1: Creation.

    Prompt: "Create a high priority task to study Python tomorrow."
    Verifies:
    - Agent resolves relative date 'tomorrow' via get_date_time tool.
    - Agent executes create_task with correct title, high priority, and resolved date.
    - Real TaskService persists the task into Cloud Firestore mock.
    - API returns HTTP 200 with created_task payload and truthful synthesis.
    """
    test_user = "user_creation_e2e"

    # Turn 1: LLM decides to resolve date 'tomorrow'
    # Turn 2: LLM receives date observation and calls create_task
    # Turn 3: LLM observes task creation and synthesizes final response
    mock_llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_date_1",
                    name="get_date_time",
                    arguments={"query": "tomorrow"},
                    raw_arguments='{"query": "tomorrow"}',
                )
            ],
        ),
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_create_1",
                    name="create_task",
                    arguments={
                        "title": "Study Python",
                        "priority": "high",
                        "due_date": "2026-09-13",
                    },
                    raw_arguments='{"title": "Study Python", "priority": "high", "due_date": "2026-09-13"}',
                )
            ],
        ),
        LLMResponse(
            content="I've scheduled a high-priority task 'Study Python' for tomorrow (2026-09-13).",
            tool_calls=[],
        ),
    ]

    agent = TaskMateAgent(
        llm_service=mock_llm_service,
        tool_registry=ToolRegistry(),
        task_service=task_service,
    )

    app.dependency_overrides[get_agent] = lambda: agent
    app.dependency_overrides[get_current_user] = lambda: test_user

    try:
        response = client.post(
            "/api/chat",
            json={"message": "Create a high priority task to study Python tomorrow."},
            headers={"Authorization": "Bearer valid-firebase-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 1. Verify successful response structure
        assert data["success"] is True
        assert "Study Python" in data["response"]
        assert "2026-09-13" in data["response"]

        # 2. Verify tool invocation trace (date-time tool usage & create-task tool usage)
        assert len(data["tool_calls"]) == 2
        tool_names = [call["name"] for call in data["tool_calls"]]
        assert "get_date_time" in tool_names
        assert "create_task" in tool_names
        assert data["tool_calls"][0]["name"] == "get_date_time"
        assert data["tool_calls"][1]["name"] == "create_task"

        # 3. Verify created_task payload in response
        created_task = data["created_task"]
        assert created_task is not None
        assert created_task["title"] == "Study Python"
        assert created_task["priority"] == "high"
        assert created_task["status"] == "pending"
        assert created_task["due_date"] == "2026-09-13"

        # 4. Verify actual document persistence in Firestore
        persisted_tasks = mock_db.store.get(f"users/{test_user}/tasks", {})
        assert len(persisted_tasks) == 1
        persisted_doc = next(iter(persisted_tasks.values()))
        assert persisted_doc["title"] == "Study Python"
        assert persisted_doc["priority"] == "high"
        assert persisted_doc["status"] == "pending"
        assert persisted_doc["due_date"] == "2026-09-13"

    finally:
        app.dependency_overrides.clear()


def test_scenario_2_query_flow(client, mock_db, task_service, mock_llm_service):
    """Scenario 2: Query.

    Prompt: "Show my pending tasks."
    Verifies:
    - Real TaskService contains pre-seeded pending and completed tasks.
    - Agent calls list_tasks(status="pending").
    - Real TaskService filters and returns only pending items.
    - Truthful response summarizes the returned pending tasks.
    """
    test_user = "user_query_e2e"

    # Pre-seed tasks in Firestore: 2 pending, 1 completed
    task_service.create_task(
        test_user,
        TaskCreate(
            title="Complete Python chapter 1",
            priority=TaskPriority.HIGH,
            due_date="2026-09-13",
        ),
    )
    task_service.create_task(
        test_user,
        TaskCreate(
            title="Review pull request",
            priority=TaskPriority.MEDIUM,
            due_date="2026-09-14",
        ),
    )
    completed_task = task_service.create_task(
        test_user,
        TaskCreate(
            title="Setup development environment",
            priority=TaskPriority.LOW,
            due_date="2026-09-10",
        ),
    )
    task_service.complete_task(test_user, completed_task.id)

    # Turn 1: LLM decides to call list_tasks(status="pending")
    # Turn 2: LLM receives task observation and synthesizes summary
    mock_llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_list_1",
                    name="list_tasks",
                    arguments={"status": "pending"},
                    raw_arguments='{"status": "pending"}',
                )
            ],
        ),
        LLMResponse(
            content="You have 2 pending tasks:\n1. Complete Python chapter 1 (High priority)\n2. Review pull request (Medium priority).",
            tool_calls=[],
        ),
    ]

    agent = TaskMateAgent(
        llm_service=mock_llm_service,
        tool_registry=ToolRegistry(),
        task_service=task_service,
    )

    app.dependency_overrides[get_agent] = lambda: agent
    app.dependency_overrides[get_current_user] = lambda: test_user

    try:
        response = client.post(
            "/api/chat",
            json={"message": "Show my pending tasks."},
            headers={"Authorization": "Bearer valid-firebase-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert data["tool_used"] == "list_tasks"
        assert "Complete Python chapter 1" in data["response"]
        assert "Review pull request" in data["response"]

        # Verify tool observation returned exactly the 2 pending items
        tool_results = data["tool_results"]
        assert len(tool_results) == 1
        assert tool_results[0]["success"] is True
        returned_tasks = tool_results[0]["tasks"]
        assert len(returned_tasks) == 2
        titles = [t["title"] for t in returned_tasks]
        assert "Complete Python chapter 1" in titles
        assert "Review pull request" in titles
        assert "Setup development environment" not in titles

    finally:
        app.dependency_overrides.clear()


def test_scenario_3_calculation_flow(client, task_service, mock_llm_service):
    """Scenario 3: Calculation.

    Prompt: "I have 30 chapters and 6 days. How many per day?"
    Verifies:
    - Agent calls calculate tool with expression '30 / 6'.
    - Safe AST calculator tool evaluates expression to 5.0.
    - Agent synthesizes truthful answer based on the real tool observation.
    """
    test_user = "user_calc_e2e"

    # Turn 1: LLM calls calculator
    # Turn 2: LLM receives result and synthesizes
    mock_llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_calc_1",
                    name="calculate",
                    arguments={"expression": "30 / 6"},
                    raw_arguments='{"expression": "30 / 6"}',
                )
            ],
        ),
        LLMResponse(
            content="You will need to complete 5 chapters per day to finish 30 chapters in 6 days.",
            tool_calls=[],
        ),
    ]

    agent = TaskMateAgent(
        llm_service=mock_llm_service,
        tool_registry=ToolRegistry(),
        task_service=task_service,
    )

    app.dependency_overrides[get_agent] = lambda: agent
    app.dependency_overrides[get_current_user] = lambda: test_user

    try:
        response = client.post(
            "/api/chat",
            json={"message": "I have 30 chapters and 6 days. How many per day?"},
            headers={"Authorization": "Bearer valid-firebase-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert data["tool_used"] == "calculate"
        assert "5" in data["response"]

        # Verify real tool result was 5.0
        tool_results = data["tool_results"]
        assert len(tool_results) == 1
        assert tool_results[0]["success"] is True
        assert tool_results[0]["result"] == 5.0

    finally:
        app.dependency_overrides.clear()


def test_scenario_4_completion_flow(client, mock_db, task_service, mock_llm_service):
    """Scenario 4: Completion.

    Prompt: "Mark task 'study Python' as completed."
    Verifies:
    - Real TaskService contains a pending task 'Study Python'.
    - Agent executes complete_task tool targeting the matching task ID.
    - Real TaskService updates Firestore document status to 'completed'.
    - API returns updated status in response.
    """
    test_user = "user_complete_e2e"

    # Seed pending task
    created = task_service.create_task(
        test_user,
        TaskCreate(
            title="Study Python",
            priority=TaskPriority.HIGH,
            due_date="2026-09-13",
        ),
    )
    task_id = created.id
    assert created.status == TaskStatus.PENDING

    # Turn 1: LLM decides to complete the task
    # Turn 2: LLM receives updated task observation and confirms
    mock_llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_complete_1",
                    name="complete_task",
                    arguments={"task_id": task_id},
                    raw_arguments=f'{{"task_id": "{task_id}"}}',
                )
            ],
        ),
        LLMResponse(
            content=f"Great job! I've marked 'Study Python' (ID: {task_id}) as completed.",
            tool_calls=[],
        ),
    ]

    agent = TaskMateAgent(
        llm_service=mock_llm_service,
        tool_registry=ToolRegistry(),
        task_service=task_service,
    )

    app.dependency_overrides[get_agent] = lambda: agent
    app.dependency_overrides[get_current_user] = lambda: test_user

    try:
        response = client.post(
            "/api/chat",
            json={"message": "Mark task 'study Python' as completed."},
            headers={"Authorization": "Bearer valid-firebase-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["success"] is True
        assert data["tool_used"] == "complete_task"
        assert "completed" in data["response"].lower()

        # Verify Firestore persistence: task status changed to completed
        persisted = task_service.get_task(test_user, task_id)
        assert persisted is not None
        assert persisted.status == TaskStatus.COMPLETED

    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Multi-Tenant Isolation & Authentication Boundary Integration Tests
# ---------------------------------------------------------------------------


def test_e2e_tenant_isolation(client, mock_db, task_service, mock_llm_service):
    """Verify that User B cannot query or access User A's tasks via the conversational API."""
    user_a = "user_alpha"
    user_b = "user_bravo"

    # User A has confidential tasks
    task_service.create_task(
        user_a,
        TaskCreate(
            title="User A Secret Task",
            priority=TaskPriority.HIGH,
        ),
    )

    # User B queries pending tasks
    mock_llm_service.chat_completion.side_effect = [
        LLMResponse(
            content=None,
            tool_calls=[
                ToolCallRequest(
                    id="call_list_b",
                    name="list_tasks",
                    arguments={"status": "pending"},
                    raw_arguments='{"status": "pending"}',
                )
            ],
        ),
        LLMResponse(
            content="You have no pending tasks.",
            tool_calls=[],
        ),
    ]

    agent = TaskMateAgent(
        llm_service=mock_llm_service,
        tool_registry=ToolRegistry(),
        task_service=task_service,
    )

    app.dependency_overrides[get_agent] = lambda: agent
    app.dependency_overrides[get_current_user] = lambda: user_b

    try:
        response = client.post(
            "/api/chat",
            json={"message": "Show my pending tasks."},
            headers={"Authorization": "Bearer token-user-b"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # User B's tool result must be completely empty
        tool_results = data["tool_results"]
        assert len(tool_results) == 1
        assert len(tool_results[0]["tasks"]) == 0
        assert "Secret Task" not in data["response"]

    finally:
        app.dependency_overrides.clear()


def test_e2e_unauthenticated_request_rejected(client):
    """Verify that end-to-end conversational requests without Bearer credentials are rejected with HTTP 401."""
    response = client.post(
        "/api/chat",
        json={"message": "Create a task to study Python."},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Authentication required" in response.json()["detail"]
