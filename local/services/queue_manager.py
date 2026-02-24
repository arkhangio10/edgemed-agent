"""Encrypted queue manager backed by SQLite + Tink AEAD.

Only ciphertext is stored in SQLite. Plaintext metadata (note_id, status,
timestamps) is stored alongside for queue management.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from local.services.tink_crypto import TinkAEAD

logger = logging.getLogger(__name__)

SCHEMA_SQL = (Path(__file__).resolve().parent.parent / "db" / "schema.sql").read_text(
    encoding="utf-8"
)


class QueueManager:
    def __init__(self, db_path: str, keyset_path: str):
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._crypto = TinkAEAD(keyset_path)
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        logger.info("SQLite queue database initialized at %s", self._db_path)

    def enqueue(self, note_id: str, payload: dict, mode: str) -> str:
        """Encrypt payload and insert into queue. Returns idempotency_key."""
        from local.config import get_local_settings

        settings = get_local_settings()
        idempotency_key = f"{settings.DEVICE_ID}:{note_id}:{uuid.uuid4()}"

        plaintext = json.dumps(payload).encode("utf-8")
        associated_data = note_id.encode("utf-8")
        ciphertext = self._crypto.encrypt(plaintext, associated_data)

        conn = self._get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO queue_items
                (note_id, idempotency_key, mode, ciphertext, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'queued', datetime('now'), datetime('now'))
            """,
            (note_id, idempotency_key, mode, ciphertext),
        )
        conn.commit()
        logger.info("Enqueued note_id=%s", note_id[:8])
        return idempotency_key

    def get_pending(self, limit: int = 10) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT note_id, idempotency_key, mode, ciphertext, retry_count, created_at
            FROM queue_items
            WHERE status = 'queued'
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def decrypt_payload(self, note_id: str, ciphertext: bytes) -> dict:
        associated_data = note_id.encode("utf-8")
        plaintext = self._crypto.decrypt(ciphertext, associated_data)
        return json.loads(plaintext)

    def mark_syncing(self, note_id: str) -> None:
        conn = self._get_conn()
        conn.execute(
            "UPDATE queue_items SET status='syncing', updated_at=datetime('now') WHERE note_id=?",
            (note_id,),
        )
        conn.commit()

    def mark_synced(self, note_id: str) -> None:
        conn = self._get_conn()
        conn.execute(
            "UPDATE queue_items SET status='synced', updated_at=datetime('now') WHERE note_id=?",
            (note_id,),
        )
        conn.commit()

    def mark_failed(self, note_id: str, reason: str) -> None:
        conn = self._get_conn()
        conn.execute(
            """
            UPDATE queue_items
            SET status='failed', fail_reason=?, retry_count=retry_count+1, updated_at=datetime('now')
            WHERE note_id=?
            """,
            (reason, note_id),
        )
        conn.commit()

    def reset_for_retry(self, note_id: str) -> None:
        """Reset a failed item back to queued for retry."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE queue_items SET status='queued', updated_at=datetime('now') WHERE note_id=?",
            (note_id,),
        )
        conn.commit()

    def log_sync_attempt(
        self,
        note_id: str,
        success: bool,
        response_code: int | None = None,
        error_message: str | None = None,
        duration_ms: int | None = None,
    ) -> None:
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO sync_attempts (note_id, success, response_code, error_message, duration_ms)
            VALUES (?, ?, ?, ?, ?)
            """,
            (note_id, 1 if success else 0, response_code, error_message, duration_ms),
        )
        conn.commit()

    def get_status_counts(self) -> dict[str, int]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM queue_items GROUP BY status"
        ).fetchall()
        return {r["status"]: r["cnt"] for r in rows}

    def get_all_items_metadata(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT note_id, idempotency_key, mode, status, fail_reason,
                   created_at, updated_at, retry_count
            FROM queue_items
            ORDER BY created_at DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_decrypted(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT note_id, ciphertext, mode, status, created_at FROM queue_items ORDER BY created_at DESC"
        ).fetchall()

        results = []
        for r in rows:
            try:
                payload = self.decrypt_payload(r["note_id"], r["ciphertext"])
                results.append({
                    "note_id": r["note_id"],
                    "mode": r["mode"],
                    "status": r["status"],
                    "created_at": r["created_at"],
                    **payload,
                })
            except Exception:
                logger.exception("Failed to decrypt note_id=%s", r["note_id"][:8])
                results.append({
                    "note_id": r["note_id"],
                    "mode": r["mode"],
                    "status": r["status"],
                    "created_at": r["created_at"],
                    "error": "Decryption failed",
                })
        return results
