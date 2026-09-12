"""Unit tests for agent-facing TaskTool."""

import pytest

from backend.app.services.task_service import TaskService
from backend.app.tools.task_tool import TaskTool
from backend.tests.unit.test_task_service import MockFirestore


@pytest.fixture
def mock_db() -> MockFirestore:
    """Fresh in-memory Firestore mock instance."""
    return MockFirestore()


@pytest.fixture
def task_service(mock_db: MockFirestore) -> TaskService:
    """TaskService wired to the in-memory mock."""
    return TaskService(db=mock_db)


@pytest.fixture
def alice_tool(task_service: TaskService) -> TaskTool:
    """TaskTool bound to user 'user_alice'."""
    return TaskTool(user_id="user_alice", task_service=task_service)


@pytest.fixture
def bob_tool(task_service: TaskService) -> TaskTool:
    """TaskTool bound to user 'user_bob'."""
    return TaskTool(user_id="user_bob", task_service=task_service)


# ---------------------------------------------------------------------------
# Initialization & Context Injection Tests
# ---------------------------------------------------------------------------


def test_task_tool_init_valid(task_service: TaskService):
    """Verify TaskTool initializes with a valid user_id."""
    tool = TaskTool(user_id="  user_xyz  ", task_service=task_service)
    assert tool.user_id == "user_xyz"


def test_task_tool_init_invalid(task_service: TaskService):
    """Verify TaskTool rejects empty or whitespace user_id."""
    with pytest.raises(ValueError, match="A valid, non-empty user_id is required"):
        TaskTool(user_id="", task_service=task_service)

    with pytest.raises(ValueError, match="A valid, non-empty user_id is required"):
        TaskTool(user_id="   ", task_service=task_service)


# ---------------------------------------------------------------------------
# Create Task Tests
# ---------------------------------------------------------------------------


def test_create_task_success(alice_tool: TaskTool):
    """Verify create_task returns structured success response with task details."""
    res = alice_tool.create_task(
        title="Write Research Paper",
        description="Literature review section",
        due_date="2026-09-20",
        priority="high",
        category="Academics",
    )
    assert res["success"] is True
    assert "task" in res
    assert res["task"]["title"] == "Write Research Paper"
    assert res["task"]["priority"] == "high"
    assert res["task"]["status"] == "pending"
    assert res["task"]["user_id"] == "user_alice"
    assert "created successfully" in res["message"]


def test_create_task_validation_error(alice_tool: TaskTool):
    """Verify create_task returns structured failure on invalid inputs."""
    # Empty title
    res_empty = alice_tool.create_task(title="   ")
    assert res_empty["success"] is False
    assert "error" in res_empty

    # Invalid priority
    res_priority = alice_tool.create_task(title="Valid Title", priority="ultra-urgent")
    assert res_priority["success"] is False
    assert "error" in res_priority


# ---------------------------------------------------------------------------
# List Tasks Tests
# ---------------------------------------------------------------------------


def test_list_tasks_empty(alice_tool: TaskTool):
    """Verify list_tasks returns empty list and count 0 when no tasks exist."""
    res = alice_tool.list_tasks()
    assert res["success"] is True
    assert res["tasks"] == []
    assert res["count"] == 0


def test_list_tasks_with_filtering(alice_tool: TaskTool):
    """Verify list_tasks filters by status and priority."""
    alice_tool.create_task(title="Task Low", priority="low")
    alice_tool.create_task(title="Task High", priority="high")

    # Filter by priority
    res_high = alice_tool.list_tasks(priority="high")
    assert res_high["success"] is True
    assert res_high["count"] == 1
    assert res_high["tasks"][0]["title"] == "Task High"

    # Complete one task and filter by status
    high_id = res_high["tasks"][0]["id"]
    alice_tool.complete_task(high_id)

    res_completed = alice_tool.list_tasks(status="completed")
    assert res_completed["success"] is True
    assert res_completed["count"] == 1
    assert res_completed["tasks"][0]["id"] == high_id

    res_pending = alice_tool.list_tasks(status="pending")
    assert res_pending["success"] is True
    assert res_pending["count"] == 1
    assert res_pending["tasks"][0]["title"] == "Task Low"


# ---------------------------------------------------------------------------
# Get Task Tests
# ---------------------------------------------------------------------------


def test_get_task_success(alice_tool: TaskTool):
    """Verify get_task retrieves existing task."""
    created = alice_tool.create_task(title="Target Task")
    task_id = created["task"]["id"]

    res = alice_tool.get_task(task_id)
    assert res["success"] is True
    assert res["task"]["id"] == task_id
    assert res["task"]["title"] == "Target Task"


def test_get_task_not_found(alice_tool: TaskTool):
    """Verify get_task returns structured error for nonexistent task."""
    res = alice_tool.get_task("nonexistent-task-id")
    assert res["success"] is False
    assert "not found" in res["error"].lower()


# ---------------------------------------------------------------------------
# Update & Complete Task Tests
# ---------------------------------------------------------------------------


def test_update_task_success(alice_tool: TaskTool):
    """Verify update_task modifies fields."""
    created = alice_tool.create_task(title="Initial Title", priority="low")
    task_id = created["task"]["id"]

    res = alice_tool.update_task(
        task_id=task_id,
        title="Updated Title",
        priority="high",
        description="New description",
    )
    assert res["success"] is True
    assert res["task"]["title"] == "Updated Title"
    assert res["task"]["priority"] == "high"
    assert res["task"]["description"] == "New description"


def test_update_task_not_found(alice_tool: TaskTool):
    """Verify update_task returns structured error if task does not exist."""
    res = alice_tool.update_task("missing-id", title="New Title")
    assert res["success"] is False
    assert "not found" in res["error"].lower()


def test_complete_task_success(alice_tool: TaskTool):
    """Verify complete_task sets status to completed."""
    created = alice_tool.create_task(title="Finish homework")
    task_id = created["task"]["id"]

    res = alice_tool.complete_task(task_id)
    assert res["success"] is True
    assert res["task"]["status"] == "completed"
    assert "marked as completed" in res["message"]


def test_complete_task_not_found(alice_tool: TaskTool):
    """Verify complete_task returns structured error if task does not exist."""
    res = alice_tool.complete_task("missing-id")
    assert res["success"] is False
    assert "not found" in res["error"].lower()


# ---------------------------------------------------------------------------
# Delete Task Tests
# ---------------------------------------------------------------------------


def test_delete_task_success(alice_tool: TaskTool):
    """Verify delete_task removes task."""
    created = alice_tool.create_task(title="Delete Me")
    task_id = created["task"]["id"]

    res = alice_tool.delete_task(task_id)
    assert res["success"] is True
    assert res["task_id"] == task_id
    assert "deleted successfully" in res["message"]

    # Verify task is no longer found
    assert alice_tool.get_task(task_id)["success"] is False


def test_delete_task_not_found(alice_tool: TaskTool):
    """Verify delete_task returns structured error if task does not exist."""
    res = alice_tool.delete_task("missing-id")
    assert res["success"] is False
    assert "not found" in res["error"].lower()


# ---------------------------------------------------------------------------
# Dispatcher (execute) Tests
# ---------------------------------------------------------------------------


def test_execute_dispatcher_valid(alice_tool: TaskTool):
    """Verify dynamic dispatch via execute() method."""
    create_res = alice_tool.execute(
        "create_task",
        title="From Dispatcher",
        priority="high",
    )
    assert create_res["success"] is True
    task_id = create_res["task"]["id"]

    list_res = alice_tool.execute("list_tasks")
    assert list_res["success"] is True
    assert list_res["count"] == 1

    get_res = alice_tool.execute("get_task", task_id=task_id)
    assert get_res["success"] is True
    assert get_res["task"]["title"] == "From Dispatcher"


def test_execute_dispatcher_unknown_operation(alice_tool: TaskTool):
    """Verify execute() returns structured error on unknown operation."""
    res = alice_tool.execute("drop_database")
    assert res["success"] is False
    assert "Unsupported task operation 'drop_database'" in res["error"]


# ---------------------------------------------------------------------------
# Security & Tenant Isolation Tests
# ---------------------------------------------------------------------------


def test_tenant_isolation_via_task_tool(alice_tool: TaskTool, bob_tool: TaskTool):
    """Security test: Bob's TaskTool cannot view or mutate Alice's tasks."""
    # Alice creates a task
    alice_created = alice_tool.create_task(title="Alice Private Task")
    alice_task_id = alice_created["task"]["id"]

    # Bob lists tasks: 0 found
    bob_list = bob_tool.list_tasks()
    assert bob_list["count"] == 0

    # Bob attempts to get Alice's task
    bob_get = bob_tool.get_task(alice_task_id)
    assert bob_get["success"] is False
    assert "not found" in bob_get["error"].lower()

    # Bob attempts to update Alice's task
    bob_update = bob_tool.update_task(alice_task_id, title="Hacked by Bob")
    assert bob_update["success"] is False
    assert "not found" in bob_update["error"].lower()

    # Bob attempts to complete Alice's task
    bob_complete = bob_tool.complete_task(alice_task_id)
    assert bob_complete["success"] is False
    assert "not found" in bob_complete["error"].lower()

    # Bob attempts to delete Alice's task
    bob_delete = bob_tool.delete_task(alice_task_id)
    assert bob_delete["success"] is False
    assert "not found" in bob_delete["error"].lower()

    # Alice's task remains untouched
    alice_check = alice_tool.get_task(alice_task_id)
    assert alice_check["success"] is True
    assert alice_check["task"]["title"] == "Alice Private Task"
    assert alice_check["task"]["status"] == "pending"
