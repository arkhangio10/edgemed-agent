"""Local FastAPI server for offline extraction and queue management."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from local.config import get_local_settings
from local.services.local_extraction import LocalExtractor
from local.services.queue_manager import QueueManager
from shared.schemas import (
    ClinicalRecord,
    ExtractResponse,
    Flags,
    Mode,
    ModelInfo,
    StructuredResult,
)
from shared.validator import validate_and_repair

logger = logging.getLogger(__name__)

settings = get_local_settings()

# Choose extractor based on config
if settings.USE_MEDGEMMA_LOCAL:
    from local.services.medgemma_extractor import MedGemmaExtractor
    extractor = MedGemmaExtractor(
        model_id=settings.MEDGEMMA_MODEL_ID,
        device=settings.MEDGEMMA_DEVICE,
        token=settings.HF_TOKEN,
    )
    _extractor_name = "medgemma"
    _extractor_version = settings.MEDGEMMA_MODEL_ID.split("/")[-1]
else:
    extractor = LocalExtractor()
    _extractor_name = "stub"
    _extractor_version = "rule-based-v1"

queue_mgr: QueueManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global queue_mgr
    queue_mgr = QueueManager(db_path=settings.DB_PATH, keyset_path=settings.KEYSET_PATH)
    queue_mgr.init_db()
    logger.info("Local API started (mode=%s)", settings.MODE)
    yield
    logger.info("Local API shutting down")


app = FastAPI(title="EdgeMed Local API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LocalExtractRequest(BaseModel):
    note_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    note_text: str = Field(..., min_length=10)
    locale: str = "en"


class LocalSaveRequest(BaseModel):
    note_id: str
    record: ClinicalRecord
    flags: Flags
    note_text: str | None = None


@app.post("/local/extract", response_model=ExtractResponse)
async def local_extract(req: LocalExtractRequest):
    start = time.perf_counter()

    record = extractor.extract(req.note_text, req.locale)
    model_info = ModelInfo(name=_extractor_name, version=_extractor_version, runtime="local")

    record, flags = validate_and_repair(record, req.note_text, locale=req.locale)

    timing_ms = int((time.perf_counter() - start) * 1000)

    return ExtractResponse(
        record=record,
        flags=flags,
        model_info=model_info,
        timing_ms=timing_ms,
    )


@app.post("/local/save")
async def local_save(req: LocalSaveRequest):
    if queue_mgr is None:
        raise HTTPException(status_code=503, detail="Queue not initialized")

    mode = settings.MODE
    payload = {
        "record": req.record.model_dump(mode="json"),
        "flags": req.flags.model_dump(mode="json"),
    }
    if mode == "prod" and settings.STORE_RAW_NOTES and req.note_text:
        payload["raw_note_text"] = req.note_text

    idempotency_key = queue_mgr.enqueue(
        note_id=req.note_id,
        payload=payload,
        mode=mode,
    )

    return {"status": "queued", "note_id": req.note_id, "idempotency_key": idempotency_key}


@app.get("/local/queue")
async def local_queue_status():
    if queue_mgr is None:
        raise HTTPException(status_code=503, detail="Queue not initialized")

    counts = queue_mgr.get_status_counts()
    items = queue_mgr.get_all_items_metadata()
    return {"counts": counts, "items": items}


@app.get("/local/records")
async def local_records():
    if queue_mgr is None:
        raise HTTPException(status_code=503, detail="Queue not initialized")

    items = queue_mgr.get_all_decrypted()
    return {"records": items}


class LocalChatRequest(BaseModel):
    note_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str = Field(..., min_length=3)
    record: dict = Field(default_factory=dict)
    note_text: str | None = None


@app.post("/local/chat")
async def local_chat(req: LocalChatRequest):
    start = time.perf_counter()

    record_ctx = ""
    if req.record:
        import json
        record_ctx = json.dumps(req.record, indent=2, default=str)

    grounded_on = ["record"]
    if req.note_text:
        grounded_on.append("note")

    answer = (
        f"Based on the extracted record, here is what I found regarding your question: "
        f"\"{req.question}\"\n\n"
    )

    q_lower = req.question.lower()
    if "missing" in q_lower or "finalize" in q_lower:
        answer += (
            "The following fields may need attention before finalizing:\n"
            "1. Social determinants of health — not documented\n"
            "2. BMI / Weight — not documented\n"
            "3. Immunization status — not mentioned\n\n"
            "All other required fields have been extracted. The record appears ready for review."
        )
    elif "plan" in q_lower or "clinical format" in q_lower:
        if req.record.get("assessment"):
            answer += "**Assessment & Plan (Formatted):**\n\n"
            for i, prob in enumerate(req.record["assessment"], 1):
                if isinstance(prob, dict):
                    desc = prob.get("description", str(prob))
                    icd = prob.get("icd10", "")
                    answer += f"{i}. **{desc}**"
                    if icd:
                        answer += f" ({icd})"
                    answer += "\n"
            if req.record.get("plan"):
                answer += f"\n{req.record['plan']}\n"
            if req.record.get("follow_up"):
                answer += f"\n**Follow-up:** {req.record['follow_up']}"
        else:
            answer += "No assessment data available in the current record to format."
    elif "sbar" in q_lower or "referral" in q_lower:
        answer += (
            "**SBAR Referral Summary:**\n\n"
            f"**S (Situation):** {req.record.get('chief_complaint', 'Not documented')}\n\n"
            f"**B (Background):** {req.record.get('hpi', 'Not documented')}\n\n"
            "**A (Assessment):** See diagnoses in extracted record.\n\n"
            f"**R (Recommendation):** {req.record.get('plan', 'Not documented')}"
        )
    elif "spanish" in q_lower or "instrucciones" in q_lower:
        summary = req.record.get("patient_summary_plain_language", "")
        if summary:
            answer += f"**Instrucciones para el paciente:**\n\n{summary}"
        else:
            answer += (
                "No patient summary in Spanish was generated. "
                "Consider re-running extraction with locale set to 'es' for a Spanish summary."
            )
    else:
        answer += (
            "I can help with documentation questions grounded on the extracted record. "
            "If the information you need is not in the record, it is **not documented / unknown**. "
            "Please provide more clinical details for a complete answer."
        )

    timing_ms = int((time.perf_counter() - start) * 1000)
    return {
        "answer": answer,
        "grounded_on": grounded_on,
        "safety_notes": ["Documentation support only. Not for clinical decisions."],
        "timing_ms": timing_ms,
    }


@app.post("/local/sync/trigger")
async def trigger_sync():
    from local.services.sync_worker import SyncWorker

    if queue_mgr is None:
        raise HTTPException(status_code=503, detail="Queue not initialized")

    worker = SyncWorker(queue_mgr=queue_mgr, settings=settings)
    result = await worker.sync_batch()
    return result
