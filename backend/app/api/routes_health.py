"""Health check endpoint definitions."""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.core.config import get_settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health response model."""

    status: str = Field(default="ok", description="Service operational status")
    service: str = Field(default="TaskMate Backend", description="Service identifier")
    timestamp: str = Field(
        description="Current UTC timestamp in ISO-8601 format"
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns the operational status, service name, and current UTC timestamp.",
)
async def get_health() -> HealthResponse:
    """Check backend service liveness."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.APP_NAME,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
