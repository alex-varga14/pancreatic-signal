from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_actor, require_case_site_access, require_roles
from app.schemas.auth import AuthenticatedActor
from app.schemas.research_intel import (
    ResearchCaseBrief,
    ResearchDigestDetail,
    ResearchDigestListItem,
    ResearchDigestTriggerInput,
    ResearchDocument,
    ResearchExperimentInput,
    ResearchGraphSnapshot,
    ResearchOpportunity,
    ResearchPromotionInput,
    ResearchPromotionResult,
    ResearchRunDetail,
    ResearchRunSummary,
    ResearchScheduleSnapshot,
    ResearchRunTriggerInput,
    ResearchRunTriggerResult,
    ResearchSource,
    ResearchTopic,
)
from app.services.research_intel import (
    build_research_case_brief,
    get_research_digest,
    get_research_graph_snapshot,
    get_research_run,
    list_research_digests,
    list_research_documents,
    list_research_opportunities,
    list_research_runs,
    list_research_schedule,
    list_research_sources,
    list_research_topics,
    promote_research_opportunity,
    run_research_digest,
    run_research_ingest,
    run_research_opportunity_experiment,
)
from app.store.memory_store import CASE_STORE

router = APIRouter()


@router.get("/sources", response_model=list[ResearchSource])
def get_sources() -> list[ResearchSource]:
    return list_research_sources()


@router.get("/schedule", response_model=ResearchScheduleSnapshot)
def get_schedule() -> ResearchScheduleSnapshot:
    return list_research_schedule()


@router.get("/documents", response_model=list[ResearchDocument])
def get_documents(
    source_kind: str | None = None,
    topic: str | None = None,
    q: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ResearchDocument]:
    return list_research_documents(
        source_kind=source_kind,
        topic=topic,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get("/topics", response_model=list[ResearchTopic])
def get_topics() -> list[ResearchTopic]:
    return list_research_topics()


@router.get("/graph", response_model=ResearchGraphSnapshot)
def get_graph() -> ResearchGraphSnapshot:
    return get_research_graph_snapshot()


@router.get("/digests", response_model=list[ResearchDigestListItem])
def get_digests() -> list[ResearchDigestListItem]:
    return list_research_digests()


@router.get("/digests/{digest_id}", response_model=ResearchDigestDetail)
def get_digest(digest_id: str) -> ResearchDigestDetail:
    digest = get_research_digest(digest_id)
    if digest is None:
        raise HTTPException(status_code=404, detail="Digest not found")
    return digest


@router.get("/opportunities", response_model=list[ResearchOpportunity])
def get_opportunities(
    opportunity_type: str | None = None,
    status: str | None = None,
    topic: str | None = None,
) -> list[ResearchOpportunity]:
    return list_research_opportunities(
        opportunity_type=opportunity_type,
        status=status,
        topic=topic,
    )


@router.get("/runs", response_model=list[ResearchRunSummary])
def get_runs(
    limit: int = Query(default=20, ge=1, le=200),
    actor: AuthenticatedActor = Depends(require_roles("analyst", "navigator", "admin")),
) -> list[ResearchRunSummary]:
    del actor
    return list_research_runs(limit=limit)


@router.get("/runs/{run_id}", response_model=ResearchRunDetail)
def get_run(
    run_id: int,
    actor: AuthenticatedActor = Depends(require_roles("analyst", "navigator", "admin")),
) -> ResearchRunDetail:
    del actor
    run = get_research_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    return run


@router.post("/runs/ingest", response_model=ResearchRunTriggerResult)
def trigger_ingest(
    payload: ResearchRunTriggerInput,
    actor: AuthenticatedActor = Depends(require_roles("analyst", "navigator", "admin")),
) -> ResearchRunTriggerResult:
    run = run_research_ingest(
        actor_user_id=actor.user_id,
        source_ids=payload.source_ids,
        include_disabled=payload.include_disabled,
        only_due=payload.only_due,
        write_artifacts=payload.write_artifacts,
        mode=payload.mode,
        max_documents_per_source=payload.max_documents_per_source,
    )
    return ResearchRunTriggerResult(ok=True, run=run)


@router.post("/runs/digest", response_model=ResearchRunTriggerResult)
def trigger_digest(
    payload: ResearchDigestTriggerInput,
    actor: AuthenticatedActor = Depends(require_roles("analyst", "navigator", "admin")),
) -> ResearchRunTriggerResult:
    run = run_research_digest(
        actor_user_id=actor.user_id,
        publish=payload.publish,
        write_artifacts=payload.write_artifacts,
    )
    return ResearchRunTriggerResult(ok=True, run=run)


@router.post("/opportunities/{opportunity_id}/promote", response_model=ResearchPromotionResult)
def promote_opportunity(
    opportunity_id: str,
    payload: ResearchPromotionInput,
    actor: AuthenticatedActor = Depends(require_roles("analyst", "navigator", "admin")),
) -> ResearchPromotionResult:
    opportunity, artifact_path = promote_research_opportunity(
        opportunity_id=opportunity_id,
        actor_user_id=actor.user_id,
        target=payload.target,
    )
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return ResearchPromotionResult(
        ok=True,
        opportunity_id=opportunity.opportunity_id,
        status=opportunity.status,
        promotion_target=payload.target,
        artifact_path=artifact_path,
    )


@router.post("/opportunities/{opportunity_id}/experiment", response_model=ResearchRunTriggerResult)
def run_opportunity_experiment(
    opportunity_id: str,
    payload: ResearchExperimentInput,
    actor: AuthenticatedActor = Depends(require_roles("analyst", "navigator", "admin")),
) -> ResearchRunTriggerResult:
    try:
        run = run_research_opportunity_experiment(
            opportunity_id=opportunity_id,
            actor_user_id=actor.user_id,
            write_artifacts=payload.write_artifacts,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if run is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return ResearchRunTriggerResult(ok=True, run=run)


@router.get("/cases/{case_id}/brief", response_model=ResearchCaseBrief)
def get_case_brief(
    case_id: str,
    actor: AuthenticatedActor = Depends(get_current_actor),
) -> ResearchCaseBrief:
    case = CASE_STORE.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    require_case_site_access(actor, case.site)
    brief = build_research_case_brief(case_id)
    if brief is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return brief
