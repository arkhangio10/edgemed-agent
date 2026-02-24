"""Local MedGemma extraction using Hugging Face transformers.

Loads google/medgemma-4b-it (or configured model) and exposes the same
interface as LocalExtractor so callers don't need to change.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from shared.schemas import Allergy, ClinicalRecord, Medication, Problem

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "shared" / "prompts"


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


def _parse_record(data: dict) -> ClinicalRecord:
    """Parse raw JSON into ClinicalRecord."""
    data.pop("confidence_by_field", None)

    meds = [
        Medication(**m) if isinstance(m, dict) else Medication(name=str(m))
        for m in data.get("medications", [])
    ]
    allergies = [
        Allergy(**a) if isinstance(a, dict) else Allergy(substance=str(a))
        for a in data.get("allergies", [])
    ]
    problems = [
        Problem(**p) if isinstance(p, dict) else Problem(description=str(p))
        for p in data.get("assessment", [])
    ]

    return ClinicalRecord(
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


class MedGemmaExtractor:
    """HuggingFace-based MedGemma extractor for local offline use."""

    def __init__(self, model_id: str = "google/medgemma-1.5-4b-it", device: str = "cuda"):
        self.model_id = model_id
        self.device = device
        self._pipeline = None
        self.model_loaded = False
        self._load_model()

    def _load_model(self) -> None:
        """Lazy-load model and tokenizer via transformers pipeline."""
        try:
            import torch
            from transformers import pipeline as hf_pipeline

            logger.info("Loading MedGemma model '%s' on device '%s' ...", self.model_id, self.device)

            # Determine dtype based on device
            dtype = torch.bfloat16 if self.device == "cuda" and torch.cuda.is_available() else torch.float32
            actual_device = self.device if self.device == "cuda" and torch.cuda.is_available() else "cpu"

            self._pipeline = hf_pipeline(
                "text-generation",
                model=self.model_id,
                torch_dtype=dtype,
                device_map=actual_device if actual_device == "cuda" else None,
                device=None if actual_device == "cuda" else actual_device,
            )
            self.model_loaded = True
            logger.info("MedGemma model loaded successfully on %s", actual_device)
        except Exception:
            logger.exception("Failed to load MedGemma model '%s'", self.model_id)
            self.model_loaded = False

    def _generate(self, prompt: str, max_new_tokens: int = 4096) -> str:
        """Generate text from the loaded model."""
        if self._pipeline is None:
            raise RuntimeError("MedGemma model not loaded")

        messages = [
            {"role": "user", "content": prompt},
        ]

        output = self._pipeline(
            messages,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=0.1,
        )
        # Extract generated text from pipeline output
        generated = output[0]["generated_text"]
        # If pipeline returns messages format, get the assistant's last message
        if isinstance(generated, list):
            return generated[-1]["content"]
        # If it returns the full text including the prompt, strip the prompt
        if isinstance(generated, str) and generated.startswith(prompt):
            return generated[len(prompt):]
        return str(generated)

    def extract(self, note_text: str, locale: str = "en") -> ClinicalRecord:
        """Extract structured data from clinical note using MedGemma."""
        system_prompt = _load_prompt("extract_system.txt")
        user_prompt = _load_prompt("extract_user.txt").format(
            note_text=note_text, locale=locale
        )
        full_prompt = system_prompt + "\n\n" + user_prompt

        if not self.model_loaded:
            logger.warning("MedGemma not loaded, returning empty record")
            return ClinicalRecord()

        try:
            raw_text = self._generate(full_prompt)
            data = _extract_json(raw_text)
            return _parse_record(data)
        except Exception:
            logger.exception("MedGemma extraction failed, returning empty record")
            return ClinicalRecord()

    def repair_fields(
        self,
        note_text: str,
        current_record: ClinicalRecord,
        fields_to_repair: list[str],
        locale: str = "en",
    ) -> dict[str, Any]:
        """Re-extract only specified fields using MedGemma."""
        repair_prompt_template = _load_prompt("repair_prompt.txt")
        prompt = repair_prompt_template.format(
            current_record_json=current_record.model_dump_json(indent=2),
            fields_to_repair=", ".join(fields_to_repair),
            issues="Missing or contradictory fields",
            note_text=note_text,
        )

        if not self.model_loaded:
            return {}

        try:
            raw_text = self._generate(prompt, max_new_tokens=2048)
            return _extract_json(raw_text)
        except Exception:
            logger.exception("MedGemma repair extraction failed")
            return {}
