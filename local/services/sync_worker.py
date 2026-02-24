"""Sync worker: monitors connectivity and syncs encrypted queue items to Cloud Run.

Runs as a background thread, with exponential backoff on failure.
Uses idempotency keys to guarantee exactly-once delivery.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timezone

import httpx

from local.config import LocalSettings
from local.services.queue_manager import QueueManager
from shared.schemas import SyncItem, SyncRequest

logger = logging.getLogger(__name__)


class SyncWorker:
    def __init__(self, queue_mgr: QueueManager, settings: LocalSettings):
        self._queue = queue_mgr
        self._settings = settings
        self._base_url = settings.CLOUD_API_URL.rstrip("/")
        self._running = False
        self._thread: threading.Thread | None = None
        self._backoff = settings.SYNC_INTERVAL_SECONDS
        self._min_backoff = settings.SYNC_INTERVAL_SECONDS
        self._max_backoff = 300

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Sync worker started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Sync worker stopped")

    def _run_loop(self) -> None:
        while self._running:
            try:
                if self.check_connectivity():
                    result = asyncio.run(self.sync_batch())
                    if result.get("synced_count", 0) > 0:
                        self._backoff = self._min_backoff
                    else:
                        self._backoff = min(self._backoff * 1.5, self._max_backoff)
                else:
                    self._backoff = min(self._backoff * 2, self._max_backoff)
                    logger.info("Offline. Next check in %.0fs", self._backoff)
            except Exception:
                logger.exception("Sync loop error")
                self._backoff = min(self._backoff * 2, self._max_backoff)

            time.sleep(self._backoff)

    def check_connectivity(self) -> bool:
        try:
            with httpx.Client(timeout=5) as client:
                r = client.get(f"{self._base_url}/v1/health")
                return r.status_code == 200
        except Exception:
            return False

    async def sync_batch(self) -> dict:
        """Sync a batch of pending items. Returns summary."""
        pending = self._queue.get_pending(limit=self._settings.SYNC_BATCH_SIZE)
        if not pending:
            return {"synced_count": 0, "failed_count": 0, "message": "No pending items"}

        items: list[SyncItem] = []
        note_ids: list[str] = []

        for row in pending:
            self._queue.mark_syncing(row["note_id"])
            try:
                payload = self._queue.decrypt_payload(row["note_id"], row["ciphertext"])
                raw_text = payload.pop("raw_note_text", None)
                if row["mode"] == "demo":
                    raw_text = None

                item = SyncItem(
                    note_id=row["note_id"],
                    record=payload["record"],
                    flags=payload["flags"],
                    created_at=row["created_at"],
                    schema_version="1.0.0",
                    idempotency_key=row["idempotency_key"],
                    raw_note_text=raw_text,
                )
                items.append(item)
                note_ids.append(row["note_id"])
            except Exception as e:
                logger.exception("Failed to prepare note_id=%s", row["note_id"][:8])
                self._queue.mark_failed(row["note_id"], str(e))

        if not items:
            return {"synced_count": 0, "failed_count": len(pending)}

        req = SyncRequest(
            device_id=self._settings.DEVICE_ID,
            mode=self._settings.MODE,
            items=items,
        )

        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{self._base_url}/v1/sync",
                    json=json.loads(req.model_dump_json()),
                    headers={"Content-Type": "application/json"},
                )
            duration_ms = int((time.perf_counter() - start) * 1000)
            resp = r.json()

            for nid in resp.get("synced", []):
                self._queue.mark_synced(nid)
                self._queue.log_sync_attempt(nid, success=True, response_code=r.status_code, duration_ms=duration_ms)

            for fail in resp.get("failed", []):
                nid = fail.get("note_id", "")
                reason = fail.get("reason", "unknown")
                self._queue.mark_failed(nid, reason)
                self._queue.log_sync_attempt(nid, success=False, response_code=r.status_code, error_message=reason, duration_ms=duration_ms)

            synced_count = len(resp.get("synced", []))
            failed_count = len(resp.get("failed", []))
            logger.info("Sync batch: synced=%d failed=%d timing=%dms", synced_count, failed_count, duration_ms)

            return {
                "synced_count": synced_count,
                "failed_count": failed_count,
                "timing_ms": duration_ms,
            }

        except Exception as e:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.exception("Sync request failed")
            for nid in note_ids:
                self._queue.mark_failed(nid, str(e))
                self._queue.log_sync_attempt(nid, success=False, error_message=str(e), duration_ms=duration_ms)
            return {"synced_count": 0, "failed_count": len(note_ids), "error": str(e)}
