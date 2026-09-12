"""FastAPI Application Entry Point for TaskMate Modular Monolith Backend."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes_health import router as health_router
from backend.app.core.config import get_settings


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

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Health Check Routes
# Supported at both `/health` and `/api/health` for compatibility
app.include_router(health_router)
app.include_router(health_router, prefix="/api")


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Root entry providing basic service information."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
