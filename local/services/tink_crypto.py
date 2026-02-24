"""Google Tink AEAD encryption for the local queue.

Uses AES128_GCM via Tink's Python API (v1.14+). The keyset is stored as a
cleartext JSON file for the MVP. Production upgrade: use KMS-encrypted keyset.
"""

from __future__ import annotations

import logging
from pathlib import Path

import tink
from tink import aead

logger = logging.getLogger(__name__)

_registered = False


def _register_aead() -> None:
    global _registered
    if not _registered:
        aead.register()
        _registered = True


def _get_secret_token():
    """Get the secret key access token for Tink 1.14+."""
    return tink._secret_key_access.TOKEN


def get_or_create_keyset(keyset_path: str) -> tink.KeysetHandle:
    """Load an existing keyset or generate a new AES128_GCM keyset."""
    _register_aead()
    path = Path(keyset_path)
    token = _get_secret_token()

    if path.exists():
        keyset_json = path.read_text(encoding="utf-8")
        return tink.json_proto_keyset_format.parse(keyset_json, token)

    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tink.new_keyset_handle(aead.aead_key_templates.AES128_GCM)

    serialized = tink.json_proto_keyset_format.serialize(handle, token)
    path.write_text(serialized, encoding="utf-8")

    logger.info("Created new Tink keyset at %s", keyset_path)
    return handle


class TinkAEAD:
    """Wrapper for Tink AEAD encrypt/decrypt operations."""

    def __init__(self, keyset_path: str):
        self._handle = get_or_create_keyset(keyset_path)
        self._aead = self._handle.primitive(aead.Aead)

    def encrypt(self, plaintext: bytes, associated_data: bytes) -> bytes:
        return self._aead.encrypt(plaintext, associated_data)

    def decrypt(self, ciphertext: bytes, associated_data: bytes) -> bytes:
        return self._aead.decrypt(ciphertext, associated_data)
