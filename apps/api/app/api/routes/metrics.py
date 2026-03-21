from fastapi import APIRouter, Depends, Query

from app.auth import get_current_actor
from app.schemas.evaluation import (
    EvaluationComparison,
    EvaluationSummary,
    ScoreMode,
    ThresholdSweepSummary,
)
from app.schemas.auth import AuthenticatedActor
from app.schemas.feedback import FeedbackSummary
from app.services.evaluation import compare_demo_evaluation, evaluate_demo_dataset, sweep_demo_thresholds
from app.store.memory_store import CASE_STORE

router = APIRouter()


@router.get("/evaluation", response_model=EvaluationSummary)
def evaluation_summary(
    threshold: float = Query(default=0.3, ge=0.0, le=1.0),
    top_k: int = Query(default=3, ge=1, le=100),
    score_mode: ScoreMode = Query(default="rules"),
) -> EvaluationSummary:
    return evaluate_demo_dataset(threshold=threshold, top_k=top_k, score_mode=score_mode)


@router.get("/evaluation/compare", response_model=EvaluationComparison)
def evaluation_compare(
    threshold: float = Query(default=0.3, ge=0.0, le=1.0),
    top_k: int = Query(default=3, ge=1, le=100),
) -> EvaluationComparison:
    return compare_demo_evaluation(threshold=threshold, top_k=top_k)


@router.get("/evaluation/sweep", response_model=ThresholdSweepSummary)
def evaluation_sweep(
    top_k: int = Query(default=3, ge=1, le=100),
    thresholds: str | None = None,
) -> ThresholdSweepSummary:
    parsed_thresholds = None
    if thresholds:
        parsed_thresholds = [
            float(item.strip())
            for item in thresholds.split(",")
            if item.strip()
        ]
    return sweep_demo_thresholds(top_k=top_k, thresholds=parsed_thresholds)


@router.get("/feedback", response_model=FeedbackSummary)
def feedback_summary(actor: AuthenticatedActor = Depends(get_current_actor)) -> FeedbackSummary:
    return CASE_STORE.summarize_feedback(accessible_sites=actor.site_scope)
