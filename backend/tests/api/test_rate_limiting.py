"""Automated tests for rate limiting middleware (Phase 13)."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from backend.app.api.middleware import RateLimiter, RateLimitingMiddleware
from backend.app.main import app


@pytest.fixture(autouse=True)
def clean_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_agent():
    from backend.app.agent.agent import AgentResponse

    agent = pytest.importorskip("unittest.mock").MagicMock()
    agent.process_message.return_value = AgentResponse(
        success=True,
        response="Test rate limit response",
        messages=[],
    )
    return agent


def test_rate_limiter_allows_under_threshold():
    """Verify requests under the threshold are allowed."""
    limiter = RateLimiter(requests_limit=3, window_seconds=60)

    # Directly check limiter logic
    import asyncio

    allowed1, _ = asyncio.run(limiter.is_allowed("user_1"))
    allowed2, _ = asyncio.run(limiter.is_allowed("user_1"))
    allowed3, _ = asyncio.run(limiter.is_allowed("user_1"))
    blocked, retry_after = asyncio.run(limiter.is_allowed("user_1"))

    assert allowed1 is True
    assert allowed2 is True
    assert allowed3 is True
    assert blocked is False
    assert retry_after > 0


def test_rate_limiting_middleware_blocks_excess_requests(mock_agent):
    """Verify middleware returns HTTP 429 when threshold is exceeded."""
    from fastapi import FastAPI

    # Create isolated test app with a low threshold for fast testing
    test_app = FastAPI()
    custom_limiter = RateLimiter(requests_limit=2, window_seconds=10)
    test_app.add_middleware(RateLimitingMiddleware, rate_limiter=custom_limiter, protected_paths={"/test-chat"})

    @test_app.post("/test-chat")
    def fake_chat():
        return {"status": "ok"}

    client = TestClient(test_app)

    # First request -> 200
    r1 = client.post("/test-chat", headers={"Authorization": "Bearer token1"})
    assert r1.status_code == status.HTTP_200_OK

    # Second request -> 200
    r2 = client.post("/test-chat", headers={"Authorization": "Bearer token1"})
    assert r2.status_code == status.HTTP_200_OK

    # Third request -> 429 Too Many Requests
    r3 = client.post("/test-chat", headers={"Authorization": "Bearer token1"})
    assert r3.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    data = r3.json()
    assert "Rate limit exceeded" in data["detail"]
    assert "retry_after" in data
    assert "Retry-After" in r3.headers


def test_rate_limiting_isolated_per_user():
    """Verify that User A reaching rate limit does not block User B."""
    from fastapi import FastAPI

    test_app = FastAPI()
    custom_limiter = RateLimiter(requests_limit=1, window_seconds=10)
    test_app.add_middleware(RateLimitingMiddleware, rate_limiter=custom_limiter, protected_paths={"/test-chat"})

    @test_app.post("/test-chat")
    def fake_chat():
        return {"status": "ok"}

    client = TestClient(test_app)

    # User A sends request 1 (allowed)
    r_a1 = client.post("/test-chat", headers={"Authorization": "Bearer token_a"})
    assert r_a1.status_code == status.HTTP_200_OK

    # User A sends request 2 (blocked)
    r_a2 = client.post("/test-chat", headers={"Authorization": "Bearer token_a"})
    assert r_a2.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    # User B sends request 1 (allowed, separate quota)
    r_b1 = client.post("/test-chat", headers={"Authorization": "Bearer token_b"})
    assert r_b1.status_code == status.HTTP_200_OK


def test_health_endpoints_unaffected_by_rate_limits():
    """Verify that GET /health is not constrained by chat rate limits."""
    client = TestClient(app)
    for _ in range(5):
        resp = client.get("/health")
        assert resp.status_code == status.HTTP_200_OK
