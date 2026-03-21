from __future__ import annotations

import json
from datetime import datetime

from app.schemas.feedback import ReviewerFeedbackInput, ReviewerFeedbackRecord


def serialize_feedback_note(payload: ReviewerFeedbackInput) -> str:
    return json.dumps(
        {
            "label": payload.label,
            "disposition": payload.disposition,
            "error_bucket": payload.error_bucket,
            "notes": payload.notes,
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def parse_feedback_note(
    *,
    reviewer: str,
    note: str | None,
    created_at: datetime,
) -> ReviewerFeedbackRecord | None:
    if not note:
        return None

    try:
        payload = json.loads(note)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    label = payload.get("label")
    disposition = payload.get("disposition")
    if not isinstance(label, str) or not isinstance(disposition, str):
        return None

    error_bucket = payload.get("error_bucket")
    notes = payload.get("notes")
    return ReviewerFeedbackRecord(
        reviewer=reviewer,
        label=label,
        disposition=disposition,
        error_bucket=error_bucket if isinstance(error_bucket, str) else None,
        notes=notes if isinstance(notes, str) and notes else None,
        created_at=created_at,
    )


def summarize_feedback(feedback: ReviewerFeedbackRecord) -> str:
    summary = f"label={feedback.label}, disposition={feedback.disposition}"
    if feedback.error_bucket:
        summary += f", bucket={feedback.error_bucket}"
    if feedback.notes:
        summary += f" ({feedback.notes})"
    return summary
