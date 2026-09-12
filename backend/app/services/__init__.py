"""TaskMate external services package (Firebase, LLM, Task persistence)."""

from backend.app.services.firebase import (
    get_firebase_app,
    get_firestore_client,
    initialize_firebase,
)
from backend.app.services.llm_service import (
    LLMAuthenticationError,
    LLMInvalidResponseError,
    LLMResponse,
    LLMService,
    LLMServiceError,
    LLMTimeoutError,
    ToolCallRequest,
)
from backend.app.services.task_service import TaskService

__all__ = [
    "LLMAuthenticationError",
    "LLMInvalidResponseError",
    "LLMResponse",
    "LLMService",
    "LLMServiceError",
    "LLMTimeoutError",
    "TaskService",
    "ToolCallRequest",
    "get_firebase_app",
    "get_firestore_client",
    "initialize_firebase",
]
