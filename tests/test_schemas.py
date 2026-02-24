"""Tests for shared schema validation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.schemas import (
    Allergy,
    ClinicalRecord,
    ExtractRequest,
    Flags,
    Medication,
    Mode,
    ModelInfo,
    Problem,
    StructuredResult,
    SyncItem,
    SyncRequest,
)
from shared.constants import SCHEMA_VERSION


def test_clinical_record_defaults():
    record = ClinicalRecord()
    assert record.chief_complaint is None
    assert record.medications == []
    assert record.allergies == []
    assert record.assessment == []
    assert record.red_flags == []


def test_clinical_record_with_data():
    record = ClinicalRecord(
        chief_complaint="Chest pain",
        hpi="55yo male with chest pain",
        assessment=[Problem(description="ACS", status="active")],
        plan="EKG stat",
        medications=[Medication(name="Aspirin", dose="325mg", frequency="daily")],
        allergies=[Allergy(substance="Penicillin", reaction="rash")],
        red_flags=["Chest pain"],
        follow_up="Reassess in 6 hours",
    )
    assert record.chief_complaint == "Chest pain"
    assert len(record.medications) == 1
    assert record.medications[0].name == "Aspirin"
    assert len(record.allergies) == 1
    assert record.allergies[0].substance == "Penicillin"


def test_flags_model():
    flags = Flags(
        missing_fields=["plan"],
        contradictions=[],
        confidence_by_field={"chief_complaint": "high"},
        completeness_score=0.85,
    )
    assert flags.completeness_score == 0.85
    assert "plan" in flags.missing_fields


def test_extract_request_mode():
    req = ExtractRequest(
        note_id="test-001",
        note_text="CC: Headache for 3 days",
        mode=Mode.demo,
    )
    assert req.mode == Mode.demo
    assert req.locale == "en"
    assert req.schema_version == SCHEMA_VERSION


def test_sync_request_demo_mode():
    item = SyncItem(
        note_id="test-001",
        record=ClinicalRecord(),
        flags=Flags(),
        created_at="2026-01-01T00:00:00Z",
        schema_version=SCHEMA_VERSION,
        idempotency_key="dev:test-001:abc123",
        raw_note_text=None,
    )
    req = SyncRequest(
        device_id="dev-001",
        mode=Mode.demo,
        items=[item],
    )
    assert req.mode == Mode.demo
    assert item.raw_note_text is None


def test_structured_result():
    result = StructuredResult(
        note_id="test-001",
        record=ClinicalRecord(chief_complaint="Headache"),
        flags=Flags(completeness_score=0.9),
        model_info=ModelInfo(),
    )
    assert result.schema_version == SCHEMA_VERSION
    assert result.record.chief_complaint == "Headache"


if __name__ == "__main__":
    test_clinical_record_defaults()
    test_clinical_record_with_data()
    test_flags_model()
    test_extract_request_mode()
    test_sync_request_demo_mode()
    test_structured_result()
    print("All schema tests passed!")
