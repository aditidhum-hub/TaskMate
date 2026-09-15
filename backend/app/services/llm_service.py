"""LLM Service connecting to NVIDIA Nemotron via an OpenAI-compatible API interface."""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, ClassVar

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

    _shared_client: ClassVar[httpx.Client | None] = None

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
            # NOTE: Do NOT set Connection: close here — it contradicts the
            # keepalive pool and causes dead-socket reuse on subsequent requests.
        }

    @classmethod
    def get_shared_client(cls, timeout: float = 30.0) -> httpx.Client:
        """Return or lazily initialize the shared connection-pooled HTTP client.

        NOTE: This is intentionally kept for test injection compatibility, but
        production code now uses _make_request_client() per request to avoid
        dead-socket reuse with the NVIDIA API server.
        """
        if cls._shared_client is None or cls._shared_client.is_closed:
            cls._shared_client = httpx.Client(
                timeout=timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10,
                    keepalive_expiry=10.0,
                ),
            )
        return cls._shared_client

    @classmethod
    def reset_shared_client(cls) -> None:
        """Reset the shared client to clean up state on communication errors."""
        if cls._shared_client is not None:
            try:
                cls._shared_client.close()
            except httpx.HTTPError as close_err:
                logger.debug("Error closing shared HTTP client: %s", close_err)
            cls._shared_client = None

    def _get_client(self) -> httpx.Client:
        """Return the active HTTP client (custom override for tests only)."""
        if self._custom_client:
            return self._custom_client
        return self.get_shared_client(timeout=self.timeout)

    def _make_fresh_client(self) -> httpx.Client:
        """Create a brand-new httpx.Client for a single request.

        Using a fresh client per request avoids all connection-pool state bugs
        (dead sockets, WinError 10038, reset-by-peer) that occur when the NVIDIA
        API closes a keepalive connection unexpectedly between requests.
        """
        return httpx.Client(
            timeout=httpx.Timeout(
                connect=10.0,     # Fail fast if we can't reach the server
                read=self.timeout,  # Full timeout for model inference
                write=10.0,
                pool=5.0,
            ),
        )


    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] = "auto",
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Send a chat completion request to the OpenAI-compatible endpoint.

        Args:
            messages: List of message objects ({'role': ..., 'content': ...}).
            tools: Optional list of tool schemas.
            tool_choice: Tool selection policy ('auto', 'none', etc.).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response. Defaults to LLM_MAX_TOKENS (512).

        Returns:
            LLMResponse: Structured response with content and parsed tool calls.

        Raises:
            LLMAuthenticationError: If credentials are missing or rejected.
            LLMTimeoutError: If the request times out.
            LLMInvalidResponseError: If the server returns 4xx/5xx or invalid JSON.
        """
        headers = self._get_headers()
        endpoint = f"{self.base_url}/chat/completions"

        effective_max_tokens = (
            max_tokens
            if max_tokens is not None
            else getattr(self.settings, "LLM_MAX_TOKENS", 512)
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": effective_max_tokens,
        }

        if tools:
            # Do NOT send reasoning_budget when tools are active.
            # reasoning_budget=0 combined with tool_choice="auto" causes the
            # Nemotron model to hang or produce severely degraded latency (1–60s
            # variance observed). The model needs reasoning tokens to decide
            # which tool to call; suppressing them here contradicts tool-use mode.
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice
        else:
            # reasoning_budget=0 is safe on non-tool turns (direct text synthesis).
            # It suppresses chain-of-thought tokens, reducing latency ~3-5s -> ~1.5s.
            reasoning_budget = getattr(self.settings, "LLM_REASONING_BUDGET", 0)
            payload["reasoning_budget"] = reasoning_budget

        # Use a fresh client per request to avoid dead-socket reuse issues
        # (WinError 10038, RemoteProtocolError) with the NVIDIA API's unpredictable
        # keepalive behaviour. Tests can inject _custom_client to bypass this.
        use_custom = self._custom_client is not None
        try:
            if use_custom:
                response = self._custom_client.post(endpoint, json=payload, headers=headers)
            else:
                with self._make_fresh_client() as fresh_client:
                    response = fresh_client.post(endpoint, json=payload, headers=headers)
        except httpx.TimeoutException as err:
            logger.error(
                "Timeout calling Nemotron (%s): %s",
                endpoint, err,
            )
            raise LLMTimeoutError(
                "Nemotron request timed out. Please try again."
            ) from err
        except httpx.RequestError as err:
            logger.error("HTTP request error calling Nemotron: %s", err)
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
            func_name = (func.get("name") or "").strip()
            # Clean func_name from XML or thinking artifacts (e.g. "list_tasks\n</function" -> "list_tasks")
            if func_name:
                func_name = re.split(r"[\s<>\n/]+", func_name)[0].strip()

            raw_args = func.get("arguments", "{}")

            # Parse arguments JSON safely
            if isinstance(raw_args, dict):
                args_dict = raw_args
                raw_str = json.dumps(raw_args)
            elif isinstance(raw_args, str):
                raw_str = raw_args.strip()
                # Clean any XML or closing tags trailing behind JSON
                if "</" in raw_str:
                    raw_str = raw_str.split("</")[0].strip()
                try:
                    args_dict = json.loads(raw_str) if raw_str else {}
                except json.JSONDecodeError:
                    # Attempt to extract embedded JSON object if wrapped by text
                    match = re.search(r"\{.*\}", raw_str, re.DOTALL)
                    if match:
                        try:
                            args_dict = json.loads(match.group(0))
                            raw_str = match.group(0)
                        except json.JSONDecodeError as err:
                            logger.warning("Malformed tool arguments JSON from LLM: %s", err)
                            args_dict = {}
                    else:
                        logger.warning("Malformed tool arguments JSON from LLM: %s", raw_str)
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
        # Pass tools=None to avoid redundant schema overhead on the synthesis turn.
        try:
            llm_turn2 = self.chat_completion(messages=messages, tools=None)
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
