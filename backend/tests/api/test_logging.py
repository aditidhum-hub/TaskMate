"""Automated tests for structured diagnostic logging (Phase 13)."""

import json
import logging

from fastapi.testclient import TestClient

from backend.app.core.logging import JsonLogFormatter
from backend.app.main import app


def test_json_log_formatter_structure():
    """Verify that JsonLogFormatter produces valid JSON with required keys."""
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Sample log event",
        args=(),
        exc_info=None,
    )
    record.context = {
        "request_id": "req_12345",
        "method": "POST",
        "path": "/api/chat",
        "latency_ms": 12.34,
        "status_code": 200,
        "user_id": "user_abc",
    }

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["message"] == "Sample log event"
    assert "timestamp" in parsed
    assert "context" in parsed
    assert parsed["context"]["request_id"] == "req_12345"
    assert parsed["context"]["status_code"] == 200


def test_json_log_formatter_redacts_sensitive_keys():
    """Verify that credentials and tokens are redacted from structured context."""
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=20,
        msg="Auth event",
        args=(),
        exc_info=None,
    )
    record.context = {
        "token": "secret_jwt_token",
        "api_key": "nvapi-very-secret",
        "password": "super_secret_password",
        "authorization": "Bearer secret",
        "request_id": "req_999",
    }

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["context"]["token"] == "[REDACTED]"
    assert parsed["context"]["api_key"] == "[REDACTED]"
    assert parsed["context"]["password"] == "[REDACTED]"
    assert parsed["context"]["authorization"] == "[REDACTED]"
    assert parsed["context"]["request_id"] == "req_999"


def test_structured_logging_middleware_injects_request_id():
    """Verify that requests pass through middleware and receive an X-Request-ID header."""
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")
