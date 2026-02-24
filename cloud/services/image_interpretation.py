"""Interpret medical images. Uses only MedGemma 1.5 4B (multimodal). No Gemini fallback."""

from __future__ import annotations

import base64
import logging
import time

from cloud.config import get_settings
from shared.schemas import ModelInfo

logger = logging.getLogger(__name__)

DEFAULT_PROMPT = (
    "Describe the visible findings in this medical image for documentation purposes. "
    "Focus on what is visible (e.g., structures, lesions, text if any). "
    "Do NOT provide a diagnosis or medical advice. "
    "Output plain text suitable for clinical documentation."
)


def _medgemma_vision(image_bytes: bytes, prompt: str, mime_type: str = "image/jpeg") -> str | None:
    """Use MedGemma multimodal endpoint (Model Garden chatCompletions format)."""
    try:
        from cloud.services.extraction import _get_medgemma_endpoint
        endpoint = _get_medgemma_endpoint()
        if endpoint is None:
            return None
        b64 = base64.b64encode(image_bytes).decode("ascii")
        # MedGemma Model Garden expects chatCompletions with messages; image as data URL
        data_url = f"data:{mime_type};base64,{b64}"
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ]
        instance = {
            "@requestFormat": "chatCompletions",
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0,
        }
        response = endpoint.predict(instances=[instance], use_dedicated_endpoint=True)
        if not response.predictions:
            return None
        # Predictions can be list (one per instance) or single dict for chatCompletions
        raw = response.predictions[0] if isinstance(response.predictions, list) else response.predictions
        if isinstance(raw, str):
            return raw
        if isinstance(raw, dict):
            choices = raw.get("choices")
            if choices and len(choices) > 0:
                msg = choices[0].get("message") or choices[0]
                content = msg.get("content") if isinstance(msg, dict) else None
                if content:
                    return str(content)
            out = raw.get("output") or raw.get("text") or raw.get("content") or raw.get("generated_text")
            return str(out) if out else None
        return None
    except Exception:
        logger.exception("MedGemma vision not available or failed")
        return None


async def interpret_image(
    image_bytes: bytes,
    prompt_override: str | None = None,
    mime_type: str = "image/jpeg",
) -> tuple[str, ModelInfo]:
    """Interpret a medical image. Only MedGemma 1.5 4B — no Gemini."""
    start = time.perf_counter()
    prompt = prompt_override or DEFAULT_PROMPT
    if mime_type not in ("image/jpeg", "image/png", "image/webp"):
        mime_type = "image/jpeg"

    settings = get_settings()
    text = None
    model_name = "none"
    model_version = ""

    # Solo MedGemma 1.5 4B multimodal (no usamos Gemini para imágenes médicas)
    if settings.MEDGEMMA_ENDPOINT_ID:
        text = _medgemma_vision(image_bytes, prompt, mime_type)
        if text:
            model_name = "medgemma"
            model_version = getattr(settings, "MEDGEMMA_VERSION", "1.5")

    if text is None:
        text = (
            "Interpretación de imágenes médicas no disponible: se requiere MedGemma 1.5 4B (endpoint multimodal). "
            "No se usa Gemini para este flujo. Configure EDGEMED_MEDGEMMA_ENDPOINT_ID con un endpoint activo de MedGemma 1.5 4B en Vertex AI Model Garden."
        )

    timing_ms = int((time.perf_counter() - start) * 1000)
    return text, ModelInfo(name=model_name, version=model_version, runtime="cloud")
