"""EdgeMed Agent — Cloud Run FastAPI entrypoint."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from cloud.auth import init_firebase
from cloud.config import get_settings
from cloud.routers import analytics, chat, extract, health, image_interpretation, prescription, sync

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_firebase()
    except Exception:
        logger.exception("Firebase init failed — running in degraded mode (demo only)")
    logger.info("EdgeMed Cloud API started")
    yield
    logger.info("EdgeMed Cloud API shutting down")


app = FastAPI(
    title="EdgeMed Agent API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: allow_credentials=True + allow_origins=["*"] is INVALID per spec.
# Browsers silently reject it. We must list explicit origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://edgemedsoinar.web.app",
        "https://edgemedsoinar.firebaseapp.com",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_metadata(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    start = time.perf_counter()

    response = await call_next(request)

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logger.info(
        "request_id=%s method=%s path=%s status=%d timing_ms=%d",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Timing-Ms"] = str(elapsed_ms)
    return response


app.include_router(health.router)
app.include_router(extract.router)
app.include_router(chat.router)
app.include_router(sync.router)
app.include_router(analytics.router)
app.include_router(image_interpretation.router)
app.include_router(prescription.router)
