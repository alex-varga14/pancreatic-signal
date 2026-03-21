from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.session import init_db
from app.observability import RequestLoggingMiddleware, configure_logging


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.started_at = datetime.now(timezone.utc)
    init_db()
    yield


app = FastAPI(
    title="Pancreatic Signal API",
    version=settings.app_version,
    description="Research-first triage API for suspicious pancreatic radiology reports.",
    lifespan=lifespan,
)
app.state.started_at = datetime.now(timezone.utc)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Pancreatic Signal API",
        "status": "ok",
        "docs": "/docs",
    }
