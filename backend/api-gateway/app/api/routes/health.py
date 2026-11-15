
from fastapi import APIRouter

from app.schemas.health import HealthResponse


router = APIRouter(tags=["Health"])


@router.get("/health/live", response_model=HealthResponse)
async def liveness_check():
    return HealthResponse(
        status="alive",
        service="api-gateway",
    )


@router.get("/health/ready", response_model=HealthResponse)
async def readiness_check():
    return HealthResponse(
        status="ready",
        service="api-gateway",
    )
