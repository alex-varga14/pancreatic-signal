from fastapi.testclient import TestClient

from app.main import app
from app.api.routes import health as health_routes
from app.schemas.health import DependencyHealth, ReadinessResponse


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "pancreatic-signal-api"
    assert payload["version"] == "0.1.0"
    assert payload["environment"]
    assert payload["uptime_seconds"] >= 0


def test_live_health() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "pancreatic-signal-api"


def test_ready_health_reports_database_check() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["checks"]["database"]["status"] == "ok"
    assert payload["checks"]["database"]["backend"]


def test_ready_health_returns_503_when_dependency_fails(monkeypatch) -> None:
    def fake_readiness_response(*_args, **_kwargs) -> ReadinessResponse:
        return ReadinessResponse(
            status="error",
            service="pancreatic-signal-api",
            version="0.1.0",
            environment="test",
            uptime_seconds=0.0,
            checks={
                "database": DependencyHealth(
                    status="error",
                    backend="sqlite",
                    detail="database unavailable",
                )
            },
        )

    monkeypatch.setattr(health_routes.runtime_health, "build_readiness_response", fake_readiness_response)

    client = TestClient(app)
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["checks"]["database"]["detail"] == "database unavailable"


def test_request_id_header_is_returned() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health", headers={"X-Request-ID": "req-123"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-123"
