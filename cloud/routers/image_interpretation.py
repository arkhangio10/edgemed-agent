"""Image interpretation endpoint."""

from __future__ import annotations

import base64
import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from cloud.auth import get_current_user
from cloud.config import get_settings
from cloud.services.image_interpretation import interpret_image
from shared.schemas import InterpretImageRequest, InterpretImageResponse, ModelInfo

logger = logging.getLogger(__name__)
router = APIRouter(tags=["image"])

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_PREFIX = "image/"


@router.post("/v1/interpret-image", response_model=InterpretImageResponse)
async def interpret_image_endpoint(
    req: InterpretImageRequest,
    user: dict = Depends(get_current_user),
):
    """Interpret a medical image for documentation (no diagnosis)."""
    try:
        image_bytes = base64.b64decode(req.image_base64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Image too large (max {MAX_IMAGE_BYTES // (1024*1024)} MB)",
        )

    start = time.perf_counter()
    interpretation, model_info = await interpret_image(
        image_bytes,
        prompt_override=req.prompt_override,
        mime_type=req.mime_type,
    )
    timing_ms = int((time.perf_counter() - start) * 1000)

    return InterpretImageResponse(
        interpretation=interpretation,
        model_info=model_info,
        timing_ms=timing_ms,
    )
