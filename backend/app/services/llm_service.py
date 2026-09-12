"""LLM Service connecting to NVIDIA Nemotron via an OpenAI-compatible API interface."""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from backend.app.core.config import Settings, get_settings
from backend.app.services.task_service import TaskService

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------


class LLMServiceError(Exception):
    """Base exception for LLM service failures."""


class LLMAuthenticationError(LLMServiceError):
    """Raised when API key is missing or unauthorized."""


class LLMTimeoutError(LLMServiceError):
    """Raised when the LLM service request times out."""


class LLMInvalidResponseError(LLMServiceError):
    """Raised when the LLM service returns a malformed response or HTTP error."""


# -----------------------------------------------------------------------------
# Data Structures
# -----------------------------------------------------------------------------


@dataclass
class ToolCallRequest:
    """Represents a structured tool call requested by the LLM."""

    id: str
    name: str
    arguments: dict[str, Any]
    raw_arguments: str = ""


@dataclass
class LLMResponse:
    """Structured result returned by the LLM service."""

    content: str | None = None
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    finish_reason: str = "stop"
    raw_response: dict[str, Any] = field(default_factory=dict)

    @property
    def has_tool_calls(self) -> bool:
        """Check whether the model requested any tool executions."""
        return len(self.tool_calls) > 0


# -----------------------------------------------------------------------------
# LLM Service Implementation
# -----------------------------------------------------------------------------


class LLMService:
    """Provider-agnostic service connecting to NVIDIA Nemotron / OpenAI-compatible API."""

    def __init__(
        self,
        settings: Settings | None = None,
        tool_registry: Any | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Initialize LLMService with configuration and dependencies.

        Args:
            settings: Optional application settings.
            tool_registry: Optional ToolRegistry instance.
            http_client: Optional httpx.Client instance for testing / connection pooling.
        """
        self.settings = settings or get_settings()
        if tool_registry is not None:
            self.tool_registry = tool_registry
        else:
            from backend.app.agent.tool_registry import ToolRegistry

            self.tool_registry = ToolRegistry()
        self._custom_client = http_client

        # Resolution of configuration parameters
        self.model = self.settings.LLM_MODEL or "nvidia/nemotron-3.5-lightning-30b-a3b"
        self.base_url = (self.settings.effective_base_url or "https://integrate.api.nvidia.com/v1").rstrip("/")
        self.api_key = self.settings.effective_api_key
        self.timeout = getattr(self.settings, "LLM_TIMEOUT", 30.0)

    def _get_headers(self) -> dict[str, str]:
        """Construct secure authorization headers."""
        if not self.api_key or not self.api_key.strip():
            raise LLMAuthenticationError(
                "NVIDIA_API_KEY or LLM_API_KEY is not configured. "
                "Please set NVIDIA_API_KEY in your environment or .env file."
            )
        return {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_client(self) -> httpx.Client:
        """Return the active HTTP client."""
        if self._custom_client:
            return self._custom_client
        return httpx.Client(timeout=self.timeout)

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] = "auto",
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Send a chat completion request to the OpenAI-compatible endpoint.

        Args:
            messages: List of message objects ({'role': ..., 'content': ...}).
            tools: Optional list of tool schemas.
            tool_choice: Tool selection policy ('auto', 'none', etc.).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.

        Returns:
            LLMResponse: Structured response with content and parsed tool calls.

        Raises:
            LLMAuthenticationError: If credentials are missing or rejected.
            LLMTimeoutError: If the request times out.
            LLMInvalidResponseError: If the server returns 4xx/5xx or invalid JSON.
        """
        headers = self._get_headers()
        endpoint = f"{self.base_url}/chat/completions"

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        client = self._get_client()
        try:
            response = client.post(endpoint, json=payload, headers=headers)
        except httpx.TimeoutException as err:
            logger.error("Timeout connecting to Nemotron endpoint (%s): %s", endpoint, err)
            raise LLMTimeoutError("Nemotron request timed out. Please check network connectivity.") from err
        except httpx.RequestError as err:
            logger.error("HTTP request error connecting to Nemotron: %s", err)
            raise LLMServiceError(f"Network error connecting to Nemotron: {err}") from err

        # Handle HTTP status codes
        if response.status_code in (401, 403):
            logger.error("Nemotron authentication failed (HTTP %d).", response.status_code)
            raise LLMAuthenticationError(
                "Invalid or unauthorized NVIDIA API key. Please check your credentials."
            )

        if response.status_code != 200:
            logger.error("Nemotron returned HTTP %d: %s", response.status_code, response.text[:200])
            raise LLMInvalidResponseError(
                f"Nemotron API error (HTTP {response.status_code}): {response.text[:200]}"
            )

        # Parse JSON response
        try:
            data = response.json()
        except Exception as err:
            logger.error("Failed to parse Nemotron response as JSON: %s", err)
            raise LLMInvalidResponseError("Invalid JSON received from Nemotron API.") from err

        return self._parse_completion_response(data)

    def _parse_completion_response(self, data: dict[str, Any]) -> LLMResponse:
        """Parse raw OpenAI-compatible response into LLMResponse."""
        choices = data.get("choices", [])
        if not choices:
            return LLMResponse(content="", finish_reason="stop", raw_response=data)

        first_choice = choices[0]
        message = first_choice.get("message", {})
        finish_reason = first_choice.get("finish_reason", "stop")
        content = message.get("content")

        parsed_tool_calls: list[ToolCallRequest] = []
        raw_tool_calls = message.get("tool_calls", [])

        for tc in raw_tool_calls:
            tc_id = tc.get("id", "")
            func = tc.get("function", {})
            func_name = func.get("name", "")
            raw_args = func.get("arguments", "{}")

            # Parse arguments JSON safely
            if isinstance(raw_args, dict):
                args_dict = raw_args
                raw_str = json.dumps(raw_args)
            elif isinstance(raw_args, str):
                raw_str = raw_args
                try:
                    args_dict = json.loads(raw_args) if raw_args.strip() else {}
                except json.JSONDecodeError as err:
                    logger.warning("Malformed tool arguments JSON from LLM: %s", err)
                    args_dict = {}
            else:
                args_dict = {}
                raw_str = str(raw_args)

            parsed_tool_calls.append(
                ToolCallRequest(
                    id=tc_id,
                    name=func_name,
                    arguments=args_dict,
                    raw_arguments=raw_str,
                )
            )

        return LLMResponse(
            content=content,
            tool_calls=parsed_tool_calls,
            finish_reason=finish_reason,
            raw_response=data,
        )

    def run_conversation_turn(
        self,
        user_id: str,
        user_prompt: str,
        system_prompt: str | None = None,
        task_service: TaskService | None = None,
        message_history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Execute the complete Phase 6 conversation flow with Nemotron and Tool Calling.

        Flow:
        1. Receive authenticated user request.
        2. Send request and available tool definitions to Nemotron.
        3. Detect whether Nemotron requests a tool call.
        4. Validate the requested tool.
        5. Validate tool arguments.
        6. Inject authenticated user_id.
        7. Execute the existing TaskTool / ToolRegistry.
        8. Send the tool result back to Nemotron.
        9. Generate the final natural-language response.
        10. Return clean structured outcome.

        Args:
            user_id: Authenticated user Firebase UID.
            user_prompt: User's natural-language message.
            system_prompt: Optional custom system instructions.
            task_service: Optional TaskService override for testing.
            message_history: Optional prior conversation turns.

        Returns:
            dict[str, Any]: Dictionary containing final response, executed tool calls,
                            and operation success indicators.
        """
        # Security verification of authenticated user context
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            return {
                "success": False,
                "response": "Authentication required. Please provide a valid user session.",
                "tool_calls": [],
                "tool_results": [],
            }

        # Build initial messages
        default_system = (
            "You are TaskMate, an AI task management assistant. "
            "Help the user manage tasks using the provided tools. "
            "Only use approved tools when necessary. Answer questions truthfully based on tool results."
        )
        messages: list[dict[str, Any]] = []
        if message_history:
            messages.extend(message_history)
        else:
            messages.append({"role": "system", "content": system_prompt or default_system})

        messages.append({"role": "user", "content": user_prompt})

        tools_schema = self.tool_registry.get_tool_schemas()

        # Step 2: Query Nemotron with available tools
        try:
            llm_turn1 = self.chat_completion(messages=messages, tools=tools_schema)
        except LLMAuthenticationError as err:
            logger.error("Authentication error during LLM call: %s", err)
            return {
                "success": False,
                "response": "AI service configuration error: invalid or missing API credentials.",
                "tool_calls": [],
                "tool_results": [],
                "error": str(err),
            }
        except LLMTimeoutError as err:
            logger.error("Timeout during LLM call: %s", err)
            return {
                "success": False,
                "response": "The AI service timed out. Please try again.",
                "tool_calls": [],
                "tool_results": [],
                "error": str(err),
            }
        except LLMServiceError as err:
            logger.error("LLM service error: %s", err)
            return {
                "success": False,
                "response": "Unable to communicate with the AI service at this time.",
                "tool_calls": [],
                "tool_results": [],
                "error": str(err),
            }

        # Step 3: Check if tool calls were requested
        if not llm_turn1.has_tool_calls:
            # Direct response without tool calls
            return {
                "success": True,
                "response": llm_turn1.content or "",
                "tool_calls": [],
                "tool_results": [],
                "messages": messages + [{"role": "assistant", "content": llm_turn1.content}],
            }

        # Step 4-7: Process each tool call requested by Nemotron
        executed_tool_records: list[dict[str, Any]] = []
        tool_results: list[dict[str, Any]] = []

        # Prepare assistant message with tool calls for history
        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": llm_turn1.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": tc.raw_arguments,
                    },
                }
                for tc in llm_turn1.tool_calls
            ],
        }
        messages.append(assistant_msg)

        for tc in llm_turn1.tool_calls:
            # Step 4, 5, 6, 7: Validate and execute with injected user_id
            result = self.tool_registry.execute_tool(
                tool_name=tc.name,
                arguments=tc.arguments,
                user_id=user_id,
                task_service=task_service,
            )

            executed_tool_records.append({
                "id": tc.id,
                "name": tc.name,
                "arguments": tc.arguments,
            })
            tool_results.append(result)

            # Step 8: Append tool message to message history
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": tc.name,
                "content": json.dumps(result),
            })

        # Step 8-9: Send tool observations back to Nemotron for synthesis
        try:
            llm_turn2 = self.chat_completion(messages=messages, tools=tools_schema)
            final_response = llm_turn2.content or ""
        except LLMServiceError as err:
            logger.warning("Nemotron synthesis turn failed: %s; falling back to tool result description", err)
            # Fallback natural language description of tool result
            if tool_results and tool_results[0].get("message"):
                final_response = tool_results[0]["message"]
            elif tool_results and not tool_results[0].get("success"):
                final_response = f"I encountered an error: {tool_results[0].get('error')}"
            else:
                final_response = "The requested action was completed successfully."

        # Step 10: Return clean structured outcome
        return {
            "success": True,
            "response": final_response,
            "tool_calls": executed_tool_records,
            "tool_results": tool_results,
            "messages": messages + [{"role": "assistant", "content": final_response}],
        }
