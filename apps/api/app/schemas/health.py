from typing import Literal

from pydantic import BaseModel, Field

HealthStatus = Literal["ok", "error"]


class DependencyHealth(BaseModel):
    status: HealthStatus
    backend: str | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    status: HealthStatus
    service: str
    version: str
    environment: str
    uptime_seconds: float = Field(ge=0.0)


class ReadinessResponse(HealthResponse):
    checks: dict[str, DependencyHealth]
