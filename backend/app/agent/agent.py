"""TaskMate Agent Orchestrator.

Orchestrates the iterative agent loop:
User Message + Authenticated Context -> Nemotron -> Tool Selection -> Tool Execution -> Observation -> Response Synthesis.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from backend.app.agent.prompts import TASKMATE_SYSTEM_PROMPT
from backend.app.agent.tool_registry import ToolRegistry
from backend.app.core.config import Settings, get_settings
from backend.app.services.llm_service import (
    LLMAuthenticationError,
    LLMInvalidResponseError,
    LLMResponse,
    LLMService,
    LLMServiceError,
    LLMTimeoutError,
)
from backend.app.services.task_service import TaskService

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Response Data Structure
# -----------------------------------------------------------------------------


@dataclass
class AgentResponse:
    """Standardized response from the TaskMate agent loop."""

    success: bool
    response: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert agent response to dictionary."""
        return {
            "success": self.success,
            "response": self.response,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "messages": self.messages,
            "error": self.error,
        }


# -----------------------------------------------------------------------------
# Agent Implementation
# -----------------------------------------------------------------------------


class TaskMateAgent:
    """Nemotron-backed AI Agent orchestrator for TaskMate."""

    def __init__(
        self,
        llm_service: LLMService | None = None,
        tool_registry: ToolRegistry | None = None,
        task_service: TaskService | None = None,
        settings: Settings | None = None,
        system_prompt: str = TASKMATE_SYSTEM_PROMPT,
        max_iterations: int = 5,
    ) -> None:
        """Initialize the agent with dependencies.

        Args:
            llm_service: Optional LLMService instance.
            tool_registry: Optional ToolRegistry instance.
            task_service: Optional TaskService instance.
            settings: Optional Settings instance.
            system_prompt: Base system instructions.
            max_iterations: Maximum tool calling iterations per user turn.
        """
        self.settings = settings or get_settings()
        self.tool_registry = tool_registry or ToolRegistry()
        self.task_service = task_service
        self.llm_service = llm_service or LLMService(
            settings=self.settings,
            tool_registry=self.tool_registry,
        )
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations

    def _sanitize_response_content(self, text: str | None) -> str:
        """Conceal raw thinking tags or reasoning markers from end-user output."""
        if not text:
            return ""

        # Strip XML-style thinking blocks: <think>...</think>
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # Strip alternative reasoning blocks if any
        cleaned = re.sub(r"\[thought\].*?\[/thought\]", "", cleaned, flags=re.DOTALL)
        return cleaned.strip()

    def process_message(
        self,
        user_id: str,
        message: str,
        message_history: list[dict[str, Any]] | None = None,
    ) -> AgentResponse:
        """Process a user message through the iterative agent loop.

        Args:
            user_id: Authenticated caller user ID (mandatory for tenant isolation).
            message: Raw natural language prompt from the user.
            message_history: Optional previous conversation messages.

        Returns:
            AgentResponse: Final sanitized response, executed tool traces, and history.

        Raises:
            ValueError: If user_id is empty, None, or only whitespace.
        """
        # Validate authenticated user context
        if not user_id or not user_id.strip():
            logger.error("Security violation: process_message called without valid user_id.")
            raise ValueError("user_id must be a non-empty, non-whitespace string.")

        user_id = user_id.strip()

        # Handle empty user message
        if not message or not message.strip():
            return AgentResponse(
                success=True,
                response="Please provide a message or task instruction.",
                tool_calls=[],
                tool_results=[],
                messages=message_history or [],
            )

        trimmed_message = message.strip()

        # Initialize conversation messages with sanitized history
        messages: list[dict[str, Any]] = []
        if message_history:
            # Filter and sanitize history to prevent malformed turns or leaking state
            for m in message_history:
                role = m.get("role")
                content = m.get("content")
                # Preserve tool role messages — they carry tool observations from
                # prior turns and must not be silently dropped or conversation
                # continuity breaks when the caller passes back full history.
                if role in ("user", "assistant", "system", "tool") and content is not None:
                    entry: dict[str, Any] = {"role": role, "content": str(content).strip()}
                    # Preserve tool_call_id for tool role messages (required by the API)
                    if role == "tool" and "tool_call_id" in m:
                        entry["tool_call_id"] = m["tool_call_id"]
                    if role == "tool" and "name" in m:
                        entry["name"] = m["name"]
                    messages.append(entry)

            # Ensure system prompt is present at root
            if not messages or messages[0].get("role") != "system":
                messages.insert(0, {"role": "system", "content": self.system_prompt})
        else:
            messages = [
                {"role": "system", "content": self.system_prompt},
            ]

        # Append current user prompt
        messages.append({"role": "user", "content": trimmed_message})

        tool_schemas = self.tool_registry.get_tool_schemas()
        executed_tool_calls: list[dict[str, Any]] = []
        collected_tool_results: list[dict[str, Any]] = []

        # Iterative agent execution loop
        for iteration in range(self.max_iterations):
            logger.debug("Agent loop iteration %d/%d for user %s", iteration + 1, self.max_iterations, user_id)

            # Once a tool has been executed, synthesize final response without tools
            # to eliminate redundant schema parsing overhead and latency
            current_tools = None if executed_tool_calls else tool_schemas
            current_choice = "none" if executed_tool_calls else "auto"
            # Use the configured max_tokens for tool-selection turns (direct answers
            # may be long). Use a fixed 384 for synthesis turns after tool execution.
            turn_max_tokens = 384 if executed_tool_calls else getattr(self.settings, "LLM_MAX_TOKENS", 512)

            try:
                llm_response: LLMResponse = self.llm_service.chat_completion(
                    messages=messages,
                    tools=current_tools,
                    tool_choice=current_choice,
                    max_tokens=turn_max_tokens,
                )
            except LLMAuthenticationError as err:
                logger.error("LLM authentication error: %s", err)
                return AgentResponse(
                    success=False,
                    response="AI service configuration error: invalid or missing API credentials.",
                    tool_calls=executed_tool_calls,
                    tool_results=collected_tool_results,
                    messages=messages,
                    error=str(err),
                )
            except LLMTimeoutError as err:
                logger.error("LLM request timeout: %s", err)
                return AgentResponse(
                    success=False,
                    response="The AI service timed out. Please try again.",
                    tool_calls=executed_tool_calls,
                    tool_results=collected_tool_results,
                    messages=messages,
                    error=str(err),
                )
            except (LLMInvalidResponseError, LLMServiceError) as err:
                logger.error("LLM service failure: %s", err)
                return AgentResponse(
                    success=False,
                    response="Unable to communicate with the AI service at this time.",
                    tool_calls=executed_tool_calls,
                    tool_results=collected_tool_results,
                    messages=messages,
                    error=str(err),
                )
            except Exception as err:
                logger.exception("Unexpected failure during LLM completion")
                return AgentResponse(
                    success=False,
                    response="An unexpected error occurred while processing your request.",
                    tool_calls=executed_tool_calls,
                    tool_results=collected_tool_results,
                    messages=messages,
                    error=str(err),
                )

            # Check if model requested tool execution
            if not llm_response.has_tool_calls:
                # No more tools needed — synthesized final response ready
                sanitized_content = self._sanitize_response_content(llm_response.content)
                # Guard: if sanitization stripped everything (e.g. pure whitespace or
                # bare newline from reasoning_budget suppression), return a safe fallback
                # rather than an empty string that would silently blank the UI.
                if not sanitized_content:
                    sanitized_content = "I'm ready to help. What would you like to do?"
                messages.append({"role": "assistant", "content": sanitized_content})
                return AgentResponse(
                    success=True,
                    response=sanitized_content,
                    tool_calls=executed_tool_calls,
                    tool_results=collected_tool_results,
                    messages=messages,
                )

            # Process requested tool calls
            # Append assistant's turn with tool_calls for OpenAI conversation compatibility
            assistant_message: dict[str, Any] = {
                "role": "assistant",
                "content": llm_response.content or None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": tc.raw_arguments if tc.raw_arguments else json.dumps(tc.arguments),
                        },
                    }
                    for tc in llm_response.tool_calls
                ],
            }
            messages.append(assistant_message)

            for tc in llm_response.tool_calls:
                logger.info("Executing tool '%s' with args %s for user %s", tc.name, tc.arguments, user_id)
                # Execute tool strictly bound to authenticated user_id
                result = self.tool_registry.execute_tool(
                    tool_name=tc.name,
                    arguments=tc.arguments,
                    user_id=user_id,
                    task_service=self.task_service,
                )

                tool_record = {
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": tc.arguments,
                }
                executed_tool_calls.append(tool_record)
                collected_tool_results.append(result)

                # Append tool observation to conversation history
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.name,
                    "content": json.dumps(result),
                })

        # If max iterations reached, perform a final synthesis without tools
        logger.warning("Agent reached maximum iterations (%d); synthesizing final response", self.max_iterations)
        try:
            final_turn = self.llm_service.chat_completion(
                messages=messages,
                tools=None,  # Do not allow further tool calls
            )
            final_content = self._sanitize_response_content(final_turn.content)
        except (LLMServiceError, LLMAuthenticationError, LLMTimeoutError) as err:
            logger.warning("Final synthesis after max iterations failed: %s", err)
            # Fallback based on last tool outcome
            if collected_tool_results:
                last_res = collected_tool_results[-1]
                if last_res.get("message"):
                    final_content = last_res["message"]
                elif not last_res.get("success"):
                    final_content = f"I encountered an issue: {last_res.get('error', 'Operation failed')}"
                else:
                    final_content = "Your request was processed successfully."
            else:
                final_content = "I was unable to complete the multi-step request."

        messages.append({"role": "assistant", "content": final_content})
        return AgentResponse(
            success=True,
            response=final_content,
            tool_calls=executed_tool_calls,
            tool_results=collected_tool_results,
            messages=messages,
        )
