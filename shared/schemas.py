from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from shared.constants import SCHEMA_VERSION


class Mode(str, Enum):
    demo = "demo"
    prod = "prod"


class Medication(BaseModel):
    name: str
    dose: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    status: Optional[str] = None  # e.g. new, increased, continue


class Allergy(BaseModel):
    substance: str
    reaction: Optional[str] = None
    severity: Optional[str] = None


class Problem(BaseModel):
    description: str
    status: Optional[str] = None  # active | resolved | chronic
    icd10: Optional[str] = None
    confidence: Optional[str] = None  # low | medium | high


class ClinicalRecord(BaseModel):
    chief_complaint: Optional[str] = None
    hpi: Optional[str] = None
    assessment: list[Problem] = Field(default_factory=list)
    plan: Optional[str] = None
    medications: list[Medication] = Field(default_factory=list)
    allergies: list[Allergy] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    follow_up: Optional[str] = None
    patient_summary_plain_language: Optional[str] = None


class Flags(BaseModel):
    missing_fields: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    confidence_by_field: dict[str, str] = Field(default_factory=dict)
    completeness_score: float = 0.0


class ModelInfo(BaseModel):
    name: str = "medgemma"
    version: str = "4b-v1.5"
    runtime: str = "cloud"  # cloud | local


class StructuredResult(BaseModel):
    note_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: str = SCHEMA_VERSION
    record: ClinicalRecord
    flags: Flags
    model_info: ModelInfo


# --------------- Request / Response models ---------------

class ExtractRequest(BaseModel):
    note_id: str
    note_text: str = Field(..., min_length=10)
    locale: str = "en"
    schema_version: str = SCHEMA_VERSION
    mode: Mode = Mode.demo


class ExtractResponse(BaseModel):
    record: ClinicalRecord
    flags: Flags
    model_info: ModelInfo
    timing_ms: int


class ChatRequest(BaseModel):
    note_id: str
    question: str = Field(..., min_length=3)
    record: ClinicalRecord
    note_text: Optional[str] = None
    mode: Mode = Mode.demo


class ChatResponse(BaseModel):
    answer: str
    grounded_on: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    timing_ms: int


class SyncItem(BaseModel):
    note_id: str
    record: ClinicalRecord
    flags: Flags
    created_at: datetime
    schema_version: str
    idempotency_key: str
    raw_note_text: Optional[str] = None


class SyncRequest(BaseModel):
    device_id: str
    mode: Mode
    items: list[SyncItem] = Field(..., max_length=50)


class SyncResponse(BaseModel):
    synced: list[str] = Field(default_factory=list)
    failed: list[dict] = Field(default_factory=list)
    timing_ms: int


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = SCHEMA_VERSION
    model_loaded: bool = True


# --------------- Image & prescription ---------------

class InterpretImageRequest(BaseModel):
    image_base64: str = Field(..., min_length=1)
    prompt_override: Optional[str] = None
    mime_type: str = "image/jpeg"  # image/jpeg | image/png


class InterpretImageResponse(BaseModel):
    interpretation: str
    model_info: ModelInfo
    timing_ms: int


class PrescriptionFromImageRequest(BaseModel):
    image_base64: str = Field(..., min_length=1)


class PrescriptionFromImageResponse(BaseModel):
    medications: list[Medication] = Field(default_factory=list)
    raw_text: Optional[str] = None
    model_info: ModelInfo
    timing_ms: int
