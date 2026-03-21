from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CaseRecord(Base):
    __tablename__ = "cases"

    case_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    report_id: Mapped[str] = mapped_column(String(128), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    urgency: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="new")
    site: Mapped[str | None] = mapped_column(String(255), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rationale_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    reports: Mapped[list["ReportRecord"]] = relationship(back_populates="case")
    findings: Mapped[list["FindingRecord"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    review_actions: Mapped[list["ReviewActionRecord"]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )


class ReportRecord(Base):
    __tablename__ = "reports"

    report_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False, index=True)
    report_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    modality: Mapped[str] = mapped_column(String(64), nullable=False)
    site: Mapped[str | None] = mapped_column(String(255), nullable=True)
    patient_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    encounter_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    accession_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ordering_provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_system: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_format: Mapped[str | None] = mapped_column(String(64), nullable=True)
    import_source_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    case: Mapped[CaseRecord] = relationship(back_populates="reports")


class FindingRecord(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False, index=True)
    report_id: Mapped[str] = mapped_column(ForeignKey("reports.report_id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    section: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    sentence_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    score_contribution: Mapped[float | None] = mapped_column(Float, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    case: Mapped[CaseRecord] = relationship(back_populates="findings")


class ReviewActionRecord(Base):
    __tablename__ = "review_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    case: Mapped[CaseRecord] = relationship(back_populates="review_actions")


class ImportRunRecord(Base):
    __tablename__ = "import_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_format: Mapped[str] = mapped_column(String(64), nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_site_scope: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    imported_sites: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    flagged_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_counts: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    items: Mapped[list["ImportRunItemRecord"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class ImportRunItemRecord(Base):
    __tablename__ = "import_run_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("import_runs.id"), nullable=False, index=True)
    item_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_identifier: Mapped[str | None] = mapped_column(String(512), nullable=True)
    site: Mapped[str | None] = mapped_column(String(255), nullable=True)
    case_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    report_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_bucket: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    run: Mapped[ImportRunRecord] = relationship(back_populates="items")
