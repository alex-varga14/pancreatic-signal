from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ResearchOpportunityType = Literal[
    "rule_gap",
    "benchmark_gap",
    "trial_catalog_gap",
    "case_brief",
    "community_project",
    "external_tooling",
]

ResearchPromotionTarget = Literal["github_issue", "docs_draft", "benchmark_task"]
ResearchIngestMode = Literal["auto", "seeded", "fixture", "live"]


class ResearchSource(BaseModel):
    source_id: str
    label: str
    source_kind: str
    trust_level: str
    access_class: str
    base_url: str | None = None
    description: str | None = None
    polling_config: dict[str, object] = Field(default_factory=dict)
    enabled: bool = True
    connector_id: str | None = None
    default_mode: ResearchIngestMode | None = None
    live_ready: bool = False
    schedule_summary: str | None = None
    health_status: str = "idle"
    last_run_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error_at: datetime | None = None
    last_error_detail: str | None = None
    last_document_count: int | None = None


class ResearchRunItem(BaseModel):
    item_index: int
    stage: str
    status: str
    source_identifier: str | None = None
    document_id: str | None = None
    error_bucket: str | None = None
    error_detail: str | None = None
    created_at: datetime


class ResearchRunSummary(BaseModel):
    run_id: int
    run_type: str
    status: str
    actor_user_id: str
    source_scope: list[str] = Field(default_factory=list)
    processed: int
    created: int
    updated: int
    failed: int
    failure_counts: dict[str, int] = Field(default_factory=dict)
    artifact_paths: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    started_at: datetime
    completed_at: datetime


class ResearchRunDetail(ResearchRunSummary):
    items: list[ResearchRunItem] = Field(default_factory=list)


class ResearchRunTriggerInput(BaseModel):
    source_ids: list[str] | None = None
    include_disabled: bool = False
    write_artifacts: bool = True
    mode: ResearchIngestMode = "auto"
    max_documents_per_source: int | None = Field(default=None, ge=1, le=50)


class ResearchDigestTriggerInput(BaseModel):
    publish: bool = True
    write_artifacts: bool = True


class ResearchRunTriggerResult(BaseModel):
    ok: bool
    run: ResearchRunDetail


class ResearchEvidence(BaseModel):
    evidence_text: str
    char_start: int
    char_end: int
    claim_text: str
    claim_type: str
    entity_tags: list[str] = Field(default_factory=list)
    citation_label: str | None = None
    confidence: float | None = None


class ResearchGraphEntity(BaseModel):
    node_id: str
    label: str
    node_type: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    topic_ids: list[str] = Field(default_factory=list)
    match_terms: list[str] = Field(default_factory=list)
    related_node_ids: list[str] = Field(default_factory=list)
    confidence: float | None = None


class ResearchDocument(BaseModel):
    document_id: str
    source_id: str
    source_label: str
    source_kind: str
    document_type: str
    title: str
    abstract_text: str
    url: str | None = None
    canonical_url: str | None = None
    doi: str | None = None
    pmid: str | None = None
    nct_id: str | None = None
    citation_key: str
    published_at: datetime | None = None
    authors: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    topic_ids: list[str] = Field(default_factory=list)
    topic_labels: list[str] = Field(default_factory=list)
    entity_tags: list[str] = Field(default_factory=list)
    relevance_scores: dict[str, float] = Field(default_factory=dict)
    novelty_score: float | None = None
    ingest_mode: str | None = None
    provenance: dict[str, object] = Field(default_factory=dict)
    graph_entities: list[ResearchGraphEntity] = Field(default_factory=list)
    evidence: list[ResearchEvidence] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ResearchTopic(BaseModel):
    topic_id: str
    label: str
    description: str | None = None
    keywords: list[str] = Field(default_factory=list)
    related_rationale_codes: list[str] = Field(default_factory=list)
    related_trial_tags: list[str] = Field(default_factory=list)
    opportunity_types: list[ResearchOpportunityType] = Field(default_factory=list)
    topic_heat: float
    document_count: int
    last_document_at: datetime | None = None
    status: str


class ResearchDigestDocumentRef(BaseModel):
    document_id: str
    title: str
    citation_key: str
    url: str | None = None
    topic_labels: list[str] = Field(default_factory=list)


class ResearchGraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    weight: float | None = None


class ResearchGraphNode(BaseModel):
    node_id: str
    label: str
    node_type: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    topic_ids: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    related_node_ids: list[str] = Field(default_factory=list)
    document_count: int
    heat: float
    recent_document_ids: list[str] = Field(default_factory=list)


class ResearchGraphSnapshot(BaseModel):
    generated_at: datetime
    active_node_ids: list[str] = Field(default_factory=list)
    nodes: list[ResearchGraphNode] = Field(default_factory=list)
    edges: list[ResearchGraphEdge] = Field(default_factory=list)


class ResearchCouncilStage1Opinion(BaseModel):
    persona: str
    focus: str
    summary: str
    citations: list[str] = Field(default_factory=list)
    proposed_opportunity_types: list[ResearchOpportunityType] = Field(default_factory=list)
    primary_topics: list[str] = Field(default_factory=list)
    confidence_label: str = "medium"
    key_claims: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)


class ResearchCouncilPeerCritique(BaseModel):
    reviewer_persona: str
    target_persona: str
    alignment: str
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    requested_evidence: list[str] = Field(default_factory=list)


class ResearchCouncilStage2Ranking(BaseModel):
    persona: str
    ranked_topics: list[str] = Field(default_factory=list)
    ranked_opportunity_types: list[ResearchOpportunityType] = Field(default_factory=list)
    critique: str
    challenge_target_persona: str | None = None
    peer_critiques: list[ResearchCouncilPeerCritique] = Field(default_factory=list)
    preferred_actions: list[str] = Field(default_factory=list)
    confidence_adjustment: str = "hold"


class ResearchCouncilStage3Synthesis(BaseModel):
    chairman_summary: str
    overall_confidence: str = "medium"
    consensus_points: list[str] = Field(default_factory=list)
    disagreement_points: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    next_experiments: list[str] = Field(default_factory=list)
    promotion_guardrails: list[str] = Field(default_factory=list)


class ResearchCouncilPayload(BaseModel):
    stage_1: list[ResearchCouncilStage1Opinion] = Field(default_factory=list)
    stage_2: list[ResearchCouncilStage2Ranking] = Field(default_factory=list)
    stage_3: ResearchCouncilStage3Synthesis


class ResearchDigestListItem(BaseModel):
    digest_id: str
    title: str
    status: str
    publication_scope: str
    generated_at: datetime
    topic_ids: list[str] = Field(default_factory=list)
    topic_labels: list[str] = Field(default_factory=list)
    disagreement_score: float
    citation_count: int


class ResearchDigestDetail(ResearchDigestListItem):
    window_start: datetime | None = None
    window_end: datetime | None = None
    summary_markdown: str
    key_takeaways: list[str] = Field(default_factory=list)
    supporting_documents: list[ResearchDigestDocumentRef] = Field(default_factory=list)
    council: ResearchCouncilPayload


class ResearchOpportunity(BaseModel):
    opportunity_id: str
    opportunity_type: ResearchOpportunityType
    title: str
    summary: str
    status: str
    confidence_score: float
    topic_ids: list[str] = Field(default_factory=list)
    topic_labels: list[str] = Field(default_factory=list)
    supporting_document_ids: list[str] = Field(default_factory=list)
    related_rationale_codes: list[str] = Field(default_factory=list)
    related_trial_ids: list[str] = Field(default_factory=list)
    action_payload: dict[str, object] = Field(default_factory=dict)
    promotion_target: str | None = None
    promoted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ResearchPromotionInput(BaseModel):
    target: ResearchPromotionTarget = "docs_draft"


class ResearchPromotionResult(BaseModel):
    ok: bool
    opportunity_id: str
    status: str
    promotion_target: ResearchPromotionTarget
    artifact_path: str | None = None


class ResearchCaseBriefTopic(BaseModel):
    topic_id: str
    label: str
    rationale: str


class ResearchCaseBriefDocument(BaseModel):
    document_id: str
    title: str
    citation_key: str
    url: str | None = None
    relevance_reason: str


class ResearchCaseBrief(BaseModel):
    case_id: str
    summary: str
    matched_topics: list[ResearchCaseBriefTopic] = Field(default_factory=list)
    supporting_documents: list[ResearchCaseBriefDocument] = Field(default_factory=list)
    suggested_benchmark_gaps: list[str] = Field(default_factory=list)
    suggested_rule_updates: list[str] = Field(default_factory=list)
    suggested_trial_updates: list[str] = Field(default_factory=list)
