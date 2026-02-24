"""Prescription-from-image endpoint."""

from __future__ import annotations

import base64
import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from cloud.auth import get_current_user
from cloud.services.prescription_service import prescription_from_image
from shared.schemas import PrescriptionFromImageRequest, PrescriptionFromImageResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["prescription"])

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/v1/prescription-from-image", response_model=PrescriptionFromImageResponse)
async def prescription_from_image_endpoint(
    req: PrescriptionFromImageRequest,
    user: dict = Depends(get_current_user),
):
    """Extract medications from a prescription/handwritten image."""
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
    medications, raw_text, model_info = await prescription_from_image(image_bytes)
    timing_ms = int((time.perf_counter() - start) * 1000)

    return PrescriptionFromImageResponse(
        medications=medications,
        raw_text=raw_text,
        model_info=model_info,
        timing_ms=timing_ms,
    )
