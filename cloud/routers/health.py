from fastapi import APIRouter

from shared.constants import SCHEMA_VERSION
from shared.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/v1/health", response_model=HealthResponse)
@router.get("/healthz", response_model=HealthResponse, include_in_schema=False)
async def health():
    return HealthResponse(
        status="ok",
        version=SCHEMA_VERSION,
        model_loaded=True,
    )


@router.get("/", include_in_schema=False)
async def root():
    return {"service": "EdgeMed Agent API", "status": "ok", "version": SCHEMA_VERSION}

