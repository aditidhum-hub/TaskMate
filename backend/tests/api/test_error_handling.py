"""Tests for centralized API error handling and exception sanitization (Phase 11)."""

from fastapi import APIRouter, status
from fastapi.testclient import TestClient
from firebase_admin.exceptions import FirebaseError

from backend.app.core.errors import (
    NotFoundError,
    ServiceUnavailableError,
    TaskMateError,
    UnauthorizedError,
    ValidationError,
)
from backend.app.main import app

error_test_router = APIRouter(prefix="/test-errors")


@error_test_router.get("/unhandled-crash")
def trigger_unhandled_crash():
    """Route that deliberately triggers an unhandled Python RuntimeError with sensitive details."""
    raise RuntimeError("Internal database connection failed at postgres://user:secret@internal-db:5432/taskmate_prod")


@error_test_router.get("/custom-not-found")
def trigger_not_found():
    raise NotFoundError("Task item 'task_999' could not be found.")


@error_test_router.get("/custom-unauthorized")
def trigger_unauthorized():
    raise UnauthorizedError("Session has expired.")


@error_test_router.get("/custom-validation")
def trigger_validation():
    raise ValidationError("Due date cannot be in the distant past.")


@error_test_router.get("/custom-service-unavailable")
def trigger_service_unavailable():
    raise ServiceUnavailableError("Upstream AI model provider is currently unreachable.")


@error_test_router.get("/custom-base-error")
def trigger_base_error():
    raise TaskMateError("Generic domain error", status_code=502)


@error_test_router.get("/firebase-error")
def trigger_firebase_error():
    raise FirebaseError(500, "Internal crypto verification failed in google-auth token decode")


from pydantic import BaseModel, Field


class SampleValidationModel(BaseModel):
    name: str = Field(..., min_length=2)
    count: int = Field(..., ge=1)


@error_test_router.post("/pydantic-validation")
def trigger_pydantic_validation(payload: SampleValidationModel):
    return {"status": "ok", "data": payload.model_dump()}


# Mount the test router onto the app for error verification
app.include_router(error_test_router)

client = TestClient(app, raise_server_exceptions=False)


def test_unhandled_exception_sanitized_500():
    """Verify that unhandled server exceptions return a 500 without leaking stack traces or internal secrets."""
    response = client.get("/test-errors/unhandled-crash")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()

    # Must contain generic message
    assert "detail" in data
    assert data["detail"] == "An internal server error occurred. Please try again later."

    # CRITICAL: Verify zero leakage of credentials, tracebacks, or file paths
    raw_text = response.text
    assert "Traceback" not in raw_text
    assert "postgres" not in raw_text
    assert "secret" not in raw_text
    assert "internal-db" not in raw_text
    assert ".py" not in raw_text


def test_custom_not_found_error():
    """Verify NotFoundError returns 404 with clean detail message."""
    response = client.get("/test-errors/custom-not-found")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Task item 'task_999' could not be found."}


def test_custom_unauthorized_error():
    """Verify UnauthorizedError returns 401."""
    response = client.get("/test-errors/custom-unauthorized")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Session has expired."}


def test_custom_validation_error():
    """Verify ValidationError returns 422."""
    response = client.get("/test-errors/custom-validation")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {"detail": "Due date cannot be in the distant past."}


def test_custom_service_unavailable_error():
    """Verify ServiceUnavailableError returns 503."""
    response = client.get("/test-errors/custom-service-unavailable")
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {"detail": "Upstream AI model provider is currently unreachable."}


def test_custom_base_domain_error():
    """Verify TaskMateError respects custom status code."""
    response = client.get("/test-errors/custom-base-error")
    assert response.status_code == 502
    assert response.json() == {"detail": "Generic domain error"}


def test_firebase_error_sanitization():
    """Verify FirebaseError returns 401 with safe message and WWW-Authenticate header."""
    response = client.get("/test-errors/firebase-error")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers.get("WWW-Authenticate") == "Bearer"
    assert response.json() == {"detail": "Authentication service error or invalid credentials."}
    assert "google-auth" not in response.text


def test_request_validation_error_sanitization():
    """Verify Pydantic validation failures return structured, sanitized field errors."""
    response = client.post(
        "/test-errors/pydantic-validation",
        json={"name": "a", "count": 0},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data
    assert "errors" in data
    fields = [err.get("field") for err in data["errors"]]
    assert "name" in fields
    assert "count" in fields
