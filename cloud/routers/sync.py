from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from cloud.auth import get_current_user
from cloud.config import Settings, get_settings
from cloud.services.bigquery_service import log_sync_metrics, log_usage_metrics
from cloud.services.firestore_service import (
    check_idempotency_key,
    save_encounter_from_sync,
    save_idempotency_key,
    save_raw_note,
)
from shared.schemas import Mode, StructuredResult, SyncRequest, SyncResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sync"])


@router.post("/v1/sync", response_model=SyncResponse)
async def sync(
    req: SyncRequest,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    if req.mode == Mode.prod and user["is_anonymous"]:
        raise HTTPException(status_code=403, detail="Anonymous auth not allowed in prod mode")

    start = time.perf_counter()
    synced: list[str] = []
    failed: list[dict] = []

    for item in req.items:
        if req.mode == Mode.demo and item.raw_note_text is not None:
            failed.append({
                "note_id": item.note_id,
                "reason": "raw_note_text must be null in demo mode",
            })
            continue

        try:
            already_exists = await check_idempotency_key(
                user["uid"], item.idempotency_key
            )
            if already_exists:
                synced.append(item.note_id)
                continue

            result = StructuredResult(
                note_id=item.note_id,
                created_at=item.created_at,
                schema_version=item.schema_version,
                record=item.record,
                flags=item.flags,
                model_info={"name": "medgemma", "version": "4b-v1.5", "runtime": "local"},
            )

            await save_encounter_from_sync(user["uid"], req.mode, result)

            if (
                req.mode == Mode.prod
                and settings.STORE_RAW_NOTES_PROD
                and item.raw_note_text is not None
            ):
                await save_raw_note(user["uid"], item.note_id, item.raw_note_text)

            await save_idempotency_key(user["uid"], item.idempotency_key, item.note_id)

            synced.append(item.note_id)
        except Exception as e:
            logger.exception("Sync failed for note_id=%s", item.note_id[:8])
            failed.append({"note_id": item.note_id, "reason": str(e)})

    timing_ms = int((time.perf_counter() - start) * 1000)

    try:
        await log_sync_metrics(
            device_id=req.device_id,
            mode=req.mode.value,
            synced_count=len(synced),
            failed_count=len(failed),
            timing_ms=timing_ms,
        )
        await log_usage_metrics(
            uid_hash=user["uid_hash"],
            mode=req.mode.value,
            action_type="sync",
            timing_ms=timing_ms,
        )
    except Exception:
        logger.exception("BigQuery write failed")

    return SyncResponse(
        synced=synced,
        failed=failed,
        timing_ms=timing_ms,
    )
