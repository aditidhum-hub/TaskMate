"""Tests for Firebase authentication dependency, cryptographic token verification, and security boundaries."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from firebase_admin import auth

from backend.app.api.dependencies import get_current_user
from backend.app.core.security import verify_firebase_token

# Create isolated test application with a protected endpoint
auth_test_app = FastAPI()


@auth_test_app.get("/api/protected")
async def protected_endpoint(
    user_id: str = Depends(get_current_user),
    client_supplied_id: str | None = None,
) -> dict[str, str]:
    """Protected endpoint enforcing that user identity is derived strictly from token."""
    return {"user_id": user_id, "access": "granted"}


client = TestClient(auth_test_app)


# --- 1. Missing and Malformed Header Tests ---


def test_missing_authorization_header_returns_401():
    """Verify request without Authorization header is rejected with HTTP 401."""
    response = client.get("/api/protected")
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "Missing Authorization Bearer header" in response.json()["detail"]


def test_invalid_bearer_scheme_returns_401():
    """Verify non-Bearer Authorization header is rejected with HTTP 401."""
    headers = {"Authorization": "Basic dXNlcm5hbWU6cGFzc3dvcmQ="}
    response = client.get("/api/protected", headers=headers)
    assert response.status_code == 401
    assert "Bearer" in response.json()["detail"]


def test_empty_bearer_token_returns_401():
    """Verify empty or whitespace Bearer token is rejected with HTTP 401."""
    headers = {"Authorization": "Bearer    "}
    response = client.get("/api/protected", headers=headers)
    assert response.status_code == 401


# --- 2. Valid Token Verification and Identity Derivation Tests ---


@patch("backend.app.core.security.get_firebase_app")
@patch("firebase_admin.auth.verify_id_token")
def test_valid_token_returns_authenticated_user_id(mock_verify, mock_get_app):
    """Verify valid token returns HTTP 200 and extracts verified UID from token claims."""
    mock_get_app.return_value = MagicMock()
    mock_verify.return_value = {
        "uid": "verified_firebase_uid_123",
        "email": "user@example.com",
    }

    headers = {"Authorization": "Bearer legitimate-firebase-id-token"}
    response = client.get("/api/protected", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "verified_firebase_uid_123"
    assert data["access"] == "granted"


@patch("backend.app.core.security.get_firebase_app")
@patch("firebase_admin.auth.verify_id_token")
def test_client_supplied_user_id_cannot_override_verified_uid(mock_verify, mock_get_app):
    """Verify client-supplied parameter cannot spoof identity or override token UID."""
    mock_get_app.return_value = MagicMock()
    mock_verify.return_value = {"uid": "real_owner_uid"}

    headers = {"Authorization": "Bearer legitimate-firebase-id-token"}
    response = client.get("/api/protected?client_supplied_id=attacker_uid", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "real_owner_uid"


# --- 3. Expired, Revoked, and Invalid Token Rejection Tests ---


@patch("backend.app.core.security.get_firebase_app")
@patch("firebase_admin.auth.verify_id_token")
def test_expired_token_returns_401(mock_verify, mock_get_app):
    """Verify expired token raises HTTP 401."""
    mock_get_app.return_value = MagicMock()
    mock_verify.side_effect = auth.ExpiredIdTokenError("Token expired", "detail")

    headers = {"Authorization": "Bearer expired-firebase-jwt-token"}
    response = client.get("/api/protected", headers=headers)

    assert response.status_code == 401
    assert "has expired" in response.json()["detail"]


@patch("backend.app.core.security.get_firebase_app")
@patch("firebase_admin.auth.verify_id_token")
def test_revoked_token_returns_401(mock_verify, mock_get_app):
    """Verify revoked token raises HTTP 401."""
    mock_get_app.return_value = MagicMock()
    mock_verify.side_effect = auth.RevokedIdTokenError("Token revoked")

    headers = {"Authorization": "Bearer revoked-firebase-jwt-token"}
    response = client.get("/api/protected", headers=headers)

    assert response.status_code == 401
    assert "has been revoked" in response.json()["detail"]


@patch("backend.app.core.security.get_firebase_app")
@patch("firebase_admin.auth.verify_id_token")
def test_invalid_token_returns_401(mock_verify, mock_get_app):
    """Verify malformed or invalid token raises HTTP 401."""
    mock_get_app.return_value = MagicMock()
    mock_verify.side_effect = auth.InvalidIdTokenError("Malformed signature")

    headers = {"Authorization": "Bearer malformed-token-string"}
    response = client.get("/api/protected", headers=headers)

    assert response.status_code == 401
    assert "Invalid authentication token" in response.json()["detail"]


@patch("backend.app.core.security.get_firebase_app")
@patch("firebase_admin.auth.verify_id_token")
def test_missing_uid_claim_in_token_returns_401(mock_verify, mock_get_app):
    """Verify token missing subject UID claim raises HTTP 401."""
    mock_get_app.return_value = MagicMock()
    mock_verify.return_value = {"email": "no_uid@example.com"}

    headers = {"Authorization": "Bearer token-lacking-uid"}
    response = client.get("/api/protected", headers=headers)

    assert response.status_code == 401
    assert "missing subject UID" in response.json()["detail"]


# --- 4. Proof of Zero Synthetic Bypass ---


def test_synthetic_token_fails_without_mock():
    """Verify fabricated mock-valid-token string NEVER succeeds without legitimate verification.

    Confirms the application security logic contains zero artificial bypasses.
    """
    with pytest.raises(Exception) as excinfo:
        verify_firebase_token("mock-valid-token-attacker")
    # Must fail with either 401 (invalid token) or 503 (service unconfigured) — NEVER return claims
    assert excinfo.value.status_code in (401, 503)
