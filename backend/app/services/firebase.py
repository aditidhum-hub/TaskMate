"""Firebase Admin SDK service initialization and management."""

import logging
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.exceptions import FirebaseError

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


def initialize_firebase() -> Any:
    """Initialize Firebase Admin SDK with project credentials or ADC.

    Returns the initialized Firebase App instance, or None if credentials are
    not configured.
    """
    if firebase_admin._apps:
        return firebase_admin.get_app()

    settings = get_settings()

    # Check for direct service-account credentials in environment variables
    if (
        settings.FIREBASE_PROJECT_ID
        and settings.FIREBASE_CLIENT_EMAIL
        and settings.FIREBASE_PRIVATE_KEY
    ):
        try:
            private_key = settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n")
            cred_dict = {
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "client_email": settings.FIREBASE_CLIENT_EMAIL,
                "private_key": private_key,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            cred = credentials.Certificate(cred_dict)
            app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized via environment credentials.")
            return app
        except (ValueError, KeyError, FirebaseError, OSError) as err:
            logger.warning("Failed to initialize Firebase Admin with credentials: %s", err)

    # Fallback to default credentials (ADC / Emulator) if available
    try:
        app = firebase_admin.initialize_app()
        logger.info("Firebase Admin SDK initialized via default application credentials.")
        return app
    except (ValueError, FirebaseError, OSError) as err:
        logger.warning(
            "Firebase Admin SDK could not be initialized with default credentials (%s). "
            "Running in unconfigured/offline mode.",
            err,
        )
        return None


def get_firebase_app() -> Any:
    """Retrieve the active Firebase App instance, initializing if needed."""
    if firebase_admin._apps:
        return firebase_admin.get_app()
    return initialize_firebase()


def get_firestore_client() -> Any:
    """Retrieve the Firestore client instance.

    Initializes Firebase app if needed, then returns firestore.client().
    Returns None if Firebase app cannot be initialized.
    """
    app = get_firebase_app()
    if app is None:
        logger.warning("Firebase app not initialized; Firestore client unavailable.")
        return None
    return firestore.client(app=app)
