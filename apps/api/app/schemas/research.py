from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class RedactionSummary(BaseModel):
    mode: str = "length_preserving_phi_mask"
    redaction_count: int
    redacted_characters: int
    categories: dict[str, int]
    pseudonymized_fields: list[str]


class ResearchEvidenceSpan(BaseModel):
    text: str
    section: str = "unknown"
    start: int
    end: int
    code: str
    sentence_index: int | None = None


class ResearchReviewAction(BaseModel):
    action: str
    reviewer: str
    note: str | None = None
    assigned_to: str | None = None
    created_date: date


class ResearchReviewerFeedbackRecord(BaseModel):
    reviewer: str
    label: str
    disposition: str
    error_bucket: str | None = None
    notes: str | None = None
    created_date: date


class ResearchImportMetadata(BaseModel):
    patient_identifier: str | None = None
    encounter_identifier: str | None = None
    accession_number: str | None = None
    ordering_provider: str | None = None
    source_system: str | None = None
    source_format: str | None = None
    import_source_id: str | None = None


class ResearchCaseListItem(BaseModel):
    case_id: str
    report_id: str
    report_date: date | None = None
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
    deidentified: bool = True


class ResearchCaseDetail(BaseModel):
    case_id: str
    report_id: str
    report_date: date | None = None
    modality: str | None = None
    score: float
    urgency: str
    status: str
    site: str | None = None
    assigned_to: str | None = None
    report_text: str
    import_metadata: ResearchImportMetadata | None = None
    rationale_codes: list[str]
    evidence: list[ResearchEvidenceSpan]
    review_actions: list[ResearchReviewAction]
    review_feedback: list[ResearchReviewerFeedbackRecord]
    redaction_summary: RedactionSummary
    deidentified: bool = True
