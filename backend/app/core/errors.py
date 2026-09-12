"""Centralized error handling and exception sanitization for TaskMate backend."""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from firebase_admin.exceptions import FirebaseError

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Domain Exception Classes
# -----------------------------------------------------------------------------


class TaskMateError(Exception):
    """Base exception for all domain and service errors in TaskMate."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(TaskMateError):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class UnauthorizedError(TaskMateError):
    """Raised when authentication fails or is missing."""

    def __init__(self, message: str = "Unauthorized access.") -> None:
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class ValidationError(TaskMateError):
    """Raised when user input fails domain validation."""

    def __init__(self, message: str = "Invalid input data.") -> None:
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class ServiceUnavailableError(TaskMateError):
    """Raised when an upstream dependency (e.g. LLM, Firebase) is unreachable."""

    def __init__(self, message: str = "Service temporarily unavailable.") -> None:
        super().__init__(message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


# -----------------------------------------------------------------------------
# Global Exception Handlers
# -----------------------------------------------------------------------------


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard FastAPI/Starlette HTTPExceptions."""
    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


async def taskmate_error_handler(request: Request, exc: TaskMateError) -> JSONResponse:
    """Handle custom domain TaskMateError instances."""
    logger.warning("TaskMate domain error [%d]: %s", exc.status_code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic/FastAPI request validation errors safely.

    Converts internal validation structures to clean, client-safe error messages.
    """
    sanitized_errors: list[dict[str, Any]] = []
    for err in exc.errors():
        loc = [str(x) for x in err.get("loc", []) if str(x) != "body"]
        field_name = ".".join(loc) if loc else "request"
        sanitized_errors.append({
            "field": field_name,
            "message": err.get("msg", "Invalid value"),
        })

    logger.info("Request validation failed on %s: %s", request.url.path, sanitized_errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed. Please check your input.",
            "errors": sanitized_errors,
        },
    )


async def firebase_error_handler(request: Request, exc: FirebaseError) -> JSONResponse:
    """Handle Firebase Admin SDK exceptions securely without leaking internal token/API details."""
    logger.error("Firebase service error during request to %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Authentication service error or invalid credentials."},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler for unexpected 500 errors.

    CRITICAL SECURITY GUARD: Never expose stack traces, database paths, or internal
    exception details to the client. Full traceback is logged server-side only.
    """
    logger.exception(
        "CRITICAL: Unhandled server exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again later.",
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all sanitized exception handlers onto the FastAPI application instance."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(TaskMateError, taskmate_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(FirebaseError, firebase_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
