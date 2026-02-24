from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from cloud.auth import get_current_user
from cloud.config import Settings, get_settings
from cloud.services.bigquery_service import log_usage_metrics
from cloud.services.chat_service import cloud_chat
from shared.schemas import ChatRequest, ChatResponse, Mode

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/v1/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    if req.mode == Mode.demo and req.note_text is not None:
        raise HTTPException(
            status_code=400,
            detail="note_text must be null in demo mode",
        )
    if req.mode == Mode.prod and user["is_anonymous"]:
        raise HTTPException(status_code=403, detail="Anonymous auth not allowed in prod mode")

    start = time.perf_counter()

    answer, grounded_on, safety_notes = await cloud_chat(
        question=req.question,
        record=req.record,
        note_text=req.note_text if req.mode == Mode.prod else None,
    )

    timing_ms = int((time.perf_counter() - start) * 1000)

    try:
        await log_usage_metrics(
            uid_hash=user["uid_hash"],
            mode=req.mode.value,
            action_type="chat",
            timing_ms=timing_ms,
        )
    except Exception:
        logger.exception("BigQuery write failed")

    return ChatResponse(
        answer=answer,
        grounded_on=grounded_on,
        safety_notes=safety_notes,
        timing_ms=timing_ms,
    )
