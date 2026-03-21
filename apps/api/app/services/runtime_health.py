from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal
from app.schemas.health import DependencyHealth, HealthResponse, ReadinessResponse


def build_health_response(started_at: datetime | None) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        uptime_seconds=_uptime_seconds(started_at),
    )


def build_readiness_response(started_at: datetime | None) -> ReadinessResponse:
    database = check_database()
    overall_status = "ok" if database.status == "ok" else "error"
    return ReadinessResponse(
        status=overall_status,
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        uptime_seconds=_uptime_seconds(started_at),
        checks={"database": database},
    )


def check_database() -> DependencyHealth:
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return DependencyHealth(status="ok", backend=settings.database_backend)
    except Exception as exc:
        return DependencyHealth(
            status="error",
            backend=settings.database_backend,
            detail=str(exc),
        )


def _uptime_seconds(started_at: datetime | None) -> float:
    if started_at is None:
        return 0.0
    baseline = started_at
    if baseline.tzinfo is None:
        baseline = baseline.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - baseline
    return round(max(delta.total_seconds(), 0.0), 3)
