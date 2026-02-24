from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_ID: str = "edgemedsoinar"
    DEMO_MODE_ENABLED: bool = True
    PROD_MODE_ENABLED: bool = False
    # MedGemma on Vertex AI Model Garden
    MEDGEMMA_MODEL: str = "publishers/google/models/medgemma"
    MEDGEMMA_VERSION: str = "medgemma-1.5-4b-it"
    MEDGEMMA_ENDPOINT_ID: str = ""  # Set after deploying MedGemma to an endpoint (text + optional vision)
    MEDGEMMA_REGION: str = "us-central1"
    # Google API key: only for chatbot and prescription-from-image. NOT used for medical image interpretation.
    GOOGLE_API_KEY: str = ""
    BQ_DATASET: str = "edgemed_analytics"
    RATE_LIMIT_PER_MIN: int = 30
    LOG_LEVEL: str = "INFO"
    GOOGLE_CLOUD_PROJECT: str = ""
    STORE_RAW_NOTES_PROD: bool = False

    model_config = {"env_prefix": "EDGEMED_"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
