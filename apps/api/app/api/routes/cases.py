from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_actor, require_case_site_access, require_roles, validate_requested_site_access
from app.schemas.auth import AuthenticatedActor
from app.schemas.case import (
    CaseDetail,
    CaseListItem,
    CaseSortBy,
    ReviewActionInput,
    ReviewActionResult,
    SortDirection,
)
from app.schemas.feedback import (
    FeedbackRecommendation,
    ReviewerFeedbackInput,
    ReviewerFeedbackRecord,
    ReviewerFeedbackResult,
)
from app.schemas.research import ResearchCaseDetail, ResearchCaseListItem
from app.services.deidentification import deidentify_case_detail, deidentify_case_list_item
from app.services.feedback_recommendation import recommend_case_feedback
from app.schemas.hybrid import HybridAnalysis
from app.services.hybrid_analysis import analyze_hybrid_report
from app.store.memory_store import CASE_STORE

router = APIRouter()


@router.get("", response_model=list[CaseListItem])
def list_cases(
    status: str | None = None,
    urgency: str | None = None,
    site: str | None = None,
    reviewer: str | None = None,
    modality: str | None = None,
    rationale: str | None = None,
    feedback_label: str | None = None,
    needs_feedback: bool = Query(default=False),
    disagreement_only: bool = Query(default=False),
    hybrid_delta_min: float | None = Query(default=None, ge=0.0, le=1.0),
    hybrid_review_priority: str | None = None,
    active_learning_priority: str | None = None,
    active_learning_only: bool = Query(default=False),
    include_hybrid: bool = Query(default=False),
    q: str | None = None,
    sort_by: CaseSortBy = Query(default="score"),
    sort_dir: SortDirection = Query(default="desc"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    actor: AuthenticatedActor = Depends(get_current_actor),
    ) -> list[CaseListItem]:
    site = validate_requested_site_access(actor, site)
    return CASE_STORE.list_cases(
        status=status,
        urgency=urgency,
        site=site,
        accessible_sites=actor.site_scope,
        reviewer=reviewer,
        modality=modality,
        rationale=rationale,
        feedback_label=feedback_label,
        needs_feedback=needs_feedback,
        disagreement_only=disagreement_only,
        hybrid_delta_min=hybrid_delta_min,
        hybrid_review_priority=hybrid_review_priority,
        active_learning_priority=active_learning_priority,
        active_learning_only=active_learning_only,
        include_hybrid=include_hybrid,
        q=q,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


@router.get("/research", response_model=list[ResearchCaseListItem])
def list_research_cases(
    status: str | None = None,
    urgency: str | None = None,
    site: str | None = None,
    reviewer: str | None = None,
    modality: str | None = None,
    rationale: str | None = None,
    feedback_label: str | None = None,
    needs_feedback: bool = Query(default=False),
    disagreement_only: bool = Query(default=False),
    hybrid_delta_min: float | None = Query(default=None, ge=0.0, le=1.0),
    hybrid_review_priority: str | None = None,
    active_learning_priority: str | None = None,
    active_learning_only: bool = Query(default=False),
    include_hybrid: bool = Query(default=False),
    q: str | None = None,
    sort_by: CaseSortBy = Query(default="score"),
    sort_dir: SortDirection = Query(default="desc"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    actor: AuthenticatedActor = Depends(get_current_actor),
) -> list[ResearchCaseListItem]:
    site = validate_requested_site_access(actor, site)
    cases = CASE_STORE.list_cases(
        status=status,
        urgency=urgency,
        site=site,
        accessible_sites=actor.site_scope,
        reviewer=reviewer,
        modality=modality,
        rationale=rationale,
        feedback_label=feedback_label,
        needs_feedback=needs_feedback,
        disagreement_only=disagreement_only,
        hybrid_delta_min=hybrid_delta_min,
        hybrid_review_priority=hybrid_review_priority,
        active_learning_priority=active_learning_priority,
        active_learning_only=active_learning_only,
        include_hybrid=include_hybrid,
        q=q,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )
    return [deidentify_case_list_item(item) for item in cases]


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(case_id: str, actor: AuthenticatedActor = Depends(get_current_actor)) -> CaseDetail:
    case = CASE_STORE.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    require_case_site_access(actor, case.site)
    return case


@router.get("/{case_id}/research", response_model=ResearchCaseDetail)
def get_research_case(case_id: str, actor: AuthenticatedActor = Depends(get_current_actor)) -> ResearchCaseDetail:
    case = CASE_STORE.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    require_case_site_access(actor, case.site)
    return deidentify_case_detail(case)


@router.get("/{case_id}/hybrid", response_model=HybridAnalysis)
def get_case_hybrid_analysis(case_id: str, actor: AuthenticatedActor = Depends(get_current_actor)) -> HybridAnalysis:
    case = CASE_STORE.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    require_case_site_access(actor, case.site)
    return analyze_hybrid_report(
        report_text=case.report_text,
        score=case.score,
        urgency=case.urgency,
        rationale_codes=case.rationale_codes,
        evidence=case.evidence,
    )


@router.post("/{case_id}/review", response_model=ReviewActionResult)
def review_case(
    case_id: str,
    payload: ReviewActionInput,
    actor: AuthenticatedActor = Depends(require_roles("reviewer", "navigator", "admin")),
) -> ReviewActionResult:
    case = CASE_STORE.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    require_case_site_access(actor, case.site)
    effective_payload = payload.model_copy(update={"reviewer": actor.user_id})
    updated_case = CASE_STORE.add_review_action(case_id, effective_payload)
    return ReviewActionResult(
        ok=True,
        case_id=case_id,
        action=effective_payload.action,
        status=updated_case["status"],
        assigned_to=updated_case.get("assigned_to"),
    )


@router.get("/{case_id}/feedback", response_model=list[ReviewerFeedbackRecord])
def get_case_feedback(case_id: str, actor: AuthenticatedActor = Depends(get_current_actor)) -> list[ReviewerFeedbackRecord]:
    case = CASE_STORE.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    require_case_site_access(actor, case.site)
    return case.review_feedback


@router.get("/{case_id}/feedback/recommendation", response_model=FeedbackRecommendation)
def get_case_feedback_recommendation(
    case_id: str,
    actor: AuthenticatedActor = Depends(get_current_actor),
) -> FeedbackRecommendation:
    case = CASE_STORE.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    require_case_site_access(actor, case.site)
    hybrid = analyze_hybrid_report(
        report_text=case.report_text,
        score=case.score,
        urgency=case.urgency,
        rationale_codes=case.rationale_codes,
        evidence=case.evidence,
    )
    return recommend_case_feedback(case, hybrid)


@router.post("/{case_id}/feedback", response_model=ReviewerFeedbackResult)
def submit_case_feedback(
    case_id: str,
    payload: ReviewerFeedbackInput,
    actor: AuthenticatedActor = Depends(require_roles("reviewer", "navigator", "admin")),
) -> ReviewerFeedbackResult:
    case = CASE_STORE.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    require_case_site_access(actor, case.site)
    effective_payload = payload.model_copy(update={"reviewer": actor.user_id})
    feedback = CASE_STORE.add_review_feedback(case_id, effective_payload)
    return ReviewerFeedbackResult(
        ok=True,
        case_id=case_id,
        reviewer=feedback.reviewer,
        label=feedback.label,
        disposition=feedback.disposition,
    )
