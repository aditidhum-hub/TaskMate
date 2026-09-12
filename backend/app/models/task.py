"""Task domain models and schemas for validation and serialization."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskPriority(str, Enum):
    """Allowed priority levels for tasks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    """Allowed status states for tasks."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskBase(BaseModel):
    """Base fields shared across task schemas."""

    title: str = Field(..., min_length=1, max_length=200, description="Task title (1-200 chars)")
    description: str | None = Field(None, max_length=2000, description="Optional notes or details")
    due_date: str | None = Field(None, description="Optional ISO-8601 date string (YYYY-MM-DD or full timestamp)")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority level")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task completion status")
    category: str | None = Field(None, max_length=50, description="Optional category label")

    @field_validator("title")
    @classmethod
    def validate_title_non_empty(cls, v: str) -> str:
        """Ensure title is not merely whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Task title cannot be empty or solely whitespace.")
        return stripped


class TaskCreate(TaskBase):
    """Schema for creating a new task."""



class TaskUpdate(BaseModel):
    """Schema for updating an existing task. All fields are optional."""

    model_config = ConfigDict(extra="ignore")

    title: str | None = Field(None, min_length=1, max_length=200, description="Updated task title")
    description: str | None = Field(None, max_length=2000, description="Updated notes or details")
    due_date: str | None = Field(None, description="Updated due date string")
    priority: TaskPriority | None = Field(None, description="Updated priority level")
    status: TaskStatus | None = Field(None, description="Updated status")
    category: str | None = Field(None, max_length=50, description="Updated category label")

    @field_validator("title")
    @classmethod
    def validate_title_non_empty(cls, v: str | None) -> str | None:
        """Ensure non-null title is not merely whitespace."""
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Task title cannot be empty or solely whitespace.")
            return stripped
        return v


class TaskResponse(TaskBase):
    """Complete task schema returned to callers."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique task identifier")
    user_id: str = Field(..., description="Owner Firebase UID")
    created_at: str = Field(..., description="ISO-8601 creation timestamp")
    updated_at: str = Field(..., description="ISO-8601 last update timestamp")


def generate_iso_timestamp() -> str:
    """Generate a current UTC ISO-8601 timestamp string."""
    return datetime.now(timezone.utc).isoformat()
