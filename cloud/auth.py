"""Firebase Auth middleware for Cloud Run.

Verifies Firebase ID tokens and enforces DEMO/PROD auth policies.
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections import defaultdict
from typing import Any

import firebase_admin
from fastapi import Depends, HTTPException, Request
from firebase_admin import auth as firebase_auth, credentials

from cloud.config import Settings, get_settings

logger = logging.getLogger(__name__)

_app_initialized = False
_rate_limit_store: dict[str, list[float]] = defaultdict(list)


def init_firebase() -> None:
    global _app_initialized
    if not _app_initialized:
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app()
        _app_initialized = True


def hash_uid(uid: str) -> str:
    return hashlib.sha256(uid.encode()).hexdigest()[:16]


def _check_rate_limit(uid: str, settings: Settings) -> None:
    now = time.time()
    window = 60.0
    timestamps = _rate_limit_store[uid]
    _rate_limit_store[uid] = [t for t in timestamps if now - t < window]
    if len(_rate_limit_store[uid]) >= settings.RATE_LIMIT_PER_MIN:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    _rate_limit_store[uid].append(now)


async def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Extract and verify Firebase ID token from Authorization header."""
    init_firebase()

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        # In demo mode, allow unauthenticated requests with a guest identity
        if settings.DEMO_MODE_ENABLED:
            logger.info("Demo mode: allowing unauthenticated guest request")
            guest_id = f"demo-guest-{hashlib.sha256(str(request.client.host).encode()).hexdigest()[:12]}"
            _check_rate_limit(guest_id, settings)
            return {
                "uid": guest_id,
                "uid_hash": hash_uid(guest_id),
                "provider": "anonymous",
                "is_anonymous": True,
            }
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header[7:]
    try:
        decoded = firebase_auth.verify_id_token(token)
    except Exception as e:
        logger.warning("Token verification failed: %s", type(e).__name__)
        if settings.DEMO_MODE_ENABLED:
            logger.info("Demo mode: allowing request despite invalid token")
            return {
                "uid": "demo-guest-fallback",
                "uid_hash": hash_uid("demo-guest-fallback"),
                "provider": "anonymous",
                "is_anonymous": True,
            }
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    uid = decoded.get("uid", "")
    provider = decoded.get("firebase", {}).get("sign_in_provider", "")

    _check_rate_limit(uid, settings)

    logger.info("Authenticated uid_hash=%s provider=%s", hash_uid(uid), provider)

    return {
        "uid": uid,
        "uid_hash": hash_uid(uid),
        "provider": provider,
        "is_anonymous": provider == "anonymous",
    }
