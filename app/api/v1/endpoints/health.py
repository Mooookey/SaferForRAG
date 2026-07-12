from datetime import datetime, timezone

from fastapi import APIRouter

from app.models import HealthResponse


router = APIRouter()


@router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="security-processer",
        version="1",
        time=datetime.now(timezone.utc).isoformat(),
    )
