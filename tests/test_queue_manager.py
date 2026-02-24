"""Tests for the encrypted queue manager (Tink AEAD + SQLite)."""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_queue_encrypt_decrypt_roundtrip():
    """Verify that enqueue encrypts and we can decrypt back to original payload."""
    from local.services.queue_manager import QueueManager

    tmpdir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(tmpdir, "test_queue.db")
        keyset_path = os.path.join(tmpdir, "test.keyset.json")

        qm = QueueManager(db_path=db_path, keyset_path=keyset_path)
        qm.init_db()

        payload = {
            "record": {"chief_complaint": "Test", "medications": []},
            "flags": {"missing_fields": [], "completeness_score": 0.9},
        }

        idempotency_key = qm.enqueue("note-001", payload, "demo")
        assert idempotency_key is not None

        items = qm.get_pending(limit=10)
        assert len(items) == 1
        assert items[0]["note_id"] == "note-001"

        ciphertext = items[0]["ciphertext"]
        assert isinstance(ciphertext, bytes)
        assert ciphertext != json.dumps(payload).encode("utf-8")

        decrypted = qm.decrypt_payload("note-001", ciphertext)
        assert decrypted["record"]["chief_complaint"] == "Test"
        assert decrypted["flags"]["completeness_score"] == 0.9

        qm.close()
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_queue_status_transitions():
    """Test queued -> syncing -> synced status flow."""
    from local.services.queue_manager import QueueManager

    tmpdir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(tmpdir, "test_queue.db")
        keyset_path = os.path.join(tmpdir, "test.keyset.json")

        qm = QueueManager(db_path=db_path, keyset_path=keyset_path)
        qm.init_db()

        qm.enqueue("note-002", {"test": True}, "prod")

        counts = qm.get_status_counts()
        assert counts.get("queued", 0) == 1

        qm.mark_syncing("note-002")
        counts = qm.get_status_counts()
        assert counts.get("syncing", 0) == 1

        qm.mark_synced("note-002")
        counts = qm.get_status_counts()
        assert counts.get("synced", 0) == 1

        pending = qm.get_pending()
        assert len(pending) == 0

        qm.close()
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_queue_failure_and_retry():
    """Test failure tracking and retry."""
    from local.services.queue_manager import QueueManager

    tmpdir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(tmpdir, "test_queue.db")
        keyset_path = os.path.join(tmpdir, "test.keyset.json")

        qm = QueueManager(db_path=db_path, keyset_path=keyset_path)
        qm.init_db()

        qm.enqueue("note-003", {"test": True}, "demo")
        qm.mark_failed("note-003", "Connection timeout")

        counts = qm.get_status_counts()
        assert counts.get("failed", 0) == 1

        items = qm.get_all_items_metadata()
        assert items[0]["retry_count"] == 1
        assert items[0]["fail_reason"] == "Connection timeout"

        qm.reset_for_retry("note-003")
        counts = qm.get_status_counts()
        assert counts.get("queued", 0) == 1

        qm.close()
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_ciphertext_is_not_plaintext():
    """Verify SQLite stores actual ciphertext, not plaintext JSON."""
    import sqlite3 as sqlite3_mod
    from local.services.queue_manager import QueueManager

    tmpdir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(tmpdir, "test_queue.db")
        keyset_path = os.path.join(tmpdir, "test.keyset.json")

        qm = QueueManager(db_path=db_path, keyset_path=keyset_path)
        qm.init_db()

        secret_payload = {"record": {"chief_complaint": "SENSITIVE_DATA_12345"}}
        qm.enqueue("note-004", secret_payload, "prod")
        qm.close()

        conn = sqlite3_mod.connect(db_path)
        row = conn.execute("SELECT ciphertext FROM queue_items WHERE note_id='note-004'").fetchone()
        conn.close()

        raw_bytes = row[0]
        assert b"SENSITIVE_DATA_12345" not in raw_bytes
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    test_queue_encrypt_decrypt_roundtrip()
    print("  [PASS] encrypt/decrypt roundtrip")
    test_queue_status_transitions()
    print("  [PASS] status transitions")
    test_queue_failure_and_retry()
    print("  [PASS] failure and retry")
    test_ciphertext_is_not_plaintext()
    print("  [PASS] ciphertext is not plaintext")
    print("All queue manager tests passed!")
