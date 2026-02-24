"""Tests for local extraction stub."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local.services.local_extraction import LocalExtractor
from shared.schemas import ClinicalRecord


SAMPLE_NOTE = """CC: Chest pain
HPI: 55yo male presents with substernal chest pain radiating to left arm for 2 hours. Pain is 8/10, pressure-like.
Medications: Lisinopril 10mg daily, Metformin 500mg BID
Allergies: Penicillin (rash), Sulfa (hives)
Assessment: 1. Acute coronary syndrome. 2. Hypertension. 3. Type 2 diabetes.
Plan: EKG stat, troponins q6h, aspirin 325mg, cardiology consult.
Follow-up: Admit to telemetry, reassess in 6 hours."""


def test_extract_returns_clinical_record():
    extractor = LocalExtractor()
    record = extractor.extract(SAMPLE_NOTE)
    assert isinstance(record, ClinicalRecord)


def test_extract_finds_chief_complaint():
    extractor = LocalExtractor()
    record = extractor.extract(SAMPLE_NOTE)
    assert record.chief_complaint is not None
    assert "chest pain" in record.chief_complaint.lower()


def test_extract_finds_medications():
    extractor = LocalExtractor()
    record = extractor.extract(SAMPLE_NOTE)
    med_names = [m.name.lower() for m in record.medications]
    assert any("lisinopril" in n for n in med_names)


def test_extract_finds_allergies():
    extractor = LocalExtractor()
    record = extractor.extract(SAMPLE_NOTE)
    allergy_substances = [a.substance.lower() for a in record.allergies]
    assert any("penicillin" in s for s in allergy_substances)


def test_extract_finds_assessment():
    extractor = LocalExtractor()
    record = extractor.extract(SAMPLE_NOTE)
    assert len(record.assessment) > 0


def test_extract_finds_red_flags():
    extractor = LocalExtractor()
    record = extractor.extract(SAMPLE_NOTE)
    assert any("chest" in f.lower() for f in record.red_flags)


def test_extract_nkda():
    note = """CC: Follow-up
HPI: Routine diabetes check
Medications: Metformin 500mg BID
Allergies: NKDA
Assessment: 1. Type 2 DM
Plan: Continue current treatment
Follow-up: 3 months"""
    extractor = LocalExtractor()
    record = extractor.extract(note)
    assert any("nkda" in a.substance.lower() for a in record.allergies)


def test_repair_fields():
    extractor = LocalExtractor()
    record = ClinicalRecord(chief_complaint="Headache")
    repaired = extractor.repair_fields(
        note_text=SAMPLE_NOTE,
        current_record=record,
        fields_to_repair=["medications", "allergies"],
    )
    assert "medications" in repaired or "allergies" in repaired


if __name__ == "__main__":
    test_extract_returns_clinical_record()
    test_extract_finds_chief_complaint()
    test_extract_finds_medications()
    test_extract_finds_allergies()
    test_extract_finds_assessment()
    test_extract_finds_red_flags()
    test_extract_nkda()
    test_repair_fields()
    print("All extraction tests passed!")
