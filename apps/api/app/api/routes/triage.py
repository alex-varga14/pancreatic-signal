from fastapi import APIRouter

from app.schemas.triage import BatchTriageRequest, BatchTriageResponse, ReportInput, TriageResult
from app.services.triage_engine import triage_report

router = APIRouter()


@router.post("/report", response_model=TriageResult)
def triage_single_report(payload: ReportInput) -> TriageResult:
    return triage_report(payload)


@router.post("/batch", response_model=BatchTriageResponse)
def triage_batch(payload: BatchTriageRequest) -> BatchTriageResponse:
    results = [triage_report(report) for report in payload.reports]
    flagged = sum(1 for result in results if result.score >= 0.30)
    return BatchTriageResponse(processed=len(results), flagged=flagged, results=results)
