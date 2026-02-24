"""Firestore service for clinical record storage.

Enforces DEMO/PROD namespace isolation and raw-note policies.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from google.cloud import firestore

from shared.schemas import Mode, StructuredResult

logger = logging.getLogger(__name__)

_db: firestore.AsyncClient | None = None


def _get_db() -> firestore.AsyncClient:
    global _db
    if _db is None:
        _db = firestore.AsyncClient()
    return _db


async def save_encounter(uid: str, mode: Mode, result: StructuredResult) -> None:
    db = _get_db()
    collection = f"{mode.value}_users"
    doc_ref = (
        db.collection(collection)
        .document(uid)
        .collection("encounters")
        .document(result.note_id)
    )
    data = result.model_dump(mode="json")
    data.pop("raw_note_text", None)
    await doc_ref.set(data)


async def save_encounter_from_sync(
    uid: str, mode: Mode, result: StructuredResult
) -> None:
    await save_encounter(uid, mode, result)


async def save_raw_note(uid: str, note_id: str, note_text: str) -> None:
    """Store raw note in PROD-only collection. NEVER call in DEMO mode."""
    db = _get_db()
    doc_ref = (
        db.collection("prod_users")
        .document(uid)
        .collection("raw_notes")
        .document(note_id)
    )
    await doc_ref.set({
        "note_id": note_id,
        "note_text": note_text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


async def check_idempotency_key(uid: str, idempotency_key: str) -> bool:
    db = _get_db()
    doc_ref = (
        db.collection("idempotency_keys")
        .document(uid)
        .collection("keys")
        .document(idempotency_key)
    )
    doc = await doc_ref.get()
    return doc.exists


async def save_idempotency_key(
    uid: str, idempotency_key: str, note_id: str
) -> None:
    db = _get_db()
    doc_ref = (
        db.collection("idempotency_keys")
        .document(uid)
        .collection("keys")
        .document(idempotency_key)
    )
    await doc_ref.set({
        "note_id": note_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


async def get_encounters(uid: str, mode: Mode, limit: int = 50) -> list[dict]:
    db = _get_db()
    collection = f"{mode.value}_users"
    docs = (
        db.collection(collection)
        .document(uid)
        .collection("encounters")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )
    results = []
    async for doc in docs.stream():
        results.append(doc.to_dict())
    return results
