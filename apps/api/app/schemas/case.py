from datetime import datetime
from typing import Literal
from pydantic import BaseModel

from app.schemas.feedback import ReviewerFeedbackRecord
from app.schemas.triage import ImportMetadata


class Finding(BaseModel):
    """Structured persisted finding row exposed on case detail responses.

    The legacy evidence dict shape (text/section/start/end/code/sentence_index)
    is preserved verbatim and is enriched with the rationale family ``label``
    and the per-finding ``score_contribution`` resolved from the ontology
    scoring profile.
    """

    text: str
    section: str = "unknown"
    start: int
    end: int
    code: str
    label: str | None = None
    sentence_index: int | None = None
    score_contribution: float | None = None


class ReviewActionInput(BaseModel):
    action: str
    reviewer: str | None = None
    note: str | None = None
    assigned_to: str | None = None


class ReviewActionResult(BaseModel):
    ok: bool
    case_id: str
    action: str
    status: str
    assigned_to: str | None = None


class ReviewAction(BaseModel):
    action: str
    reviewer: str
    note: str | None = None
    assigned_to: str | None = None
    created_at: datetime


class CaseListItem(BaseModel):
    case_id: str
    report_id: str
    report_datetime: datetime | None = None
    modality: str | None = None
    score: float
    urgency: str
    status: str
    site: str | None = None
    assigned_to: str | None = None
    top_rationale: str | None = None
    hybrid_score: float | None = None
    hybrid_delta: float | None = None
    hybrid_confidence: str | None = None
    hybrid_review_priority: str | None = None
    active_learning_priority: str | None = None
    disagreement_level: str | None = None
    review_feedback_count: int = 0
    latest_feedback_label: str | None = None
    latest_feedback_disposition: str | None = None


class CaseDetail(BaseModel):
    case_id: str
    report_id: str
    report_datetime: datetime | None = None
    modality: str | None = None
    score: float
    urgency: str
    status: str
    site: str | None = None
    assigned_to: str | None = None
    report_text: str
    import_metadata: ImportMetadata | None = None
    rationale_codes: list[str]
    evidence: list[Finding]
    review_actions: list[ReviewAction]
    review_feedback: list[ReviewerFeedbackRecord]


CaseSortBy = Literal[
    "score",
    "hybrid_score",
    "hybrid_delta",
    "review_feedback_count",
    "urgency",
    "report_datetime",
    "case_id",
]
SortDirection = Literal["asc", "desc"]
