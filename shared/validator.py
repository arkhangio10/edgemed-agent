"""Agentic validation + repair loop for clinical records.

Shared by both cloud and local extraction pipelines.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Protocol

from shared.constants import (
    COMPLETENESS_THRESHOLD,
    CONFIDENCE_NUMERIC,
    CRITICAL_FIELDS,
    MAX_REPAIR_ATTEMPTS,
    REQUIRED_FIELDS,
)
from shared.schemas import ClinicalRecord, Flags

logger = logging.getLogger(__name__)


class Extractor(Protocol):
    """Interface that both cloud and local extractors must satisfy."""

    def repair_fields(
        self,
        note_text: str,
        current_record: ClinicalRecord,
        fields_to_repair: list[str],
        locale: str,
    ) -> dict[str, Any]: ...


# ── Contradiction rules ──────────────────────────────────────────────

ContradictionRule = tuple[Callable[[ClinicalRecord], bool], str]

CONTRADICTION_RULES: list[ContradictionRule] = [
    (
        lambda r: any("nkda" in a.substance.lower() for a in r.allergies)
        and len(r.allergies) > 1,
        "States NKDA (no known drug allergies) but also lists specific allergies",
    ),
    (
        lambda r: any("none" in m.name.lower() for m in r.medications)
        and len(r.medications) > 1,
        "States no medications but also lists specific medications",
    ),
    (
        lambda r: r.chief_complaint is not None
        and r.assessment
        and not _chief_complaint_addressed(r),
        "Chief complaint not addressed in assessment",
    ),
]


def _chief_complaint_addressed(r: ClinicalRecord) -> bool:
    if not r.chief_complaint or not r.assessment:
        return True
    cc_words = set(r.chief_complaint.lower().split())
    for p in r.assessment:
        desc_words = set(p.description.lower().split())
        if cc_words & desc_words:
            return True
    return False


# ── Field presence helpers ───────────────────────────────────────────

def _is_field_present(record: ClinicalRecord, field: str) -> bool:
    val = getattr(record, field, None)
    if val is None:
        return False
    if isinstance(val, list) and len(val) == 0:
        return False
    if isinstance(val, str) and val.strip() == "":
        return False
    return True


# ── Core validation ──────────────────────────────────────────────────

def validate(record: ClinicalRecord) -> Flags:
    missing: list[str] = []
    for f in REQUIRED_FIELDS:
        if not _is_field_present(record, f):
            missing.append(f)

    contradictions: list[str] = []
    for rule_fn, msg in CONTRADICTION_RULES:
        try:
            if rule_fn(record):
                contradictions.append(msg)
        except Exception:
            pass

    confidence = _compute_confidence(record)
    score = _compute_completeness(missing, confidence)

    return Flags(
        missing_fields=missing,
        contradictions=contradictions,
        confidence_by_field=confidence,
        completeness_score=round(score, 3),
    )


def _compute_confidence(record: ClinicalRecord) -> dict[str, str]:
    confidence: dict[str, str] = {}
    for f in REQUIRED_FIELDS:
        if not _is_field_present(record, f):
            confidence[f] = "low"
            continue
        val = getattr(record, f)
        if isinstance(val, list):
            confidence[f] = "high" if len(val) >= 1 else "low"
        elif isinstance(val, str):
            word_count = len(val.split())
            if word_count >= 5:
                confidence[f] = "high"
            elif word_count >= 2:
                confidence[f] = "medium"
            else:
                confidence[f] = "low"
        else:
            confidence[f] = "medium"
    return confidence


def _compute_completeness(
    missing: list[str], confidence: dict[str, str]
) -> float:
    total_required = len(REQUIRED_FIELDS)
    fields_present = total_required - len(missing)

    missing_critical = sum(1 for f in CRITICAL_FIELDS if f in missing)
    total_critical = len(CRITICAL_FIELDS)

    conf_values = [
        CONFIDENCE_NUMERIC.get(v, 0.33) for v in confidence.values()
    ]
    avg_confidence = sum(conf_values) / len(conf_values) if conf_values else 0.0

    score = (
        0.5 * (fields_present / total_required)
        + 0.3 * (1.0 - missing_critical / total_critical)
        + 0.2 * avg_confidence
    )
    return max(0.0, min(1.0, score))


# ── Repair loop ──────────────────────────────────────────────────────

def validate_and_repair(
    record: ClinicalRecord,
    note_text: str,
    extractor: Extractor | None = None,
    locale: str = "en",
    max_repairs: int = MAX_REPAIR_ATTEMPTS,
) -> tuple[ClinicalRecord, Flags]:
    """Run validation; if below threshold, attempt targeted repairs."""
    for attempt in range(max_repairs + 1):
        flags = validate(record)

        if (
            flags.completeness_score >= COMPLETENESS_THRESHOLD
            and not flags.contradictions
        ):
            break

        if attempt < max_repairs and extractor is not None:
            fields_to_fix = flags.missing_fields + [
                "contradictions"
            ] if flags.contradictions else flags.missing_fields

            if not fields_to_fix:
                break

            logger.info(
                "Repair attempt %d/%d for fields: %s",
                attempt + 1,
                max_repairs,
                fields_to_fix,
            )
            record = _apply_repair(
                record, note_text, fields_to_fix, extractor, locale
            )

    return record, flags


def _apply_repair(
    record: ClinicalRecord,
    note_text: str,
    fields_to_fix: list[str],
    extractor: Extractor,
    locale: str,
) -> ClinicalRecord:
    try:
        repaired = extractor.repair_fields(
            note_text=note_text,
            current_record=record,
            fields_to_repair=fields_to_fix,
            locale=locale,
        )
    except Exception:
        logger.exception("Repair call failed")
        return record

    data = record.model_dump()
    for field, value in repaired.items():
        if field in data and value is not None:
            if isinstance(value, str) and value.strip().lower() == "unknown":
                continue
            data[field] = value

    return ClinicalRecord.model_validate(data)
