"""Local MedGemma extraction stub.

MVP: Rule-based extraction using regex patterns and section header detection.
Interface matches the cloud extraction service exactly so MedGemma local weights
can be swapped in without changing callers.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from shared.schemas import Allergy, ClinicalRecord, Medication, Problem

logger = logging.getLogger(__name__)


class LocalExtractor:
    def __init__(self):
        self.model_loaded = False

    def extract(self, note_text: str, locale: str = "en") -> ClinicalRecord:
        """Extract structured data from clinical note text using rule-based patterns."""
        sections = self._split_sections(note_text)
        medications = self._extract_medications(note_text)
        allergies = self._extract_allergies(note_text)
        problems = self._extract_problems(sections.get("assessment", ""))
        red_flags = self._extract_red_flags(note_text)

        return ClinicalRecord(
            chief_complaint=sections.get("cc") or sections.get("chief_complaint"),
            hpi=sections.get("hpi") or sections.get("history"),
            assessment=problems,
            plan=sections.get("plan"),
            medications=medications,
            allergies=allergies,
            red_flags=red_flags,
            follow_up=sections.get("follow_up") or sections.get("follow-up"),
            patient_summary_plain_language=self._generate_summary(
                sections, medications, allergies, problems
            ),
        )

    def repair_fields(
        self,
        note_text: str,
        current_record: ClinicalRecord,
        fields_to_repair: list[str],
        locale: str = "en",
    ) -> dict[str, Any]:
        """Re-extract only specified fields."""
        full = self.extract(note_text, locale)
        result = {}
        for field in fields_to_repair:
            if field == "contradictions":
                continue
            val = getattr(full, field, None)
            if val is not None:
                if isinstance(val, list):
                    result[field] = [
                        item.model_dump() if hasattr(item, "model_dump") else item
                        for item in val
                    ]
                else:
                    result[field] = val
        return result

    def _split_sections(self, text: str) -> dict[str, str]:
        """Split note into sections by common clinical headers."""
        section_patterns = [
            (r"(?i)(?:CC|Chief\s*Complaint)\s*[:\.]\s*", "cc"),
            (r"(?i)(?:HPI|History\s*of\s*Present\s*Illness)\s*[:\.]\s*", "hpi"),
            (r"(?i)(?:History)\s*[:\.]\s*", "history"),
            (r"(?i)(?:Assessment|Dx|Diagnosis|Diagnoses)\s*[:\.]\s*", "assessment"),
            (r"(?i)(?:Plan|Treatment\s*Plan)\s*[:\.]\s*", "plan"),
            (r"(?i)(?:Follow[\s-]*Up)\s*[:\.]\s*", "follow_up"),
            (r"(?i)(?:Allergies|Allergy)\s*[:\.]\s*", "allergies_section"),
            (r"(?i)(?:Medications|Meds|Current\s*Medications)\s*[:\.]\s*", "medications_section"),
        ]

        boundaries: list[tuple[int, str]] = []
        for pattern, name in section_patterns:
            for m in re.finditer(pattern, text):
                boundaries.append((m.end(), name))

        if not boundaries:
            return {"hpi": text.strip()}

        boundaries.sort(key=lambda x: x[0])
        sections: dict[str, str] = {}
        for i, (start, name) in enumerate(boundaries):
            end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(text)
            content = text[start:end].strip()
            for pat, _ in section_patterns:
                content = re.sub(pat, "", content).strip()
            if content:
                sections[name] = content

        return sections

    def _extract_medications(self, text: str) -> list[Medication]:
        meds: list[Medication] = []
        patterns = [
            r"(?i)(\b[A-Z][a-z]+(?:\/[A-Z][a-z]+)?)\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?))\s*(?:,?\s*((?:once|twice|three\s+times|QD|BID|TID|QID|daily|weekly|PRN|as\s+needed|q\d+h)[^,\n]*))?(?:\s*(?:PO|IV|IM|SC|topical|inhaled|sublingual))?",
            r"(?i)-\s*(\b[A-Z][a-z]+(?:\/[A-Z][a-z]+)?)\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?))\s*(.*?)(?:\n|$)",
        ]
        seen_names: set[str] = set()
        for pattern in patterns:
            for m in re.finditer(pattern, text):
                name = m.group(1).strip()
                if name.lower() in seen_names or name.lower() in ("the", "and", "with", "for"):
                    continue
                seen_names.add(name.lower())
                dose = m.group(2).strip() if m.group(2) else None
                freq = m.group(3).strip() if len(m.groups()) >= 3 and m.group(3) else None
                meds.append(Medication(name=name, dose=dose, frequency=freq))
        return meds

    def _extract_allergies(self, text: str) -> list[Allergy]:
        allergies: list[Allergy] = []
        nkda = re.search(r"(?i)\bNKDA\b|no\s+known\s+(?:drug\s+)?allergies", text)
        if nkda:
            allergies.append(Allergy(substance="NKDA", reaction=None))
            return allergies

        patterns = [
            r"(?i)allerg(?:ic|y|ies)\s*(?:to|:)\s*([^\n\.;]+)",
            r"(?i)-\s*([A-Za-z]+)\s*\((?:causes?|reaction:?)\s*([^)]+)\)",
        ]
        seen: set[str] = set()
        for pattern in patterns:
            for m in re.finditer(pattern, text):
                substances = re.split(r"[,;]|\band\b", m.group(1))
                reaction = m.group(2).strip() if len(m.groups()) >= 2 else None
                for s in substances:
                    s = s.strip().rstrip(".")
                    if s and s.lower() not in seen and len(s) > 1:
                        seen.add(s.lower())
                        allergies.append(Allergy(substance=s, reaction=reaction))
        return allergies

    def _extract_problems(self, assessment_text: str) -> list[Problem]:
        if not assessment_text:
            return []
        problems: list[Problem] = []
        lines = re.split(r"[\n;]|\d+\.\s*", assessment_text)
        for line in lines:
            line = line.strip().rstrip(".")
            if line and len(line) > 2:
                status = None
                if re.search(r"(?i)\b(resolved|stable)\b", line):
                    status = "resolved"
                elif re.search(r"(?i)\b(chronic|ongoing)\b", line):
                    status = "chronic"
                elif line:
                    status = "active"
                problems.append(Problem(description=line, status=status))
        return problems

    def _extract_red_flags(self, text: str) -> list[str]:
        flags: list[str] = []
        red_flag_patterns = [
            (r"(?i)\bchest\s+pain\b", "Chest pain"),
            (r"(?i)\bshortness\s+of\s+breath\b|\bSOB\b|\bdyspnea\b", "Shortness of breath"),
            (r"(?i)\bfever\b.*?\b10[1-9]|1[1-9]\d", "High fever"),
            (r"(?i)\bsuicidal\b|\bSI\b|\bself[\s-]harm\b", "Suicidal ideation/self-harm"),
            (r"(?i)\bsevere\s+pain\b|\bpain\s*(?:scale|rating|level)?\s*(?::|is)?\s*(?:[89]|10)\b", "Severe pain"),
            (r"(?i)\bunresponsive\b|\bunconsci", "Unresponsive/unconscious"),
        ]
        for pattern, label in red_flag_patterns:
            if re.search(pattern, text):
                flags.append(label)
        return flags

    def _generate_summary(
        self,
        sections: dict[str, str],
        meds: list[Medication],
        allergies: list[Allergy],
        problems: list[Problem],
    ) -> str:
        parts: list[str] = []
        cc = sections.get("cc") or sections.get("chief_complaint")
        if cc:
            parts.append(f"Patient presents with: {cc}.")
        if problems:
            desc = ", ".join(p.description for p in problems[:3])
            parts.append(f"Assessment includes: {desc}.")
        if meds:
            names = ", ".join(m.name for m in meds[:5])
            parts.append(f"Current medications: {names}.")
        if allergies:
            substances = ", ".join(a.substance for a in allergies)
            parts.append(f"Allergies: {substances}.")
        return " ".join(parts) if parts else "No summary available."
