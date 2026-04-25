from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import require_roles
from app.schemas.auth import AuthenticatedActor
from app.schemas.autoresearch import (
    AutoresearchLeaderboard,
    AutoresearchPromotionResult,
    AutoresearchRunDetail,
    AutoresearchRunSummary,
)
from app.services import autoresearch as autoresearch_service

router = APIRouter()

_VIEW_ROLES = ("analyst", "navigator", "admin")


@router.get("/runs", response_model=list[AutoresearchRunSummary])
def list_runs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _actor: AuthenticatedActor = Depends(require_roles(*_VIEW_ROLES)),
) -> list[AutoresearchRunSummary]:
    return autoresearch_service.list_runs(limit=limit, offset=offset)


@router.get("/leaderboard", response_model=AutoresearchLeaderboard)
def get_leaderboard(
    top_n: int = Query(default=10, ge=1, le=50),
    _actor: AuthenticatedActor = Depends(require_roles(*_VIEW_ROLES)),
) -> AutoresearchLeaderboard:
    return autoresearch_service.leaderboard(top_n=top_n)


@router.get("/runs/{run_id}", response_model=AutoresearchRunDetail)
def get_run_detail(
    run_id: str,
    _actor: AuthenticatedActor = Depends(require_roles(*_VIEW_ROLES)),
) -> AutoresearchRunDetail:
    detail = autoresearch_service.get_run_detail(run_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Autoresearch run not found")
    return detail


@router.post("/promote/{run_id}", response_model=AutoresearchPromotionResult)
def promote_run(
    run_id: str,
    actor: AuthenticatedActor = Depends(require_roles("admin")),
) -> AutoresearchPromotionResult:
    try:
        return autoresearch_service.promote_run(run_id, actor_user_id=actor.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
