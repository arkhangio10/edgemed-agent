"""Cloud extraction service using Vertex AI with medical prompts.

Supports two modes:
1. MedGemma via deployed Vertex AI endpoint (when MEDGEMMA_ENDPOINT_ID is set)
2. Gemini 1.5 Flash as fallback (always available)
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import vertexai
from vertexai.generative_models import GenerativeModel, Part

from cloud.config import get_settings
from shared.schemas import (
    Allergy,
    ClinicalRecord,
    Medication,
    ModelInfo,
    Problem,
)

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "shared" / "prompts"

# Cached model instances
_gemini_model: GenerativeModel | None = None
_medgemma_endpoint = None
_active_model_name: str = "gemini"
_vertex_initialized: bool = False


def _init_vertex() -> None:
    """Initialize Vertex AI SDK once."""
    global _vertex_initialized
    if _vertex_initialized:
        return
    settings = get_settings()
    project = settings.GOOGLE_CLOUD_PROJECT or settings.PROJECT_ID
    vertexai.init(project=project, location=settings.MEDGEMMA_REGION)
    _vertex_initialized = True
    logger.info("Vertex AI initialized (project=%s, region=%s)", project, settings.MEDGEMMA_REGION)


def _get_medgemma_endpoint():
    """Get the deployed MedGemma endpoint (if configured)."""
    global _medgemma_endpoint
    if _medgemma_endpoint is not None:
        return _medgemma_endpoint

    settings = get_settings()
    if not settings.MEDGEMMA_ENDPOINT_ID:
        return None

    try:
        _init_vertex()
        from google.cloud.aiplatform import Endpoint

        project = settings.GOOGLE_CLOUD_PROJECT or settings.PROJECT_ID
        endpoint_name = (
            f"projects/{project}/locations/{settings.MEDGEMMA_REGION}"
            f"/endpoints/{settings.MEDGEMMA_ENDPOINT_ID}"
        )
        _medgemma_endpoint = Endpoint(endpoint_name=endpoint_name)
        logger.info("MedGemma endpoint loaded: %s", settings.MEDGEMMA_ENDPOINT_ID)
        return _medgemma_endpoint
    except Exception:
        logger.exception("Failed to load MedGemma endpoint")
        return None


def _get_gemini_model() -> GenerativeModel | None:
    """Get Gemini model (always-available fallback)."""
    global _gemini_model
    if _gemini_model is None:
        try:
            _init_vertex()
            _gemini_model = GenerativeModel("gemini-2.5-flash")
            logger.info("Gemini 2.5 Flash loaded")
        except Exception:
            logger.exception("Failed to load Gemini model")
    return _gemini_model


def _generate_with_medgemma(prompt: str, max_tokens: int = 4096) -> str | None:
    """Generate text using the deployed MedGemma endpoint (Model Garden chatCompletions)."""
    endpoint = _get_medgemma_endpoint()
    if endpoint is None:
        return None

    try:
        messages = [{"role": "user", "content": prompt}]
        instance = {
            "@requestFormat": "chatCompletions",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.1,
        }
        response = endpoint.predict(
            instances=[instance],
            use_dedicated_endpoint=True,
        )
        predictions = response.predictions
        if not predictions:
            return None
        raw = predictions[0] if isinstance(predictions, list) else predictions
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
        logger.exception("MedGemma endpoint prediction failed")
        return None


def _generate_with_gemini(prompt: str, max_tokens: int = 4096) -> str | None:
    """Generate text using Gemini 1.5 Flash."""
    model = _get_gemini_model()
    if model is None:
        return None
    try:
        response = model.generate_content(
            [Part.from_text(prompt)],
            generation_config={"temperature": 0.1, "max_output_tokens": max_tokens},
        )
        return response.text
    except Exception:
        logger.exception("Gemini generation failed")
        return None


def _load_prompt(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text(encoding="utf-8")


def _extract_json(text: str) -> dict:
    """Extract JSON object from model response, handling markdown fences."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    raise ValueError("No JSON object found in response")


def _parse_record(data: dict) -> tuple[ClinicalRecord, dict[str, str]]:
    """Parse raw JSON into ClinicalRecord and confidence map."""
    confidence = data.pop("confidence_by_field", {})

    meds = []
    for m in data.get("medications", []):
        if isinstance(m, dict):
            meds.append(Medication(
                name=m.get("name", "unknown"),
                dose=m.get("dose"),
                frequency=m.get("frequency"),
                route=m.get("route"),
                status=m.get("status"),
            ))
        else:
            meds.append(Medication(name=str(m)))

    allergies = []
    for a in data.get("allergies", []):
        if isinstance(a, dict):
            allergies.append(Allergy(
                substance=a.get("substance", "unknown"),
                reaction=a.get("reaction"),
                severity=a.get("severity"),
            ))
        else:
            allergies.append(Allergy(substance=str(a)))

    problems = []
    for p in data.get("assessment", []):
        if isinstance(p, dict):
            problems.append(Problem(
                description=p.get("description", str(p)),
                status=p.get("status"),
                icd10=p.get("icd10"),
                confidence=p.get("confidence"),
            ))
        else:
            problems.append(Problem(description=str(p)))

    record = ClinicalRecord(
        chief_complaint=data.get("chief_complaint"),
        hpi=data.get("hpi"),
        assessment=problems,
        plan=data.get("plan"),
        medications=meds,
        allergies=allergies,
        red_flags=data.get("red_flags", []),
        follow_up=data.get("follow_up"),
        patient_summary_plain_language=data.get("patient_summary_plain_language"),
    )
    return record, confidence


def _filter_denied_red_flags(record: ClinicalRecord, note_text: str) -> None:
    """Remove red_flags that correspond to symptoms the patient denies."""
    if not record.red_flags or not note_text:
        return

    lower_note = note_text.lower()
    denial_patterns = [
        r"denies\s+",
        r"denied\s+",
        r"no\s+",
        r"negative\s+for\s+",
        r"without\s+",
        r"niega\s+",
        r"sin\s+",
        r"no\s+refiere\s+",
    ]
    import re as _re
    denial_regex = "|".join(denial_patterns)

    filtered = []
    for flag in record.red_flags:
        flag_terms = [t.strip().lower() for t in _re.split(r"[—–\-,]", flag) if len(t.strip()) > 2]
        is_denied = False
        for term in flag_terms:
            # Check if in the note this term appears after a denial word
            pattern = rf"(?:{denial_regex})[^.\n]{{0,40}}{_re.escape(term)}"
            if _re.search(pattern, lower_note):
                is_denied = True
                break
        if not is_denied:
            filtered.append(flag)

    record.red_flags = filtered


async def cloud_extract(
    note_text: str, locale: str = "en"
) -> tuple[ClinicalRecord, ModelInfo]:
    """Run extraction via Vertex AI.

    Priority: MedGemma endpoint (if deployed) → Gemini 1.5 Flash (fallback) → Demo fallback.
    """
    system_prompt = _load_prompt("extract_system.txt")
    user_prompt = _load_prompt("extract_user.txt").format(
        note_text=note_text, locale=locale
    )
    full_prompt = system_prompt + "\n\n" + user_prompt

    settings = get_settings()

    # Try MedGemma endpoint first
    raw_text = None
    used_model = "gemini"
    used_version = "1.5-flash"

    if settings.MEDGEMMA_ENDPOINT_ID:
        raw_text = _generate_with_medgemma(full_prompt)
        if raw_text:
            used_model = "medgemma"
            used_version = settings.MEDGEMMA_VERSION

    # Fall back to Gemini
    if raw_text is None:
        raw_text = _generate_with_gemini(full_prompt)

    model_info = ModelInfo(name=used_model, version=used_version, runtime="cloud")

    if raw_text is not None:
        try:
            data = _extract_json(raw_text)
            record, confidence = _parse_record(data)
            _filter_denied_red_flags(record, note_text)
            return record, model_info
        except Exception:
            logger.exception("Extraction parse failed")

    # ── Demo fallback: smart extraction from note text ───────────────────
    if settings.DEMO_MODE_ENABLED:
        logger.info("Using demo fallback extraction")
        record = _demo_extract(note_text)
        _filter_denied_red_flags(record, note_text)
        return record, ModelInfo(name="demo-fallback", version="1.0", runtime="cloud")

    logger.warning("No model available, returning empty record")
    return ClinicalRecord(), model_info


def _demo_extract(note_text: str) -> ClinicalRecord:
    """Best-effort rule-based extraction for demo mode.

    Parses common clinical note patterns so the frontend always has data
    to display, even when Vertex AI is not available.
    """
    import re as _re

    text = note_text
    lower = text.lower()

    # Chief complaint
    cc = None
    cc_match = _re.search(
        r"(?:chief\s+complaint|motivo\s+de\s+consulta|cc)[:\s]*[\"']?(.+?)[\"']?\s*(?:\n|$)",
        text, _re.IGNORECASE,
    )
    if cc_match:
        cc = cc_match.group(1).strip().rstrip('"').rstrip("'")

    # HPI
    hpi = None
    hpi_match = _re.search(
        r"(?:hpi|historia?|history\s+of\s+present\s+illness)[:\s]*(.+?)(?=\n[A-Z]|\nROS|\nPMH|\nMed|\nAll|\nSocial|\nVital|\nPhysical|\nAssess|\nPlan|\Z)",
        text, _re.IGNORECASE | _re.DOTALL,
    )
    if hpi_match:
        hpi = hpi_match.group(1).strip()

    # Medications
    meds = []
    med_section = _re.search(
        r"(?:medications?|medicamentos?)[:\s]*(.+?)(?=\n[A-Z]|\nAll|\nSocial|\nVital|\nPhysical|\nAssess|\Z)",
        text, _re.IGNORECASE | _re.DOTALL,
    )
    if med_section:
        for m in _re.findall(r"([A-Z][a-záéíóú]+(?:\s+\d+\s*mg)?(?:\s+\w+)?)", med_section.group(1)):
            parts = m.strip().split()
            name = parts[0]
            dose = parts[1] if len(parts) > 1 else None
            freq = parts[2] if len(parts) > 2 else None
            meds.append(Medication(name=name, dose=dose, frequency=freq))

    # Allergies
    allergies = []
    allergy_section = _re.search(
        r"(?:allergies?|alergias?)[:\s]*(.+?)(?=\n[A-Z]|\nSocial|\nVital|\nPhysical|\nAssess|\Z)",
        text, _re.IGNORECASE | _re.DOTALL,
    )
    if allergy_section:
        for a in _re.split(r"[,;]", allergy_section.group(1)):
            a = a.strip()
            if a and len(a) > 1:
                reaction_match = _re.search(r"\((.+?)\)", a)
                substance = _re.sub(r"\(.+?\)", "", a).strip()
                reaction = reaction_match.group(1) if reaction_match else None
                if substance:
                    allergies.append(Allergy(substance=substance, reaction=reaction))

    # Assessment/Plan
    plan = None
    problems = []
    plan_match = _re.search(
        r"(?:assessment\s*/?\s*plan|plan|evaluación)[:\s]*(.+?)(?=\nFollow|\nSeguimiento|\Z)",
        text, _re.IGNORECASE | _re.DOTALL,
    )
    if plan_match:
        plan_text = plan_match.group(1).strip()
        plan = plan_text
        for line in plan_text.split("\n"):
            line = line.strip()
            desc_match = _re.match(r"^\d+[\.\)]\s*(.+?)(?:\s*[-–—]\s*|$)", line)
            if desc_match:
                desc = desc_match.group(1).strip()
                if desc:
                    problems.append(Problem(description=desc))

    # Red flags
    red_flags = []
    if "chest pain" in lower or "dolor torácico" in lower or "dolor en el pecho" in lower:
        red_flags.append("Chest pain — evaluate for acute coronary syndrome")
    if _re.search(r"bp\s*\d{3}/\d{2,3}", lower) or "poorly controlled" in lower:
        red_flags.append("Poorly controlled hypertension")
    if "shortness of breath" in lower or "disnea" in lower:
        red_flags.append("Shortness of breath — assess respiratory status")

    # Follow-up
    follow_up = None
    fu_match = _re.search(
        r"(?:follow[- ]?up|seguimiento)[:\s]*(.+?)(?:\.|$)",
        text, _re.IGNORECASE,
    )
    if fu_match:
        follow_up = fu_match.group(1).strip()

    # Patient summary
    summary = None
    if cc or hpi:
        summary = f"Patient presents with {cc or 'symptoms as described'}. {hpi[:200] + '...' if hpi and len(hpi) > 200 else hpi or ''}"

    return ClinicalRecord(
        chief_complaint=cc,
        hpi=hpi,
        assessment=problems,
        plan=plan,
        medications=meds,
        allergies=allergies,
        red_flags=red_flags,
        follow_up=follow_up,
        patient_summary_plain_language=summary,
    )


class CloudRepairExtractor:
    """Implements the Extractor protocol for the repair loop."""

    def repair_fields(
        self,
        note_text: str,
        current_record: ClinicalRecord,
        fields_to_repair: list[str],
        locale: str = "en",
    ) -> dict[str, Any]:
        repair_prompt_template = _load_prompt("repair_prompt.txt")
        prompt = repair_prompt_template.format(
            current_record_json=current_record.model_dump_json(indent=2),
            fields_to_repair=", ".join(fields_to_repair),
            issues="Missing or contradictory fields",
            note_text=note_text,
        )

        settings = get_settings()

        # Try MedGemma first, then Gemini
        raw_text = None
        if settings.MEDGEMMA_ENDPOINT_ID:
            raw_text = _generate_with_medgemma(prompt, max_tokens=2048)
        if raw_text is None:
            raw_text = _generate_with_gemini(prompt, max_tokens=2048)

        if raw_text is None:
            return {}

        try:
            return _extract_json(raw_text)
        except Exception:
            logger.exception("Repair extraction failed")
            return {}
