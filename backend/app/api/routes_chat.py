"""FastAPI route handlers for conversational AI agent (/api/chat)."""

import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.agent.agent import AgentResponse, TaskMateAgent
from backend.app.api.dependencies import get_current_user
from backend.app.models.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


def get_agent() -> TaskMateAgent:
    """Dependency provider for TaskMateAgent to facilitate testing and configuration."""
    return TaskMateAgent()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with TaskMate AI Agent",
    description="Primary conversational interaction endpoint backed by the Nemotron agent loop.",
)
async def chat_endpoint(
    request: ChatRequest,
    user_id: Annotated[str, Depends(get_current_user)],
    agent: Annotated[TaskMateAgent, Depends(get_agent)],
) -> ChatResponse:
    """Process a user message through the authenticated Nemotron agent loop."""
    start_time = time.perf_counter()
    logger.info(
        "Chat request received: user_id=%s, message_length=%d",
        user_id,
        len(request.message),
    )

    try:
        agent_outcome: AgentResponse = agent.process_message(
            user_id=user_id,
            message=request.message,
            message_history=request.message_history,
        )
    except ValueError as err:
        logger.warning("Validation error in agent process_message: %s", err)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        ) from err
    except Exception as err:
        logger.exception("Unexpected exception during agent execution")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the conversational agent request.",
        ) from err

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    logger.info(
        "Chat request finished: user_id=%s, latency=%.2fms, success=%s, tools_called=%d",
        user_id,
        elapsed_ms,
        agent_outcome.success,
        len(agent_outcome.tool_calls),
    )

    # Derive tool_used and created_task fields for response convenience
    tool_used: str | None = None
    if agent_outcome.tool_calls:
        tool_used = agent_outcome.tool_calls[0].get("name")

    created_task: dict | None = None
    for result in agent_outcome.tool_results:
        if isinstance(result, dict) and result.get("success") and "task" in result:
            created_task = result["task"]
            break

    return ChatResponse(
        response=agent_outcome.response,
        tool_used=tool_used,
        created_task=created_task,
        tool_calls=agent_outcome.tool_calls,
        tool_results=agent_outcome.tool_results,
        messages=agent_outcome.messages,
        success=agent_outcome.success,
    )
