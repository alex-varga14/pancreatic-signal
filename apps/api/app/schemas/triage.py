from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.hybrid import HybridAnalysis


class ImportMetadata(BaseModel):
    patient_identifier: str | None = None
    encounter_identifier: str | None = None
    accession_number: str | None = None
    ordering_provider: str | None = None
    source_system: str | None = None
    source_format: str | None = None
    import_source_id: str | None = None


class ReportInput(BaseModel):
    report_id: str
    case_id: str
    report_datetime: datetime
    modality: str
    report_text: str
    site: str | None = None
    import_metadata: ImportMetadata | None = None


class EvidenceSpan(BaseModel):
    text: str
    section: str = "unknown"
    start: int
    end: int
    code: str
    sentence_index: int | None = None


class TriageResult(BaseModel):
    report_id: str
    case_id: str
    score: float = Field(ge=0.0, le=1.0)
    urgency: str
    rationale_codes: list[str]
    evidence: list[EvidenceSpan]
    hybrid_analysis: HybridAnalysis | None = None


class BatchTriageRequest(BaseModel):
    reports: list[ReportInput]


class BatchTriageResponse(BaseModel):
    processed: int
    flagged: int
    results: list[TriageResult]
