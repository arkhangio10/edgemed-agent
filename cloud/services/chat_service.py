"""Grounded clinical Q&A service. Uses Google API key when set (chat only)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from shared.schemas import ClinicalRecord

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "shared" / "prompts"


def _load_prompt(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8")


def _extract_chat_text(response, source: str) -> str:
    """Extract text from Gemini/Vertex response; handle blocked or empty."""
    try:
        if hasattr(response, "text") and response.text:
            return response.text.strip()
    except (ValueError, AttributeError):
        pass
    try:
        if hasattr(response, "candidates") and response.candidates:
            for c in response.candidates:
                if getattr(c, "content", None) and getattr(c.content, "parts", None):
                    parts = [p for p in c.content.parts if getattr(p, "text", None)]
                    if parts:
                        return " ".join(p.text for p in parts).strip()
    except Exception:
        logger.debug("Could not get text from %s response candidates", source)
    return ""


async def cloud_chat(
    question: str,
    record: ClinicalRecord,
    note_text: Optional[str] = None,
) -> tuple[str, list[str], list[str]]:
    """Answer a question grounded on the structured record (and optionally the note).

    Uses GOOGLE_API_KEY (Gemini API) when set; otherwise Vertex AI.
    Returns (answer, grounded_on, safety_notes).
    """
    grounded_on = ["record"]
    context = f"STRUCTURED RECORD:\n{record.model_dump_json(indent=2)}"

    if note_text:
        context += f"\n\nORIGINAL NOTE:\n{note_text}"
        grounded_on.append("note")

    system_prompt = _load_prompt("chat_system.txt")
    full_prompt = (
        f"{system_prompt}\n\n{context}\n\nQUESTION: {question}\n\nANSWER:"
    )

    try:
        from cloud.config import get_settings
        settings = get_settings()

        if settings.GOOGLE_API_KEY:
            logger.info("Chat using Gemini API (API key)")
            import google.generativeai as genai
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(
                full_prompt,
                generation_config={"temperature": 0.2, "max_output_tokens": 1024},
            )
            answer = _extract_chat_text(response, "genai")
        else:
            logger.info("Chat using Vertex AI Gemini")
            import vertexai
            from vertexai.generative_models import GenerativeModel, Part
            vertexai.init(
                project=settings.GOOGLE_CLOUD_PROJECT or settings.PROJECT_ID,
                location=settings.MEDGEMMA_REGION,
            )
            model = GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(
                [Part.from_text(full_prompt)],
                generation_config={"temperature": 0.2, "max_output_tokens": 1024},
            )
            answer = _extract_chat_text(response, "vertex")
        if not answer:
            raise ValueError("Empty model response")
    except Exception:
        logger.exception("Chat model call failed, using fallback")
        answer = _fallback_chat(question, record)

    safety_notes = _check_safety(record, question)
    return answer, grounded_on, safety_notes


def _fallback_chat(question: str, record: ClinicalRecord) -> str:
    """Rule-based fallback when the model is unavailable."""
    q_lower = question.lower()
    if "allerg" in q_lower:
        if record.allergies:
            items = ", ".join(a.substance for a in record.allergies)
            return f"Documented allergies: {items}"
        return "No allergies documented in this encounter."
    if "medication" in q_lower or "med" in q_lower:
        if record.medications:
            items = ", ".join(
                f"{m.name} {m.dose or ''} {m.frequency or ''}".strip()
                for m in record.medications
            )
            return f"Documented medications: {items}"
        return "No medications documented in this encounter."
    if "assessment" in q_lower or "diagnosis" in q_lower or "problem" in q_lower:
        if record.assessment:
            items = ", ".join(p.description for p in record.assessment)
            return f"Assessment/problems: {items}"
        return "No assessment documented in this encounter."
    if "plan" in q_lower:
        return record.plan or "No plan documented in this encounter."

    return (
        "I can answer questions about the documented allergies, medications, "
        "assessment, and plan. Please ask a more specific question."
    )


def _check_safety(record: ClinicalRecord, question: str) -> list[str]:
    notes: list[str] = []
    if record.red_flags:
        notes.append(
            f"Red flags documented: {', '.join(record.red_flags)}. "
            "Please review before making clinical decisions."
        )
    if record.allergies and record.medications:
        allergy_substances = {a.substance.lower() for a in record.allergies}
        for med in record.medications:
            if med.name.lower() in allergy_substances:
                notes.append(
                    f"Potential allergy-medication conflict: {med.name} "
                    f"is listed in both medications and allergies."
                )
    return notes
