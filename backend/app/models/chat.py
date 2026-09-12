"""Pydantic schemas for the /api/chat endpoint."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    """Incoming request schema for the /api/chat conversational endpoint."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Natural language message or task instruction from the user.",
    )
    message_history: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional previous conversation history for multi-turn context.",
    )

    @field_validator("message")
    @classmethod
    def validate_message_non_empty(cls, v: str) -> str:
        """Ensure message is not empty or solely whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or solely whitespace.")
        return stripped


class ChatResponse(BaseModel):
    """Outgoing response schema for the /api/chat conversational endpoint."""

    model_config = ConfigDict(from_attributes=True)

    response: str = Field(
        ...,
        description="Synthesized natural language response from the agent.",
    )
    tool_used: str | None = Field(
        default=None,
        description="Name of primary tool invoked during turn, if any.",
    )
    created_task: dict[str, Any] | None = Field(
        default=None,
        description="Details of task created if create_task was executed.",
    )
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Audit trace of tools called by the agent.",
    )
    tool_results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Raw observations received from executed tools.",
    )
    messages: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Updated conversation history including user, assistant, and tool turns.",
    )
    success: bool = Field(
        default=True,
        description="Whether the conversational turn succeeded.",
    )
