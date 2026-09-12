"""FastAPI dependency injection providers for authentication and authorization."""

from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.core.security import verify_firebase_token

security_scheme = HTTPBearer(auto_error=False)
AuthCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)]


async def get_current_user(
    credentials: AuthCredentials = None,
) -> str:
    """Extract and verify authenticated user_id from Authorization Bearer header.

    Rejects requests without valid tokens with HTTP 401 Unauthorized.
    Derives user_id solely from the cryptographically verified JWT claims.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Authorization Bearer header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Bearer scheme required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    decoded_token = verify_firebase_token(credentials.credentials)
    user_id = decoded_token.get("uid")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject UID claim.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return str(user_id)


async def get_current_user_claims(
    credentials: AuthCredentials = None,
) -> dict[str, Any]:
    """Extract and return full decoded token claims for the authenticated user."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Authorization Bearer header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verify_firebase_token(credentials.credentials)
