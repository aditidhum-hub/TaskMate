"""Security module: Cryptographic Firebase ID token verification."""

import logging
from typing import Any

from fastapi import HTTPException, status
from firebase_admin import auth
from firebase_admin.exceptions import FirebaseError

from backend.app.services.firebase import get_firebase_app

logger = logging.getLogger(__name__)


def verify_firebase_token(id_token: str) -> dict[str, Any]:
    """Verify Firebase ID token and extract cryptographically signed claims.

    Derives authenticated identity directly from the verified JWT.
    Never accepts synthetic tokens or client-supplied identities.
    """
    if not id_token or not isinstance(id_token, str) or not id_token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ensure Firebase Admin is initialized before verification
    app = get_firebase_app()
    if not app:
        logger.error("Firebase Admin SDK is not initialized; cannot verify token.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable: Firebase Admin SDK is unconfigured.",
        )

    try:
        decoded_token = auth.verify_id_token(id_token.strip(), check_revoked=True)
        uid = decoded_token.get("uid")
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject UID claim.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return decoded_token
    except auth.ExpiredIdTokenError as err:
        logger.info("Firebase token expired: %s", err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
    except auth.RevokedIdTokenError as err:
        logger.warning("Firebase token has been revoked: %s", err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
    except (
        auth.InvalidIdTokenError,
        auth.CertificateFetchError,
        FirebaseError,
        ValueError,
    ) as err:
        logger.warning("Firebase token verification failed: %s", err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err
