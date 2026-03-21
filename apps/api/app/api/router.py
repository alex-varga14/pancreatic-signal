from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.triage import router as triage_router
from app.api.routes.cases import router as cases_router
from app.api.routes.exports import router as exports_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.imports import router as imports_router
from app.api.routes.trials import router as trials_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(triage_router, prefix="/triage", tags=["triage"])
api_router.include_router(imports_router, prefix="/imports", tags=["imports"])
api_router.include_router(cases_router, prefix="/cases", tags=["cases"])
api_router.include_router(exports_router, prefix="/exports", tags=["exports"])
api_router.include_router(metrics_router, prefix="/metrics", tags=["metrics"])
api_router.include_router(trials_router, prefix="/trials", tags=["trials"])
