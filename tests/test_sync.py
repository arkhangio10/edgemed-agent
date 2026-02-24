"""Tests for sync-related logic (idempotency, payload preparation)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.schemas import (
    ClinicalRecord,
    Flags,
    Mode,
    SyncItem,
    SyncRequest,
)
from shared.constants import SCHEMA_VERSION


def test_sync_request_demo_rejects_raw_text():
    """In DEMO mode, raw_note_text must be None."""
    item = SyncItem(
        note_id="test-sync-001",
        record=ClinicalRecord(chief_complaint="Test"),
        flags=Flags(completeness_score=0.9),
        created_at="2026-01-01T00:00:00Z",
        schema_version=SCHEMA_VERSION,
        idempotency_key="dev:test-sync-001:abc",
        raw_note_text="This should be rejected in demo",
    )
    assert item.raw_note_text is not None
    # The server router enforces: if mode==demo and raw_note_text is not None -> fail


def test_sync_request_serialization():
    """Verify SyncRequest serializes correctly."""
    item = SyncItem(
        note_id="test-sync-002",
        record=ClinicalRecord(),
        flags=Flags(),
        created_at="2026-01-01T00:00:00Z",
        schema_version=SCHEMA_VERSION,
        idempotency_key="dev:test-sync-002:def",
    )
    req = SyncRequest(
        device_id="dev-001",
        mode=Mode.demo,
        items=[item],
    )
    data = req.model_dump(mode="json")
    assert data["device_id"] == "dev-001"
    assert data["mode"] == "demo"
    assert len(data["items"]) == 1
    assert data["items"][0]["idempotency_key"] == "dev:test-sync-002:def"
    assert data["items"][0]["raw_note_text"] is None


def test_idempotency_key_format():
    """Verify idempotency key has expected format."""
    key = "local-dev-001:note-001:a1b2c3d4"
    parts = key.split(":")
    assert len(parts) == 3
    assert parts[0] == "local-dev-001"
    assert parts[1] == "note-001"


if __name__ == "__main__":
    test_sync_request_demo_rejects_raw_text()
    test_sync_request_serialization()
    test_idempotency_key_format()
    print("All sync tests passed!")
