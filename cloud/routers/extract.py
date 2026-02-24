from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from cloud.auth import get_current_user
from cloud.config import Settings, get_settings
from cloud.services.bigquery_service import log_extraction_metrics, log_usage_metrics
from cloud.services.extraction import cloud_extract
from cloud.services.firestore_service import save_encounter
from shared.schemas import ExtractRequest, ExtractResponse, Mode, StructuredResult
from shared.validator import validate_and_repair

logger = logging.getLogger(__name__)
router = APIRouter(tags=["extract"])


@router.post("/v1/extract", response_model=ExtractResponse)
async def extract(
    req: ExtractRequest,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    if req.mode == Mode.demo and not settings.DEMO_MODE_ENABLED:
        raise HTTPException(status_code=403, detail="Demo mode disabled")
    if req.mode == Mode.prod and not settings.PROD_MODE_ENABLED:
        raise HTTPException(status_code=403, detail="Prod mode disabled")
    if req.mode == Mode.prod and user["is_anonymous"]:
        raise HTTPException(status_code=403, detail="Anonymous auth not allowed in prod mode")

    start = time.perf_counter()

    record, model_info = await cloud_extract(req.note_text, req.locale)
    record, flags = validate_and_repair(record, req.note_text, locale=req.locale)

    timing_ms = int((time.perf_counter() - start) * 1000)

    result = StructuredResult(
        note_id=req.note_id,
        record=record,
        flags=flags,
        model_info=model_info,
    )

    try:
        await save_encounter(user["uid"], req.mode, result)
    except Exception:
        logger.exception("Firestore write failed for note_id_hash=%s", req.note_id[:8])

    try:
        await log_extraction_metrics(
            uid_hash=user["uid_hash"],
            note_id=req.note_id,
            mode=req.mode.value,
            timing_ms=timing_ms,
            completeness_score=flags.completeness_score,
            missing_fields_count=len(flags.missing_fields),
            contradictions_count=len(flags.contradictions),
            model_version=model_info.version,
            schema_version=req.schema_version,
        )
        await log_usage_metrics(
            uid_hash=user["uid_hash"],
            mode=req.mode.value,
            action_type="extract",
            timing_ms=timing_ms,
        )
    except Exception:
        logger.exception("BigQuery write failed")

    return ExtractResponse(
        record=record,
        flags=flags,
        model_info=model_info,
        timing_ms=timing_ms,
    )
