from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response, status

from app.schemas.health import HealthResponse, ReadinessResponse
from app.services import runtime_health

router = APIRouter()


def _started_at(request: Request) -> datetime | None:
    return getattr(request.app.state, "started_at", datetime.now(timezone.utc))


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    return runtime_health.build_health_response(_started_at(request))


@router.get("/health/live", response_model=HealthResponse)
def live_health(request: Request) -> HealthResponse:
    return runtime_health.build_health_response(_started_at(request))


@router.get("/health/ready", response_model=ReadinessResponse)
def ready_health(request: Request, response: Response) -> ReadinessResponse:
    readiness = runtime_health.build_readiness_response(_started_at(request))
    if readiness.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return readiness
