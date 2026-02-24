from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings

LOCAL_DIR = Path(__file__).resolve().parent


class LocalSettings(BaseSettings):
    MODE: str = "prod"
    CLOUD_API_URL: str = "http://localhost:8080"
    DEVICE_ID: str = "local-dev-001"
    DB_PATH: str = str(LOCAL_DIR / "data" / "queue.db")
    KEYSET_PATH: str = str(LOCAL_DIR / "keys" / "edgemed_local.keyset.json")
    SYNC_INTERVAL_SECONDS: int = 30
    SYNC_BATCH_SIZE: int = 10
    MAX_RETRY_COUNT: int = 5
    STORE_RAW_NOTES: bool = True

    # MedGemma local (Hugging Face). Model is gated: accept terms at
    # https://huggingface.co/google/medgemma-1.5-4b-it and set HF token.
    USE_MEDGEMMA_LOCAL: bool = False
    MEDGEMMA_MODEL_ID: str = "google/medgemma-1.5-4b-it"
    MEDGEMMA_DEVICE: str = "cuda"  # "cuda" | "cpu"
    HF_TOKEN: Optional[str] = None  # For gated model; or set env HF_TOKEN

    model_config = {"env_prefix": "EDGEMED_"}


@lru_cache
def get_local_settings() -> LocalSettings:
    return LocalSettings()
