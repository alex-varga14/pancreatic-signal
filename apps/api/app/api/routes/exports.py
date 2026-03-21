import csv
import io
import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.auth import require_roles, validate_requested_site_access
from app.schemas.auth import AuthenticatedActor
from app.services.deidentification import deidentify_case_export_row, deidentify_feedback_export_row
from app.store.memory_store import CASE_STORE

router = APIRouter()


@router.get("/cases.csv")
def export_cases_csv(
    status: str | None = None,
    urgency: str | None = None,
    site: str | None = None,
    reviewer: str | None = None,
    redact: bool = Query(default=False),
    actor: AuthenticatedActor = Depends(require_roles("analyst", "navigator", "admin")),
) -> Response:
    site = validate_requested_site_access(actor, site)
    rows = CASE_STORE.export_cases(
        status=status,
        urgency=urgency,
        site=site,
        accessible_sites=actor.site_scope,
        reviewer=reviewer,
    )
    if redact:
        rows = [deidentify_case_export_row(row) for row in rows]
    else:
        rows = [{**row, "deidentified": False} for row in rows]

    buffer = io.StringIO()
    fieldnames = [
        "case_id",
        "report_id",
        "report_datetime",
        "modality",
        "patient_identifier",
        "encounter_identifier",
        "accession_number",
        "ordering_provider",
        "source_system",
        "source_format",
        "import_source_id",
        "score",
        "hybrid_score",
        "hybrid_delta",
        "urgency",
        "disagreement_level",
        "status",
        "site",
        "assigned_to",
        "top_rationale",
        "review_feedback_count",
        "latest_feedback_label",
        "latest_feedback_disposition",
        "rationale_codes",
        "evidence_count",
        "review_action_count",
        "deidentified",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="cases.csv"'},
    )


@router.get("/review-feedback.jsonl")
def export_review_feedback_jsonl(
    redact: bool = Query(default=False),
    actor: AuthenticatedActor = Depends(require_roles("analyst", "navigator", "admin")),
) -> Response:
    rows = CASE_STORE.export_review_feedback(accessible_sites=actor.site_scope)
    if redact:
        rows = [deidentify_feedback_export_row(row) for row in rows]
    payload = "".join(json.dumps(row) + "\n" for row in rows)
    return Response(
        content=payload,
        media_type="application/x-ndjson",
        headers={"Content-Disposition": 'attachment; filename="review-feedback.jsonl"'},
    )
