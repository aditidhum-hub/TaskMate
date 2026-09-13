"""Rate limiting middleware protecting conversational endpoints (Phase 13).

Enforces IP and User rate limiting on `/api/chat` to protect against API abuse,
denial of service, and runaway LLM invocation costs.
"""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory sliding-window rate limiter with automatic cleanup."""

    def __init__(self, requests_limit: int = 60, window_seconds: int = 60) -> None:
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        # Mapping: caller_key -> list of request timestamps (float)
        self._records: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> tuple[bool, int]:
        """Check if request for key is allowed under the rate limit.

        Returns:
            (allowed: bool, retry_after: int)
        """
        now = time.time()
        cutoff = now - self.window_seconds

        async with self._lock:
            # Prune outdated timestamps for this key
            timestamps = [t for t in self._records[key] if t > cutoff]

            if len(timestamps) >= self.requests_limit:
                # Oldest timestamp in current window determines retry delay
                oldest = timestamps[0]
                retry_after = max(1, int(oldest + self.window_seconds - now))
                self._records[key] = timestamps
                return False, retry_after

            # Record current request
            timestamps.append(now)
            self._records[key] = timestamps
            return True, 0

    async def reset(self) -> None:
        """Reset all tracking records (useful in tests)."""
        async with self._lock:
            self._records.clear()


# Default singleton instance bound to application settings
_settings = get_settings()
default_rate_limiter = RateLimiter(
    requests_limit=_settings.RATE_LIMIT_REQUESTS,
    window_seconds=_settings.RATE_LIMIT_WINDOW_SECONDS,
)


def _get_caller_key(request: Request) -> str:
    """Derive caller identity key from authorization header or client IP."""
    # If state has verified user_id, use it
    if hasattr(request.state, "user_id") and request.state.user_id:
        return f"user:{request.state.user_id}"

    # Extract user hint from Authorization header if present
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token_snippet = auth_header[7:].strip()
        if token_snippet:
            # Hash or take prefix to form stable identifier
            return f"token:{hash(token_snippet)}"

    # Fallback to client IP
    client_ip = request.client.host if request.client else "unknown_ip"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    return f"ip:{client_ip}"


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing rate limits specifically on conversational endpoints."""

    def __init__(
        self,
        app: Any,
        rate_limiter: RateLimiter | None = None,
        protected_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.rate_limiter = rate_limiter or default_rate_limiter
        self.protected_paths = protected_paths or {"/api/chat"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Check if the requested path is protected by rate limiting
        if request.method == "POST" and request.url.path in self.protected_paths:
            caller_key = _get_caller_key(request)
            allowed, retry_after = await self.rate_limiter.is_allowed(caller_key)

            if not allowed:
                request_id = getattr(request.state, "request_id", "unknown")
                logger.warning(
                    "Rate limit exceeded: caller=%s, path=%s, request_id=%s, retry_after=%ds",
                    caller_key,
                    request.url.path,
                    request_id,
                    retry_after,
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Rate limit exceeded. Maximum {self.rate_limiter.requests_limit} requests "
                        f"per {self.rate_limiter.window_seconds} seconds allowed.",
                        "retry_after": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

        return await call_next(request)
