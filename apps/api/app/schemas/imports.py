from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ImportFailureBucket = Literal[
    "parse_error",
    "validation_error",
    "unsupported_payload",
    "site_scope_rejection",
]
ImportRunStatus = Literal["completed", "failed"]
ImportRunItemStatus = Literal["imported", "failed"]


class ReportImportSummary(BaseModel):
    run_id: int | None = None
    processed: int
    flagged: int
    created: int = 0
    updated: int = 0
    failed: int = 0
    failure_counts: dict[ImportFailureBucket, int] = Field(default_factory=dict)
    source_format: str
    case_ids: list[str]
    report_ids: list[str]


class ImportAuditItem(BaseModel):
    item_index: int
    status: ImportRunItemStatus
    source_identifier: str | None = None
    site: str | None = None
    case_id: str | None = None
    report_id: str | None = None
    error_bucket: ImportFailureBucket | None = None
    error_detail: str | None = None


class ImportRunSummary(BaseModel):
    run_id: int
    source_format: str
    source_name: str | None = None
    actor_user_id: str
    actor_role: str
    actor_site_scope: list[str] | None = None
    imported_sites: list[str] = Field(default_factory=list)
    status: ImportRunStatus
    processed: int
    flagged: int
    created: int
    updated: int
    failed: int
    failure_counts: dict[ImportFailureBucket, int] = Field(default_factory=dict)
    started_at: datetime
    completed_at: datetime


class ImportRunDetail(ImportRunSummary):
    items: list[ImportAuditItem] = Field(default_factory=list)
