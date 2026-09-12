"""FastAPI Application Entry Point for TaskMate Modular Monolith Backend."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes_chat import router as chat_router
from backend.app.api.routes_health import router as health_router
from backend.app.core.config import get_settings
from backend.app.core.errors import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown lifecycle."""
    yield


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="TaskMate Modular Monolith API — AI-Powered Task Management Assistant",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Register centralized exception sanitization handlers
register_exception_handlers(app)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
# Health check supported at both `/health` and `/api/health`
app.include_router(health_router)
app.include_router(health_router, prefix="/api")

# Conversational Agent Loop route mounted at `/api/chat`
app.include_router(chat_router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Root entry providing basic service information."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
