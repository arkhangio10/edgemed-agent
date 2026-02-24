"""Extract medications from prescription images. Uses Google API key when set."""

from __future__ import annotations

import json
import logging
import time

from cloud.config import get_settings
from shared.schemas import Medication, ModelInfo

logger = logging.getLogger(__name__)

EXTRACT_MEDICATIONS_PROMPT = """This image shows a prescription or medication list (possibly handwritten).
Extract every medication you can read. For each one provide:
- name (required)
- dose (if visible, e.g. "20mg")
- frequency (if visible, e.g. "daily", "BID", "TID")
- route (if visible, e.g. "oral", "IV")

Respond with a JSON array only, no other text. Example:
[{"name": "Omeprazole", "dose": "20mg", "frequency": "daily", "route": "oral"}, {"name": "Metformin", "dose": "500mg", "frequency": "BID", "route": "oral"}]
If you cannot read any medications, return: []"""

_vertex_initialized = False
_vertex_model = None


def _get_vertex_model():
    global _vertex_initialized, _vertex_model
    if _vertex_model is not None:
        return _vertex_model
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel, Part
        settings = get_settings()
        if not _vertex_initialized:
            vertexai.init(
                project=settings.GOOGLE_CLOUD_PROJECT or settings.PROJECT_ID,
                location=settings.MEDGEMMA_REGION,
            )
            _vertex_initialized = True
        _vertex_model = GenerativeModel("gemini-2.5-flash")
        return _vertex_model
    except Exception:
        logger.exception("Vertex model not available for prescription")
        return None


def _parse_medications_json(raw: str) -> list[Medication]:
    """Parse model output into list of Medication. Tolerant of extra fields."""
    raw = raw.strip()
    # Try to find a JSON array in the response
    start = raw.find("[")
    if start == -1:
        return []
    depth = 0
    end = -1
    for i in range(start, len(raw)):
        if raw[i] == "[":
            depth += 1
        elif raw[i] == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        return []
    try:
        arr = json.loads(raw[start:end])
    except json.JSONDecodeError:
        return []
    meds = []
    for item in arr:
        if isinstance(item, dict):
            meds.append(Medication(
                name=item.get("name") or item.get("medication") or "unknown",
                dose=item.get("dose"),
                frequency=item.get("frequency"),
                route=item.get("route"),
                status=item.get("status"),
            ))
        elif isinstance(item, str):
            meds.append(Medication(name=item))
    return meds


async def prescription_from_image(
    image_bytes: bytes,
) -> tuple[list[Medication], str | None, ModelInfo]:
    """Extract medications from prescription image. Uses GOOGLE_API_KEY when set; else Vertex."""
    start = time.perf_counter()
    settings = get_settings()
    raw_text = None
    medications = []

    try:
        if settings.GOOGLE_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel("gemini-2.5-flash")
            image_part = {"mime_type": "image/jpeg", "data": image_bytes}
            response = model.generate_content(
                [image_part, EXTRACT_MEDICATIONS_PROMPT],
                generation_config={"temperature": 0.1, "max_output_tokens": 1024},
            )
            raw_text = (response.text or "").strip()
            medications = _parse_medications_json(raw_text)
        else:
            from vertexai.generative_models import Part
            model = _get_vertex_model()
            if model is None:
                return [], None, ModelInfo(name="none", version="", runtime="cloud")
            part = Part.from_data(data=image_bytes, mime_type="image/jpeg")
            response = model.generate_content(
                [part, Part.from_text(EXTRACT_MEDICATIONS_PROMPT)],
                generation_config={"temperature": 0.1, "max_output_tokens": 1024},
            )
            raw_text = (response.text or "").strip()
            medications = _parse_medications_json(raw_text)
    except Exception:
        logger.exception("Prescription extraction failed")
        raw_text = None
        medications = []

    timing_ms = int((time.perf_counter() - start) * 1000)
    return medications, raw_text, ModelInfo(name="gemini", version="2.5-flash", runtime="cloud")
