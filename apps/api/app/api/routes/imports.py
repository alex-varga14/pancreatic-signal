from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, Request, UploadFile, status

from app.auth import actor_can_access_site, require_roles
from app.schemas.auth import AuthenticatedActor
from app.schemas.imports import ImportAuditItem, ImportRunDetail, ImportRunSummary, ReportImportSummary
from app.schemas.triage import ReportInput
from app.services.fhir_imports import parse_fhir_diagnostic_report_payload
from app.services.hl7_imports import parse_hl7_oru_messages
from app.services.imports import ImportParseError, categorize_import_parse_error, parse_report_upload
from app.services.triage_engine import triage_report
from app.store.memory_store import CASE_STORE

router = APIRouter()


@router.post("/reports", response_model=ReportImportSummary)
async def import_reports(
    file: UploadFile = File(...),
    actor: AuthenticatedActor = Depends(require_roles("analyst", "navigator", "admin")),
) -> ReportImportSummary:
    raw_bytes = await file.read()
    started_at = datetime.now(timezone.utc)
    source_format = _detect_upload_source_format(file.filename, file.content_type)

    try:
        source_format, reports = parse_report_upload(
            filename=file.filename,
            content_type=file.content_type,
            raw_bytes=raw_bytes,
        )
    except ImportParseError as exc:
        run = _record_failed_import_run(
            actor=actor,
            source_format=source_format,
            source_name=file.filename,
            started_at=started_at,
            failure_bucket=categorize_import_parse_error(exc),
            failure_detail=str(exc),
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
            headers={"X-Import-Run-ID": str(run.run_id)},
        ) from exc

    return _process_import_reports(
        actor=actor,
        source_format=source_format,
        source_name=file.filename,
        reports=reports,
        started_at=started_at,
    )


@router.post("/fhir/diagnostic-reports", response_model=ReportImportSummary)
def import_fhir_diagnostic_reports(
    payload: dict[str, Any] | list[dict[str, Any]] = Body(...),
    actor: AuthenticatedActor = Depends(require_roles("analyst", "navigator", "admin")),
) -> ReportImportSummary:
    started_at = datetime.now(timezone.utc)
    source_format = "fhir-diagnostic-report"

    try:
        reports = parse_fhir_diagnostic_report_payload(payload)
    except ImportParseError as exc:
        run = _record_failed_import_run(
            actor=actor,
            source_format=source_format,
            source_name=None,
            started_at=started_at,
            failure_bucket=categorize_import_parse_error(exc),
            failure_detail=str(exc),
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
            headers={"X-Import-Run-ID": str(run.run_id)},
        ) from exc

    return _process_import_reports(
        actor=actor,
        source_format=source_format,
        source_name=None,
        reports=reports,
        started_at=started_at,
    )


@router.post("/hl7/oru", response_model=ReportImportSummary)
async def import_hl7_oru_results(
    request: Request,
    actor: AuthenticatedActor = Depends(require_roles("analyst", "navigator", "admin")),
) -> ReportImportSummary:
    started_at = datetime.now(timezone.utc)
    source_format = "hl7-oru"
    raw_text = (await request.body()).decode("utf-8-sig")

    try:
        reports = parse_hl7_oru_messages(raw_text)
    except ImportParseError as exc:
        run = _record_failed_import_run(
            actor=actor,
            source_format=source_format,
            source_name=None,
            started_at=started_at,
            failure_bucket=categorize_import_parse_error(exc),
            failure_detail=str(exc),
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
            headers={"X-Import-Run-ID": str(run.run_id)},
        ) from exc

    return _process_import_reports(
        actor=actor,
        source_format=source_format,
        source_name=None,
        reports=reports,
        started_at=started_at,
    )


@router.get("/runs", response_model=list[ImportRunSummary])
def list_import_runs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    actor: AuthenticatedActor = Depends(require_roles("analyst", "navigator", "admin")),
) -> list[ImportRunSummary]:
    return CASE_STORE.list_import_runs(
        actor_user_id=actor.user_id,
        accessible_sites=actor.site_scope,
        limit=limit,
        offset=offset,
    )


@router.get("/runs/{run_id}", response_model=ImportRunDetail)
def get_import_run(
    run_id: int,
    actor: AuthenticatedActor = Depends(require_roles("analyst", "navigator", "admin")),
) -> ImportRunDetail:
    run = CASE_STORE.get_import_run(run_id, actor_user_id=actor.user_id, accessible_sites=actor.site_scope)
    if run is None:
        raise HTTPException(status_code=404, detail="Import run not found")
    return run


def _process_import_reports(
    *,
    actor: AuthenticatedActor,
    source_format: str,
    source_name: str | None,
    reports: list[ReportInput],
    started_at: datetime,
) -> ReportImportSummary:
    blocked_reports = [report for report in reports if not actor_can_access_site(actor, report.site)]
    blocked_sites = sorted({report.site or "<missing site>" for report in blocked_reports})
    imported_sites = _sorted_sites(reports)

    if blocked_reports:
        run = CASE_STORE.record_import_run(
            source_format=source_format,
            source_name=source_name,
            actor_user_id=actor.user_id,
            actor_role=actor.role,
            actor_site_scope=actor.site_scope,
            imported_sites=imported_sites,
            status="failed",
            processed=0,
            flagged=0,
            created=0,
            updated=0,
            failed=len(blocked_reports),
            failure_counts={"site_scope_rejection": len(blocked_reports)},
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            items=[
                ImportAuditItem(
                    item_index=index,
                    status="failed",
                    source_identifier=_source_identifier(report),
                    site=report.site,
                    case_id=report.case_id,
                    report_id=report.report_id,
                    error_bucket="site_scope_rejection",
                    error_detail=f"Actor '{actor.user_id}' cannot import site '{report.site or '<missing site>'}'.",
                )
                for index, report in enumerate(blocked_reports, start=1)
            ],
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Actor '{actor.user_id}' cannot import reports for site(s): "
                f"{', '.join(blocked_sites)}."
            ),
            headers={"X-Import-Run-ID": str(run.run_id)},
        )

    upsert_outcomes = CASE_STORE.classify_import_upserts(reports)
    results = [triage_report(report) for report in reports]
    flagged = sum(1 for result in results if result.score >= 0.30)
    created = sum(1 for report in reports if upsert_outcomes.get(report.report_id) == "created")
    updated = sum(1 for report in reports if upsert_outcomes.get(report.report_id) == "updated")

    run = CASE_STORE.record_import_run(
        source_format=source_format,
        source_name=source_name,
        actor_user_id=actor.user_id,
        actor_role=actor.role,
        actor_site_scope=actor.site_scope,
        imported_sites=imported_sites,
        status="completed",
        processed=len(results),
        flagged=flagged,
        created=created,
        updated=updated,
        failed=0,
        failure_counts={},
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        items=[
            ImportAuditItem(
                item_index=index,
                status="imported",
                source_identifier=_source_identifier(report),
                site=report.site,
                case_id=result.case_id,
                report_id=result.report_id,
            )
            for index, (report, result) in enumerate(zip(reports, results, strict=True), start=1)
        ],
    )

    return ReportImportSummary(
        run_id=run.run_id,
        processed=len(results),
        flagged=flagged,
        created=created,
        updated=updated,
        failed=0,
        failure_counts={},
        source_format=source_format,
        case_ids=[result.case_id for result in results],
        report_ids=[result.report_id for result in results],
    )


def _record_failed_import_run(
    *,
    actor: AuthenticatedActor,
    source_format: str,
    source_name: str | None,
    started_at: datetime,
    failure_bucket: str,
    failure_detail: str,
) -> ImportRunSummary:
    return CASE_STORE.record_import_run(
        source_format=source_format,
        source_name=source_name,
        actor_user_id=actor.user_id,
        actor_role=actor.role,
        actor_site_scope=actor.site_scope,
        imported_sites=[],
        status="failed",
        processed=0,
        flagged=0,
        created=0,
        updated=0,
        failed=1,
        failure_counts={failure_bucket: 1},
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        items=[],
    )


def _sorted_sites(reports: list[ReportInput]) -> list[str]:
    return sorted({report.site for report in reports if report.site})


def _source_identifier(report: ReportInput) -> str:
    if report.import_metadata and report.import_metadata.import_source_id:
        return report.import_metadata.import_source_id
    return report.report_id


def _detect_upload_source_format(filename: str | None, content_type: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    content_type = (content_type or "").lower()

    if suffix == ".csv" or content_type in {"text/csv", "application/csv"}:
        return "csv"
    if suffix in {".jsonl", ".ndjson"} or content_type in {
        "application/x-ndjson",
        "application/jsonl",
        "application/jsonlines",
    }:
        return "jsonl"
    if suffix == ".json" or content_type == "application/json":
        return "json"
    return "unknown-upload"
