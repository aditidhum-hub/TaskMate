"""Structured diagnostic logging for TaskMate backend (Phase 13).

Provides JSON-formatted logging capturing request diagnostics (request_id,
user_id, status_code, latency_ms, tool_name) while strictly redacting
passwords, API keys, tokens, and private user conversation content.
"""

import json
import logging
import sys
import time
from typing import Any
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Keys that must never appear in diagnostic logs
SENSITIVE_KEYS = {
    "password",
    "token",
    "authorization",
    "api_key",
    "secret",
    "private_key",
    "credentials",
}


class JsonLogFormatter(logging.Formatter):
    """Custom formatter emitting structured JSON log entries."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach custom contextual data if provided
        context = getattr(record, "context", None)
        if isinstance(context, dict):
            # Sanitize context to ensure no sensitive parameters leak
            sanitized_context = {}
            for k, v in context.items():
                if any(sensitive in k.lower() for sensitive in SENSITIVE_KEYS):
                    sanitized_context[k] = "[REDACTED]"
                else:
                    sanitized_context[k] = v
            log_entry["context"] = sanitized_context

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure application logging handlers and formatters.

    Args:
        log_level: Standard log level ('DEBUG', 'INFO', 'WARNING', 'ERROR').
        log_format: Format style ('json' or 'text').
    """
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Remove existing stream handlers to prevent duplicate lines
    for handler in list(root_logger.handlers):
        if isinstance(handler, logging.StreamHandler):
            root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    if log_format.lower() == "json":
        console_handler.setFormatter(JsonLogFormatter())
    else:
        standard_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        console_handler.setFormatter(logging.Formatter(standard_format))

    root_logger.addHandler(console_handler)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """HTTP middleware capturing request_id, latency, status_code, and user diagnostics."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract or generate unique request_id
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid4().hex[:12]}"
        request.state.request_id = request_id

        start_time = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Inject request_id header into response for tracing
        response.headers["X-Request-ID"] = request_id

        # Determine caller identity if established on request state
        user_id = getattr(request.state, "user_id", None) or "unauthenticated"

        # Safe diagnostic log record (never logs request body or sensitive credentials)
        diagnostic_context = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "user_id": user_id,
        }

        logger = logging.getLogger("taskmate.request")
        logger.info(
            "%s %s -> %d (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            latency_ms,
            extra={"context": diagnostic_context},
        )

        return response
