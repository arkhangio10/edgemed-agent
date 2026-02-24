"""Tests for the agentic validator + repair loop."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.schemas import Allergy, ClinicalRecord, Medication, Problem
from shared.validator import validate, validate_and_repair


def test_complete_record_high_score():
    record = ClinicalRecord(
        chief_complaint="Chest pain",
        hpi="55yo male with chest pain for 2 hours",
        assessment=[Problem(description="Acute coronary syndrome", status="active")],
        plan="EKG stat, troponins q6h",
        medications=[Medication(name="Aspirin", dose="325mg")],
        allergies=[Allergy(substance="Penicillin", reaction="rash")],
    )
    flags = validate(record)
    assert flags.completeness_score >= 0.8
    assert len(flags.missing_fields) == 0


def test_empty_record_low_score():
    record = ClinicalRecord()
    flags = validate(record)
    assert flags.completeness_score < 0.5
    assert len(flags.missing_fields) == 6  # all required fields


def test_partial_record():
    record = ClinicalRecord(
        chief_complaint="Headache",
        hpi="Patient has headache",
    )
    flags = validate(record)
    assert "assessment" in flags.missing_fields
    assert "plan" in flags.missing_fields
    assert "medications" in flags.missing_fields
    assert "allergies" in flags.missing_fields


def test_nkda_contradiction():
    record = ClinicalRecord(
        chief_complaint="Follow-up",
        hpi="Routine visit",
        assessment=[Problem(description="HTN")],
        plan="Continue meds",
        medications=[Medication(name="Lisinopril", dose="10mg")],
        allergies=[
            Allergy(substance="NKDA"),
            Allergy(substance="Penicillin", reaction="rash"),
        ],
    )
    flags = validate(record)
    assert any("NKDA" in c for c in flags.contradictions)


def test_validate_and_repair_without_extractor():
    record = ClinicalRecord(chief_complaint="Test")
    record, flags = validate_and_repair(record, "Test note text")
    assert flags.completeness_score < 0.8  # Can't repair without extractor


def test_confidence_by_field():
    record = ClinicalRecord(
        chief_complaint="A",
        hpi="Short",
        assessment=[Problem(description="Test")],
        plan="Follow up in 2 weeks with a comprehensive plan and reassessment",
        medications=[Medication(name="Aspirin")],
        allergies=[Allergy(substance="Penicillin")],
    )
    flags = validate(record)
    assert "chief_complaint" in flags.confidence_by_field
    assert flags.confidence_by_field["plan"] == "high"


if __name__ == "__main__":
    test_complete_record_high_score()
    test_empty_record_low_score()
    test_partial_record()
    test_nkda_contradiction()
    test_validate_and_repair_without_extractor()
    test_confidence_by_field()
    print("All validator tests passed!")
