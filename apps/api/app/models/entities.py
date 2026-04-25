from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
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


class ResearchSourceRecord(Base):
    __tablename__ = "research_sources"

    source_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    trust_level: Mapped[str] = mapped_column(String(32), nullable=False)
    access_class: Mapped[str] = mapped_column(String(32), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    polling_config: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )


class ResearchRunRecord(Base):
    __tablename__ = "research_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_scope: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_counts: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)
    artifact_paths: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    items: Mapped[list["ResearchRunItemRecord"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class ResearchRunItemRecord(Base):
    __tablename__ = "research_run_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("research_runs.id"), nullable=False, index=True)
    item_index: Mapped[int] = mapped_column(Integer, nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    source_identifier: Mapped[str | None] = mapped_column(String(512), nullable=True)
    document_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_bucket: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    run: Mapped[ResearchRunRecord] = relationship(back_populates="items")


class ResearchDocumentRecord(Base):
    __tablename__ = "research_documents"

    document_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("research_sources.source_id"), nullable=False, index=True)
    source_identifier: Mapped[str | None] = mapped_column(String(512), nullable=True)
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pmid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nct_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    citation_key: Mapped[str] = mapped_column(String(255), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    authors: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    organizations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    topic_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    entity_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    relevance_scores: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    raw_metadata: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    evidence: Mapped[list["ResearchEvidenceRecord"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class ResearchEvidenceRecord(Base):
    __tablename__ = "research_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("research_documents.document_id"),
        nullable=False,
        index=True,
    )
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    citation_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    document: Mapped[ResearchDocumentRecord] = relationship(back_populates="evidence")


class ResearchTopicRecord(Base):
    __tablename__ = "research_topics"

    topic_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    related_rationale_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    related_trial_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    opportunity_types: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    topic_heat: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_document_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )


class ResearchDigestRecord(Base):
    __tablename__ = "research_digests"

    digest_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    publication_scope: Mapped[str] = mapped_column(String(32), nullable=False, default="public")
    window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    topic_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    supporting_document_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    council_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    summary_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    summary_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    disagreement_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    citation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )


class ResearchOpportunityRecord(Base):
    __tablename__ = "research_opportunities"

    opportunity_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    opportunity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="proposed")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    topic_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    supporting_document_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    related_rationale_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    related_trial_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    action_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    promotion_target: Mapped[str | None] = mapped_column(String(64), nullable=True)
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )
