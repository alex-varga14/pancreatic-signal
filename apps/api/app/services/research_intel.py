from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select

from app.core.paths import resolve_data_path
from app.db.session import SessionLocal, init_db
from app.models import (
    ResearchDigestRecord,
    ResearchDocumentRecord,
    ResearchEvidenceRecord,
    ResearchOpportunityRecord,
    ResearchRunItemRecord,
    ResearchRunRecord,
    ResearchSourceRecord,
    ResearchTopicRecord,
)
from app.schemas.research_intel import (
    ResearchCaseBrief,
    ResearchCaseBriefDocument,
    ResearchCaseBriefTopic,
    ResearchOpportunityActionPayload,
    ResearchOpportunityArtifactSpec,
    ResearchOpportunityEvidence,
    ResearchOpportunityExperimentResult,
    ResearchCouncilPayload,
    ResearchCouncilPeerCritique,
    ResearchCouncilStage1Opinion,
    ResearchCouncilStage2Ranking,
    ResearchCouncilStage3Synthesis,
    ResearchDigestDetail,
    ResearchDigestDocumentRef,
    ResearchDigestListItem,
    ResearchDocument,
    ResearchEvidence,
    ResearchGraphEdge,
    ResearchGraphEntity,
    ResearchGraphNode,
    ResearchGraphSnapshot,
    ResearchIngestMode,
    ResearchOpportunity,
    ResearchPromotionTarget,
    ResearchRunDetail,
    ResearchRunItem,
    ResearchRunSummary,
    ResearchScheduleSnapshot,
    ResearchSource,
    ResearchTopic,
)
from app.services.research_intel_connectors import collect_research_documents_for_source
from app.services.trial_matching import match_case_to_trials
from app.store.memory_store import CASE_STORE

SOURCE_CATALOG_PATH = resolve_data_path("research", "sources.json")
TOPIC_CATALOG_PATH = resolve_data_path("research", "topics.json")
GRAPH_PATH = resolve_data_path("research", "pancreatic_oncology_graph.json")
SEED_DOCUMENTS_PATH = resolve_data_path("research", "seed_documents.json")

_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-]+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_TRUST_SCORES = {
    "high": 0.22,
    "medium": 0.12,
    "emerging": 0.06,
}
_PERSONAS = [
    {
        "persona": "literature_scout",
        "focus": "Track what changed across pancreatic oncology literature and trusted updates.",
    },
    {
        "persona": "translational_oncologist",
        "focus": "Prioritize evidence that could change screening, trials, or escalation pathways.",
    },
    {
        "persona": "open_source_builder",
        "focus": "Look for benchmark, tooling, and workflow opportunities for the open-source community.",
    },
]
_OPPORTUNITY_PERSONA_PRIORITY = {
    "rule_gap": ["translational_oncologist", "literature_scout"],
    "benchmark_gap": ["literature_scout", "open_source_builder"],
    "trial_catalog_gap": ["translational_oncologist", "literature_scout"],
    "case_brief": ["translational_oncologist"],
    "community_project": ["open_source_builder", "literature_scout"],
    "external_tooling": ["open_source_builder"],
}
_EXPERIMENT_SUPPORTED_OPPORTUNITY_TYPES = {"benchmark_gap", "rule_gap"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _artifact_root() -> Path:
    root = _repo_root() / "artifacts" / "research-intel"
    root.mkdir(parents=True, exist_ok=True)
    return root


@lru_cache(maxsize=1)
def load_research_source_catalog() -> list[dict[str, Any]]:
    with SOURCE_CATALOG_PATH.open() as handle:
        payload = json.load(handle)
    return list(payload.get("sources", []))


@lru_cache(maxsize=1)
def load_research_topic_catalog() -> list[dict[str, Any]]:
    with TOPIC_CATALOG_PATH.open() as handle:
        payload = json.load(handle)
    return list(payload.get("topics", []))


@lru_cache(maxsize=1)
def load_research_graph() -> dict[str, Any]:
    with GRAPH_PATH.open() as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def load_seed_research_documents() -> list[dict[str, Any]]:
    with SEED_DOCUMENTS_PATH.open() as handle:
        payload = json.load(handle)
    return list(payload.get("documents", []))


@lru_cache(maxsize=1)
def load_research_graph_indexes() -> dict[str, Any]:
    graph = load_research_graph()
    nodes = list(graph.get("nodes") or [])
    edges = list(graph.get("edges") or [])

    node_map = {
        str(node.get("node_id") or "").strip(): node
        for node in nodes
        if str(node.get("node_id") or "").strip()
    }
    neighbors: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        source = str(edge.get("source") or "").strip()
        target = str(edge.get("target") or "").strip()
        if source in node_map and target in node_map:
            neighbors[source].append(target)
            neighbors[target].append(source)

    indexed_nodes: list[dict[str, Any]] = []
    for node_id, node in node_map.items():
        terms = [
            str(node.get("label") or "").strip(),
            *[str(item).strip() for item in node.get("aliases") or []],
            *[str(item).strip() for item in node.get("keywords") or []],
        ]
        indexed_nodes.append(
            {
                **node,
                "node_id": node_id,
                "match_terms": sorted(
                    {term for term in terms if term},
                    key=lambda item: (-len(item), item.lower()),
                ),
                "related_node_ids": sorted(set(neighbors.get(node_id, []))),
            }
        )

    return {
        "nodes": indexed_nodes,
        "node_map": node_map,
        "neighbor_map": {key: sorted(set(value)) for key, value in neighbors.items()},
        "edges": edges,
    }


def validate_research_intel_catalogs() -> dict[str, int]:
    sources = load_research_source_catalog()
    topics = load_research_topic_catalog()
    graph = load_research_graph()
    documents = load_seed_research_documents()

    source_ids = [item["source_id"] for item in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Research source catalog contains duplicate source_id values.")

    topic_ids = [item["topic_id"] for item in topics]
    if len(topic_ids) != len(set(topic_ids)):
        raise ValueError("Research topic catalog contains duplicate topic_id values.")

    known_sources = set(source_ids)
    for item in documents:
        source_id = str(item.get("source_id") or "").strip()
        if source_id not in known_sources:
            raise ValueError(f"Seed research document references unknown source_id '{source_id}'.")

    graph_nodes = graph.get("nodes", [])
    if not isinstance(graph_nodes, list):
        raise ValueError("Research graph must contain a list of nodes.")
    graph_node_ids = {
        str(node.get("node_id") or "").strip()
        for node in graph_nodes
        if str(node.get("node_id") or "").strip()
    }
    if len(graph_node_ids) != len(graph_nodes):
        raise ValueError("Research graph contains duplicate or missing node_id values.")
    for edge in graph.get("edges", []):
        source = str(edge.get("source") or "").strip()
        target = str(edge.get("target") or "").strip()
        if source not in graph_node_ids or target not in graph_node_ids:
            raise ValueError(
                f"Research graph edge references unknown nodes: {source!r} -> {target!r}."
            )

    fixture_count = 0
    live_ready_count = 0
    for descriptor in sources:
        polling_config = descriptor.get("polling_config") or {}
        if _is_live_ready(polling_config):
            live_ready_count += 1
        fixture_path = str(polling_config.get("fixture_path") or "").strip()
        if not fixture_path:
            continue
        fixture_count += 1
        resolved = resolve_data_path("research", fixture_path)
        if not resolved.exists():
            raise ValueError(
                f"Research source '{descriptor['source_id']}' references missing fixture '{fixture_path}'."
            )

    return {
        "sources": len(sources),
        "topics": len(topics),
        "graph_nodes": len(graph_nodes),
        "documents": len(documents),
        "fixtures": fixture_count,
        "live_ready_sources": live_ready_count,
    }


def ensure_research_intel_seeded() -> None:
    init_db()
    with SessionLocal.begin() as session:
        existing_sources = {
            row.source_id: row
            for row in session.execute(select(ResearchSourceRecord)).scalars().all()
        }
        for descriptor in load_research_source_catalog():
            source_id = descriptor["source_id"]
            record = existing_sources.get(source_id)
            if record is None:
                session.add(
                    ResearchSourceRecord(
                        source_id=source_id,
                        label=descriptor["label"],
                        source_kind=descriptor["source_kind"],
                        trust_level=descriptor["trust_level"],
                        access_class=descriptor["access_class"],
                        base_url=descriptor.get("base_url"),
                        description=descriptor.get("description"),
                        polling_config=descriptor.get("polling_config") or {},
                        enabled=bool(descriptor.get("enabled", True)),
                    )
                )
                continue

            record.label = descriptor["label"]
            record.source_kind = descriptor["source_kind"]
            record.trust_level = descriptor["trust_level"]
            record.access_class = descriptor["access_class"]
            record.base_url = descriptor.get("base_url")
            record.description = descriptor.get("description")
            record.polling_config = _merge_catalog_polling_config(
                catalog_config=descriptor.get("polling_config") or {},
                existing_config=record.polling_config or {},
            )
            record.enabled = bool(descriptor.get("enabled", True))

        existing_topics = {
            row.topic_id: row
            for row in session.execute(select(ResearchTopicRecord)).scalars().all()
        }
        for descriptor in load_research_topic_catalog():
            topic_id = descriptor["topic_id"]
            record = existing_topics.get(topic_id)
            if record is None:
                session.add(
                    ResearchTopicRecord(
                        topic_id=topic_id,
                        label=descriptor["label"],
                        description=descriptor.get("description"),
                        keywords=descriptor.get("keywords") or [],
                        related_rationale_codes=descriptor.get("related_rationale_codes") or [],
                        related_trial_tags=descriptor.get("related_trial_tags") or [],
                        opportunity_types=descriptor.get("opportunity_types") or [],
                        status=descriptor.get("status") or "active",
                    )
                )
                continue

            record.label = descriptor["label"]
            record.description = descriptor.get("description")
            record.keywords = descriptor.get("keywords") or []
            record.related_rationale_codes = descriptor.get("related_rationale_codes") or []
            record.related_trial_tags = descriptor.get("related_trial_tags") or []
            record.opportunity_types = descriptor.get("opportunity_types") or []
            record.status = descriptor.get("status") or "active"


def _merge_catalog_polling_config(
    *,
    catalog_config: dict[str, Any],
    existing_config: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(catalog_config or {})
    existing_health = dict((existing_config or {}).get("health") or {})
    if existing_health:
        merged["health"] = existing_health
    return merged


def list_research_sources() -> list[ResearchSource]:
    ensure_research_intel_seeded()
    now = _utcnow()
    with SessionLocal() as session:
        rows = session.execute(
            select(ResearchSourceRecord).order_by(ResearchSourceRecord.label.asc())
        ).scalars().all()
        return [_build_research_source(row, now=now) for row in rows]


def list_research_schedule() -> ResearchScheduleSnapshot:
    sources = list_research_sources()
    sorted_sources = sorted(
        sources,
        key=lambda item: (
            0 if item.schedule_state == "due" else 1 if item.schedule_state == "scheduled" else 2 if item.schedule_state == "unscheduled" else 3,
            0 if item.priority == "high" else 1 if item.priority == "medium" else 2,
            item.next_run_at or datetime.max.replace(tzinfo=timezone.utc),
            item.label.lower(),
        ),
    )
    return ResearchScheduleSnapshot(
        generated_at=_utcnow(),
        total_sources=len(sorted_sources),
        due_count=sum(1 for item in sorted_sources if item.schedule_state == "due"),
        overdue_count=sum(1 for item in sorted_sources if (item.overdue_by_hours or 0) > 0),
        scheduled_count=sum(1 for item in sorted_sources if item.schedule_state == "scheduled"),
        disabled_count=sum(1 for item in sorted_sources if item.schedule_state == "disabled"),
        live_ready_count=sum(1 for item in sorted_sources if item.live_ready),
        fixture_only_count=sum(1 for item in sorted_sources if not item.live_ready),
        sources=sorted_sources,
    )


def list_research_runs(*, limit: int = 20) -> list[ResearchRunSummary]:
    ensure_research_intel_seeded()
    with SessionLocal() as session:
        rows = session.execute(
            select(ResearchRunRecord).order_by(ResearchRunRecord.completed_at.desc()).limit(limit)
        ).scalars().all()
        return [_build_run_summary(row) for row in rows]


def get_research_run(run_id: int) -> ResearchRunDetail | None:
    ensure_research_intel_seeded()
    with SessionLocal() as session:
        run = session.get(ResearchRunRecord, run_id)
        if run is None:
            return None
        items = session.execute(
            select(ResearchRunItemRecord)
            .where(ResearchRunItemRecord.run_id == run.id)
            .order_by(ResearchRunItemRecord.item_index.asc())
        ).scalars().all()
        return _build_run_detail(run, items)


def run_research_ingest(
    *,
    actor_user_id: str,
    source_ids: list[str] | None = None,
    include_disabled: bool = False,
    only_due: bool = False,
    write_artifacts: bool = True,
    mode: ResearchIngestMode = "auto",
    max_documents_per_source: int | None = None,
) -> ResearchRunDetail:
    ensure_research_intel_seeded()
    started_at = _utcnow()
    initial_selected_sources = _select_source_ids(source_ids=source_ids, include_disabled=include_disabled)
    source_map = _source_catalog_map()
    topic_descriptors = _topic_catalog_map()
    requested_mode = str(mode or "auto")

    with SessionLocal.begin() as session:
        source_records = {
            row.source_id: row
            for row in session.execute(
                select(ResearchSourceRecord).where(ResearchSourceRecord.source_id.in_(initial_selected_sources))
            ).scalars().all()
        }
        due_source_ids, skipped_source_ids = _partition_due_sources(
            source_records=source_records,
            requested_source_ids=initial_selected_sources,
            only_due=only_due,
            now=started_at,
        )
        selected_sources = due_source_ids
        run = ResearchRunRecord(
            run_type="ingest",
            status="completed",
            actor_user_id=actor_user_id,
            source_scope=selected_sources,
            started_at=started_at,
            completed_at=started_at,
            metadata_json={
                "requested_mode": requested_mode,
                "max_documents_per_source": max_documents_per_source,
                "only_due": only_due,
                "requested_source_scope": initial_selected_sources,
                "skipped_source_ids": skipped_source_ids,
            },
        )
        session.add(run)
        session.flush()

        created = 0
        updated = 0
        processed_documents = 0
        failure_counts: Counter[str] = Counter()
        items: list[ResearchRunItemRecord] = []
        source_summaries: dict[str, dict[str, Any]] = {}

        collected_batches: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for source_index, source_id in enumerate(selected_sources, start=1):
            source_descriptor = source_map[source_id]
            source_record = source_records.get(source_id)

            try:
                if requested_mode == "seeded":
                    batch = {
                        "source_id": source_id,
                        "connector_id": "seed_catalog",
                        "mode": "seeded",
                        "fetched_at": started_at,
                        "query": None,
                        "source_url": source_descriptor.get("base_url"),
                        "documents": [
                            item
                            for item in load_seed_research_documents()
                            if item["source_id"] == source_id
                        ][: max_documents_per_source or 9999],
                        "fixture_path": str(SEED_DOCUMENTS_PATH),
                    }
                else:
                    batch = collect_research_documents_for_source(
                        source_descriptor,
                        mode=requested_mode,
                        max_documents_per_source=max_documents_per_source,
                    )
            except Exception as exc:
                failure_counts["connector_error"] += 1
                source_summaries[source_id] = {
                    "status": "error",
                    "mode": requested_mode,
                    "connector_id": str((source_descriptor.get("polling_config") or {}).get("connector_id") or ""),
                    "document_count": 0,
                    "error_bucket": "connector_error",
                    "error_detail": str(exc),
                }
                if source_record is not None:
                    _update_source_health(
                        source_record,
                        status="error",
                        last_run_at=started_at,
                        last_error_at=_utcnow(),
                        last_error_detail=str(exc),
                        last_document_count=0,
                        last_mode=requested_mode,
                    )
                items.append(
                    ResearchRunItemRecord(
                        run_id=run.id,
                        item_index=source_index,
                        stage="fetch",
                        status="failed",
                        source_identifier=source_id,
                        error_bucket="connector_error",
                        error_detail=str(exc),
                    )
                )
                continue

            fetched_at = _coerce_utc(batch.get("fetched_at")) or _utcnow()
            documents = list(batch.get("documents") or [])
            source_summaries[source_id] = {
                "status": "healthy",
                "mode": batch.get("mode"),
                "connector_id": batch.get("connector_id"),
                "document_count": len(documents),
                "query": batch.get("query"),
                "source_url": batch.get("source_url"),
                "fetched_at": fetched_at.isoformat(),
            }
            if source_record is not None:
                _update_source_health(
                    source_record,
                    status="healthy",
                    last_run_at=started_at,
                    last_success_at=_utcnow(),
                    last_document_count=len(documents),
                    last_mode=str(batch.get("mode") or requested_mode),
                    last_error_at=None,
                    last_error_detail=None,
                )
            items.append(
                ResearchRunItemRecord(
                    run_id=run.id,
                    item_index=source_index,
                    stage="fetch",
                    status="completed",
                    source_identifier=source_id,
                    document_id=None,
                )
            )
            for document in documents:
                collected_batches.append((document, batch))

        for index, (document, batch) in enumerate(collected_batches, start=len(items) + 1):
            source_descriptor = source_map[document["source_id"]]
            normalized = _normalize_seed_document(
                document,
                source_map=source_map,
                topic_descriptors=topic_descriptors,
            )
            existing = session.execute(
                select(ResearchDocumentRecord).where(
                    ResearchDocumentRecord.dedupe_key == normalized["dedupe_key"]
                )
            ).scalar_one_or_none()

            novelty_score = _calculate_novelty_score(
                document=document,
                source_descriptor=source_descriptor,
                existing=existing,
            )
            _apply_document_provenance(
                normalized,
                batch=batch,
                requested_mode=requested_mode,
                novelty_score=novelty_score,
            )

            if existing is None:
                record = ResearchDocumentRecord(
                    document_id=normalized["document_id"],
                    source_id=normalized["source_id"],
                    source_identifier=normalized.get("source_identifier"),
                    document_type=normalized["document_type"],
                    title=normalized["title"],
                    abstract_text=normalized["abstract_text"],
                    url=normalized.get("url"),
                    canonical_url=normalized.get("canonical_url"),
                    doi=normalized.get("doi"),
                    pmid=normalized.get("pmid"),
                    nct_id=normalized.get("nct_id"),
                    citation_key=normalized["citation_key"],
                    dedupe_key=normalized["dedupe_key"],
                    published_at=normalized.get("published_at"),
                    authors=normalized["authors"],
                    organizations=normalized["organizations"],
                    topic_ids=normalized["topic_ids"],
                    entity_tags=normalized["entity_tags"],
                    relevance_scores=normalized["relevance_scores"],
                    raw_metadata=normalized["raw_metadata"],
                )
                session.add(record)
                session.flush()
                created += 1
                processed_documents += 1
                document_id = record.document_id
            else:
                existing.source_id = normalized["source_id"]
                existing.source_identifier = normalized.get("source_identifier")
                existing.document_type = normalized["document_type"]
                existing.title = normalized["title"]
                existing.abstract_text = normalized["abstract_text"]
                existing.url = normalized.get("url")
                existing.canonical_url = normalized.get("canonical_url")
                existing.doi = normalized.get("doi")
                existing.pmid = normalized.get("pmid")
                existing.nct_id = normalized.get("nct_id")
                existing.citation_key = normalized["citation_key"]
                existing.published_at = normalized.get("published_at")
                existing.authors = normalized["authors"]
                existing.organizations = normalized["organizations"]
                existing.topic_ids = normalized["topic_ids"]
                existing.entity_tags = normalized["entity_tags"]
                existing.relevance_scores = normalized["relevance_scores"]
                existing.raw_metadata = normalized["raw_metadata"]
                document_id = existing.document_id
                updated += 1
                processed_documents += 1
                session.execute(
                    delete(ResearchEvidenceRecord).where(
                        ResearchEvidenceRecord.document_id == existing.document_id
                    )
                )

            for evidence in normalized["evidence"]:
                session.add(
                    ResearchEvidenceRecord(
                        document_id=document_id,
                        evidence_text=evidence["evidence_text"],
                        char_start=evidence["char_start"],
                        char_end=evidence["char_end"],
                        claim_text=evidence["claim_text"],
                        claim_type=evidence["claim_type"],
                        entity_tags=evidence["entity_tags"],
                        citation_label=evidence["citation_label"],
                        confidence=evidence["confidence"],
                    )
                )

            items.append(
                ResearchRunItemRecord(
                    run_id=run.id,
                    item_index=index,
                    stage="collect",
                    status="processed",
                    source_identifier=str(document.get("source_identifier") or document.get("title") or ""),
                    document_id=document_id,
                )
            )

        for item in items:
            session.add(item)

        _refresh_topic_metrics(session)

        artifact_paths: list[str] = []
        if write_artifacts:
            artifact_paths.extend(
                _write_run_artifacts(
                    artifact_root=_artifact_root() / "runs",
                    basename=f"ingest-run-{run.id}",
                    payload={
                        "run_id": run.id,
                        "run_type": "ingest",
                        "source_scope": selected_sources,
                        "requested_source_scope": initial_selected_sources,
                        "requested_mode": requested_mode,
                        "only_due": only_due,
                        "processed": processed_documents,
                        "created": created,
                        "updated": updated,
                        "failure_counts": dict(failure_counts),
                        "skipped_source_ids": skipped_source_ids,
                        "sources": source_summaries,
                    },
                    markdown_lines=[
                        f"# Research Intelligence ingest run {run.id}",
                        "",
                        f"- actor: `{actor_user_id}`",
                        f"- requested mode: `{requested_mode}`",
                        f"- due-only selection: `{only_due}`",
                        f"- processed: `{processed_documents}`",
                        f"- created: `{created}`",
                        f"- updated: `{updated}`",
                        f"- failed sources: `{sum(failure_counts.values())}`",
                        f"- sources: {', '.join(selected_sources) or 'none'}",
                        (
                            f"- skipped sources: {', '.join(skipped_source_ids)}"
                            if skipped_source_ids
                            else "- skipped sources: none"
                        ),
                        "",
                        "## Source status",
                        *[
                            (
                                f"- `{source_id}`: {summary['status']} • "
                                f"{summary.get('document_count', 0)} document(s) • "
                                f"mode `{summary.get('mode') or requested_mode}`"
                                + (
                                    f" • error `{summary.get('error_detail')}`"
                                    if summary.get("error_detail")
                                    else ""
                                )
                            )
                            for source_id, summary in sorted(source_summaries.items())
                        ],
                    ],
                )
            )

        run.processed_count = processed_documents
        run.created_count = created
        run.updated_count = updated
        run.failed_count = sum(failure_counts.values())
        run.failure_counts = dict(failure_counts)
        run.completed_at = _utcnow()
        run.artifact_paths = artifact_paths
        run.status = "completed_with_errors" if failure_counts else "completed"
        run.metadata_json = {
            "requested_mode": requested_mode,
            "max_documents_per_source": max_documents_per_source,
            "only_due": only_due,
            "requested_source_scope": initial_selected_sources,
            "skipped_source_ids": skipped_source_ids,
            "source_summaries": source_summaries,
            "processed_documents": processed_documents,
        }

        run_id = run.id

    return get_research_run(run_id) or ResearchRunDetail(
        run_id=run_id,
        run_type="ingest",
        status="completed_with_errors" if failure_counts else "completed",
        actor_user_id=actor_user_id,
        source_scope=selected_sources,
        processed=processed_documents,
        created=created,
        updated=updated,
        failed=sum(failure_counts.values()),
        failure_counts=dict(failure_counts),
        artifact_paths=[],
        metadata={
            "requested_mode": requested_mode,
            "only_due": only_due,
            "requested_source_scope": initial_selected_sources,
            "skipped_source_ids": skipped_source_ids,
            "source_summaries": source_summaries,
        },
        started_at=started_at,
        completed_at=_utcnow(),
        items=[],
    )


def run_research_digest(
    *,
    actor_user_id: str,
    publish: bool = True,
    write_artifacts: bool = True,
) -> ResearchRunDetail:
    ensure_research_intel_seeded()
    started_at = _utcnow()

    with SessionLocal.begin() as session:
        source_rows = session.execute(select(ResearchSourceRecord)).scalars().all()
        source_map = {row.source_id: row for row in source_rows}
        topic_rows = session.execute(select(ResearchTopicRecord)).scalars().all()
        topic_label_map = {row.topic_id: row.label for row in topic_rows}
        topic_record_map = {row.topic_id: row for row in topic_rows}
        documents = session.execute(
            select(ResearchDocumentRecord).order_by(ResearchDocumentRecord.published_at.desc())
        ).scalars().all()

        run = ResearchRunRecord(
            run_type="digest",
            status="completed",
            actor_user_id=actor_user_id,
            source_scope=sorted({doc.source_id for doc in documents}),
            started_at=started_at,
            completed_at=started_at,
            metadata_json={"publish": publish},
        )
        session.add(run)
        session.flush()

        if not documents:
            run.processed_count = 0
            run.created_count = 0
            run.updated_count = 0
            run.failed_count = 0
            run.failure_counts = {}
            run.completed_at = _utcnow()
            return _build_run_detail(run, [])

        digest_payload = _build_digest_payload(
            documents=documents,
            topic_label_map=topic_label_map,
            source_map=source_map,
        )
        council = ResearchCouncilPayload.model_validate(digest_payload["council_payload"])
        digest_id = digest_payload["digest_id"]
        digest = session.get(ResearchDigestRecord, digest_id)
        if digest is None:
            digest = ResearchDigestRecord(
                digest_id=digest_id,
                title=digest_payload["title"],
                status="published" if publish else "draft",
                publication_scope="public",
                window_start=digest_payload["window_start"],
                window_end=digest_payload["window_end"],
                generated_at=digest_payload["generated_at"],
                topic_ids=digest_payload["topic_ids"],
                supporting_document_ids=digest_payload["supporting_document_ids"],
                council_payload=digest_payload["council_payload"],
                summary_markdown=digest_payload["summary_markdown"],
                summary_json=digest_payload["summary_json"],
                disagreement_score=digest_payload["disagreement_score"],
                citation_count=digest_payload["citation_count"],
            )
            session.add(digest)
        else:
            digest.title = digest_payload["title"]
            digest.status = "published" if publish else "draft"
            digest.publication_scope = "public"
            digest.window_start = digest_payload["window_start"]
            digest.window_end = digest_payload["window_end"]
            digest.generated_at = digest_payload["generated_at"]
            digest.topic_ids = digest_payload["topic_ids"]
            digest.supporting_document_ids = digest_payload["supporting_document_ids"]
            digest.council_payload = digest_payload["council_payload"]
            digest.summary_markdown = digest_payload["summary_markdown"]
            digest.summary_json = digest_payload["summary_json"]
            digest.disagreement_score = digest_payload["disagreement_score"]
            digest.citation_count = digest_payload["citation_count"]

        created_opportunities = _upsert_opportunities_for_digest(
            session=session,
            digest=digest,
            topic_record_map=topic_record_map,
            topic_label_map=topic_label_map,
            source_map=source_map,
            documents=documents,
            council=council,
            write_artifacts=write_artifacts,
        )

        run_items = [
            ResearchRunItemRecord(
                run_id=run.id,
                item_index=1,
                stage="deliberate",
                status="completed",
                source_identifier=digest.digest_id,
                document_id=digest.digest_id,
            )
        ]
        for item in run_items:
            session.add(item)

        artifact_paths: list[str] = []
        if write_artifacts:
            artifact_paths.extend(
                _write_run_artifacts(
                    artifact_root=_artifact_root() / "digests",
                    basename=digest.digest_id,
                    payload=digest_payload["artifact_json"],
                    markdown_lines=digest_payload["summary_markdown"].splitlines(),
                )
            )
            artifact_paths.extend(created_opportunities["artifact_paths"])

        run.processed_count = len(documents)
        run.created_count = 1 + created_opportunities["created"]
        run.updated_count = created_opportunities["updated"]
        run.failed_count = 0
        run.failure_counts = {}
        run.completed_at = _utcnow()
        run.artifact_paths = artifact_paths
        run.metadata_json = {
            "publish": publish,
            "digest_id": digest.digest_id,
            "opportunities_created": created_opportunities["created"],
            "opportunities_updated": created_opportunities["updated"],
            "opportunity_artifacts_written": len(created_opportunities["artifact_paths"]),
        }

    return get_research_run(run.id) or _build_run_detail(run, [])


def list_research_documents(
    *,
    source_kind: str | None = None,
    topic: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ResearchDocument]:
    ensure_research_intel_seeded()
    with SessionLocal() as session:
        documents = session.execute(
            select(ResearchDocumentRecord).order_by(ResearchDocumentRecord.published_at.desc())
        ).scalars().all()
        source_rows = session.execute(select(ResearchSourceRecord)).scalars().all()
        topic_rows = session.execute(select(ResearchTopicRecord)).scalars().all()
        source_map = {row.source_id: row for row in source_rows}
        topic_label_map = {row.topic_id: row.label for row in topic_rows}

        source_kind_l = source_kind.lower() if source_kind else None
        topic_l = topic.lower() if topic else None
        query_l = q.lower() if q else None

        filtered: list[ResearchDocument] = []
        for row in documents:
            source = source_map.get(row.source_id)
            if source_kind_l and (source.source_kind if source else "").lower() != source_kind_l:
                continue
            if topic_l and not any(topic_l in item.lower() for item in row.topic_ids):
                continue
            haystack = " ".join(
                [
                    row.title,
                    row.abstract_text,
                    " ".join(row.entity_tags or []),
                    " ".join(row.topic_ids or []),
                ]
            ).lower()
            if query_l and query_l not in haystack:
                continue
            filtered.append(_build_document_response(session, row, source_map, topic_label_map))

        return filtered[offset : offset + limit]


def list_research_topics() -> list[ResearchTopic]:
    ensure_research_intel_seeded()
    with SessionLocal() as session:
        rows = session.execute(
            select(ResearchTopicRecord).order_by(
                ResearchTopicRecord.topic_heat.desc(),
                ResearchTopicRecord.label.asc(),
            )
        ).scalars().all()
        return [
            ResearchTopic(
                topic_id=row.topic_id,
                label=row.label,
                description=row.description,
                keywords=row.keywords or [],
                related_rationale_codes=row.related_rationale_codes or [],
                related_trial_tags=row.related_trial_tags or [],
                opportunity_types=row.opportunity_types or [],
                topic_heat=row.topic_heat,
                document_count=row.document_count,
                last_document_at=row.last_document_at,
                status=row.status,
            )
            for row in rows
        ]


def get_research_graph_snapshot() -> ResearchGraphSnapshot:
    ensure_research_intel_seeded()
    indexes = load_research_graph_indexes()
    node_map = {
        str(node.get("node_id") or "").strip(): node
        for node in indexes["nodes"]
        if str(node.get("node_id") or "").strip()
    }

    with SessionLocal() as session:
        documents = session.execute(select(ResearchDocumentRecord)).scalars().all()

    node_stats: dict[str, dict[str, Any]] = {
        node_id: {
            "document_count": 0,
            "heat": 0.0,
            "recent_document_ids": [],
        }
        for node_id in node_map
    }

    for document in documents:
        graph_entities = list((document.raw_metadata or {}).get("graph_entities") or [])
        seen_node_ids: set[str] = set()
        novelty = _coerce_float((document.raw_metadata or {}).get("novelty_score")) or 0.0
        for entity in graph_entities:
            node_id = str(entity.get("node_id") or "").strip()
            if not node_id or node_id not in node_stats or node_id in seen_node_ids:
                continue
            seen_node_ids.add(node_id)
            node_stats[node_id]["document_count"] += 1
            node_stats[node_id]["heat"] += round(
                (float(entity.get("confidence") or 0.0) * 0.65) + (novelty * 0.35),
                4,
            )
            node_stats[node_id]["recent_document_ids"].append(document.document_id)

    nodes = [
        ResearchGraphNode(
            node_id=node_id,
            label=str(node.get("label") or node_id),
            node_type=str(node.get("node_type") or "entity"),
            description=str(node.get("description") or "") or None,
            tags=[str(item) for item in node.get("tags") or []],
            topic_ids=[str(item) for item in node.get("topic_ids") or []],
            aliases=[str(item) for item in node.get("aliases") or []],
            keywords=[str(item) for item in node.get("keywords") or []],
            related_node_ids=[str(item) for item in indexes["neighbor_map"].get(node_id, [])],
            document_count=node_stats[node_id]["document_count"],
            heat=round(node_stats[node_id]["heat"], 4),
            recent_document_ids=node_stats[node_id]["recent_document_ids"][:5],
        )
        for node_id, node in node_map.items()
    ]
    nodes.sort(key=lambda item: (-item.document_count, -item.heat, item.label))

    edges = [
        ResearchGraphEdge(
            source=str(edge.get("source") or ""),
            target=str(edge.get("target") or ""),
            relation=str(edge.get("relation") or ""),
            weight=_coerce_float(edge.get("weight")),
        )
        for edge in indexes["edges"]
    ]

    return ResearchGraphSnapshot(
        generated_at=_utcnow(),
        active_node_ids=[node.node_id for node in nodes if node.document_count > 0],
        nodes=nodes,
        edges=edges,
    )


def list_research_digests() -> list[ResearchDigestListItem]:
    ensure_research_intel_seeded()
    with SessionLocal() as session:
        topic_rows = session.execute(select(ResearchTopicRecord)).scalars().all()
        topic_label_map = {row.topic_id: row.label for row in topic_rows}
        rows = session.execute(
            select(ResearchDigestRecord).order_by(ResearchDigestRecord.generated_at.desc())
        ).scalars().all()
        return [
            ResearchDigestListItem(
                digest_id=row.digest_id,
                title=row.title,
                status=row.status,
                publication_scope=row.publication_scope,
                generated_at=row.generated_at,
                topic_ids=row.topic_ids or [],
                topic_labels=[topic_label_map[item] for item in row.topic_ids or [] if item in topic_label_map],
                disagreement_score=row.disagreement_score,
                citation_count=row.citation_count,
            )
            for row in rows
        ]


def get_research_digest(digest_id: str) -> ResearchDigestDetail | None:
    ensure_research_intel_seeded()
    with SessionLocal() as session:
        digest = session.get(ResearchDigestRecord, digest_id)
        if digest is None:
            return None

        topic_rows = session.execute(select(ResearchTopicRecord)).scalars().all()
        topic_label_map = {row.topic_id: row.label for row in topic_rows}
        documents = session.execute(
            select(ResearchDocumentRecord).where(
                ResearchDocumentRecord.document_id.in_(digest.supporting_document_ids or [])
            )
        ).scalars().all()
        document_map = {item.document_id: item for item in documents}
        refs = [
            _build_digest_document_ref(
                document_map[document_id],
                topic_label_map=topic_label_map,
            )
            for document_id in digest.supporting_document_ids or []
            if document_id in document_map
        ]
        summary_json = digest.summary_json or {}
        council = ResearchCouncilPayload.model_validate(_normalize_council_payload(digest.council_payload))
        return ResearchDigestDetail(
            digest_id=digest.digest_id,
            title=digest.title,
            status=digest.status,
            publication_scope=digest.publication_scope,
            generated_at=digest.generated_at,
            topic_ids=digest.topic_ids or [],
            topic_labels=[topic_label_map[item] for item in digest.topic_ids or [] if item in topic_label_map],
            disagreement_score=digest.disagreement_score,
            citation_count=digest.citation_count,
            window_start=digest.window_start,
            window_end=digest.window_end,
            summary_markdown=digest.summary_markdown,
            key_takeaways=list(summary_json.get("key_takeaways") or []),
            supporting_documents=refs,
            council=council,
        )


def list_research_opportunities(
    *,
    opportunity_type: str | None = None,
    status: str | None = None,
    topic: str | None = None,
) -> list[ResearchOpportunity]:
    ensure_research_intel_seeded()
    with SessionLocal() as session:
        topic_rows = session.execute(select(ResearchTopicRecord)).scalars().all()
        topic_label_map = {row.topic_id: row.label for row in topic_rows}
        rows = session.execute(
            select(ResearchOpportunityRecord).order_by(ResearchOpportunityRecord.updated_at.desc())
        ).scalars().all()
        opportunity_type_l = opportunity_type.lower() if opportunity_type else None
        status_l = status.lower() if status else None
        topic_l = topic.lower() if topic else None

        items: list[ResearchOpportunity] = []
        for row in rows:
            if opportunity_type_l and row.opportunity_type.lower() != opportunity_type_l:
                continue
            if status_l and row.status.lower() != status_l:
                continue
            if topic_l and not any(topic_l in item.lower() for item in row.topic_ids or []):
                continue
            items.append(_build_opportunity_response(row, topic_label_map))
        return items


def promote_research_opportunity(
    *,
    opportunity_id: str,
    actor_user_id: str,
    target: ResearchPromotionTarget,
) -> tuple[ResearchOpportunity | None, str | None]:
    ensure_research_intel_seeded()
    with SessionLocal.begin() as session:
        row = session.get(ResearchOpportunityRecord, opportunity_id)
        if row is None:
            return None, None

        row.status = "promoted"
        row.promotion_target = target
        row.promoted_at = _utcnow()
        artifact_path = _write_opportunity_promotion_artifact(row, target=target)
        action_payload = ResearchOpportunityActionPayload.model_validate(row.action_payload or {})
        action_payload.promoted_by_user_id = actor_user_id
        action_payload.last_promotion_target = target
        action_payload.promotion_artifact_path = artifact_path
        row.action_payload = action_payload.model_dump(mode="json")
        topic_rows = session.execute(select(ResearchTopicRecord)).scalars().all()
        topic_label_map = {topic.topic_id: topic.label for topic in topic_rows}
        return _build_opportunity_response(row, topic_label_map), artifact_path


def run_research_opportunity_experiment(
    *,
    opportunity_id: str,
    actor_user_id: str,
    write_artifacts: bool = True,
) -> ResearchRunDetail | None:
    ensure_research_intel_seeded()
    started_at = _utcnow()

    with SessionLocal.begin() as session:
        row = session.get(ResearchOpportunityRecord, opportunity_id)
        if row is None:
            return None
        if row.opportunity_type not in _EXPERIMENT_SUPPORTED_OPPORTUNITY_TYPES:
            raise ValueError("Experiments currently support only benchmark and rule opportunities.")

        action_payload = ResearchOpportunityActionPayload.model_validate(row.action_payload or {})
        topic_rows = session.execute(select(ResearchTopicRecord)).scalars().all()
        topic_label_map = {topic.topic_id: topic.label for topic in topic_rows}

        run = ResearchRunRecord(
            run_type="experiment",
            status="completed",
            actor_user_id=actor_user_id,
            source_scope=row.topic_ids or [],
            started_at=started_at,
            completed_at=started_at,
            metadata_json={
                "opportunity_id": opportunity_id,
                "opportunity_type": row.opportunity_type,
                "write_artifacts": write_artifacts,
            },
        )
        session.add(run)
        session.flush()

        run_items = [
            ResearchRunItemRecord(
                run_id=run.id,
                item_index=1,
                stage="validate_opportunity",
                status="completed",
                source_identifier=opportunity_id,
                document_id=action_payload.digest_id,
            )
        ]
        for item in run_items:
            session.add(item)

        experiment = _evaluate_opportunity_experiment(
            row=row,
            action_payload=action_payload,
            run_id=run.id,
        )
        run_items.extend(
            [
                ResearchRunItemRecord(
                    run_id=run.id,
                    item_index=2,
                    stage="score_baseline",
                    status="completed",
                    source_identifier=opportunity_id,
                    document_id=action_payload.digest_id,
                ),
                ResearchRunItemRecord(
                    run_id=run.id,
                    item_index=3,
                    stage="score_candidate",
                    status="completed",
                    source_identifier=opportunity_id,
                    document_id=action_payload.digest_id,
                ),
                ResearchRunItemRecord(
                    run_id=run.id,
                    item_index=4,
                    stage="ratchet",
                    status="completed",
                    source_identifier=opportunity_id,
                    document_id=action_payload.digest_id,
                ),
            ]
        )
        for item in run_items[1:]:
            session.add(item)

        artifact_paths: list[str] = []
        if write_artifacts:
            session.flush()
            artifact_paths = _write_opportunity_experiment_artifacts(
                row=row,
                action_payload=action_payload,
                experiment=experiment,
                topic_label_map=topic_label_map,
            )

        completed_at = _utcnow()
        experiment.artifact_paths = artifact_paths
        experiment.completed_at = completed_at

        action_payload.last_experiment = experiment
        row.action_payload = action_payload.model_dump(mode="json")

        run.processed_count = 1
        run.created_count = 1
        run.updated_count = 1
        run.failed_count = 0
        run.failure_counts = {}
        run.artifact_paths = artifact_paths
        run.completed_at = completed_at
        run.metadata_json = {
            "opportunity_id": opportunity_id,
            "opportunity_type": row.opportunity_type,
            "ratchet_outcome": experiment.ratchet_outcome,
            "experiment_kind": experiment.experiment_kind,
            "metric_name": experiment.metric_name,
            "baseline_value": experiment.baseline_value,
            "candidate_value": experiment.candidate_value,
            "delta": experiment.delta,
            "threshold": experiment.threshold,
            "min_delta": experiment.min_delta,
            "write_artifacts": write_artifacts,
        }

        run_id = run.id

    return get_research_run(run_id) or _build_run_detail(run, run_items)


def build_research_case_brief(case_id: str) -> ResearchCaseBrief | None:
    ensure_research_intel_seeded()
    case = CASE_STORE.get_case(case_id)
    if case is None:
        return None

    trial_matches = match_case_to_trials(case_id)
    with SessionLocal() as session:
        topics = session.execute(select(ResearchTopicRecord)).scalars().all()
        documents = session.execute(
            select(ResearchDocumentRecord).order_by(ResearchDocumentRecord.published_at.desc())
        ).scalars().all()
        opportunities = session.execute(select(ResearchOpportunityRecord)).scalars().all()

        matched_topics: list[ResearchCaseBriefTopic] = []
        matched_topic_ids: list[str] = []
        report_text_l = case.report_text.lower()
        trial_labels = {
            match.trial_id.lower()
            for match in (trial_matches.matches if trial_matches is not None else [])
        }

        for topic in topics:
            rationale_overlap = sorted(
                set(topic.related_rationale_codes or []).intersection(set(case.rationale_codes))
            )
            trial_overlap = sorted(
                item
                for item in topic.related_trial_tags or []
                if item.lower() in trial_labels
            )
            keyword_overlap = [
                keyword
                for keyword in topic.keywords or []
                if keyword.lower() in report_text_l
            ]
            if not any([rationale_overlap, trial_overlap, keyword_overlap]):
                continue

            reason_parts: list[str] = []
            if rationale_overlap:
                reason_parts.append(f"rationale codes {', '.join(rationale_overlap)}")
            if trial_overlap:
                reason_parts.append(f"trial tags {', '.join(trial_overlap)}")
            if keyword_overlap:
                reason_parts.append(f"report language {', '.join(keyword_overlap[:2])}")

            matched_topics.append(
                ResearchCaseBriefTopic(
                    topic_id=topic.topic_id,
                    label=topic.label,
                    rationale="Matched via " + "; ".join(reason_parts) + ".",
                )
            )
            matched_topic_ids.append(topic.topic_id)

        if not matched_topics and topics:
            fallback = sorted(topics, key=lambda item: item.topic_heat, reverse=True)[:2]
            for topic in fallback:
                matched_topics.append(
                    ResearchCaseBriefTopic(
                        topic_id=topic.topic_id,
                        label=topic.label,
                        rationale="Selected as a high-activity pancreatic oncology topic for general case context.",
                    )
                )
                matched_topic_ids.append(topic.topic_id)

        supporting_documents: list[ResearchCaseBriefDocument] = []
        for document in documents:
            overlap = [topic_id for topic_id in document.topic_ids or [] if topic_id in matched_topic_ids]
            if not overlap:
                continue
            supporting_documents.append(
                ResearchCaseBriefDocument(
                    document_id=document.document_id,
                    title=document.title,
                    citation_key=document.citation_key,
                    url=document.url,
                    relevance_reason=(
                        "Touches "
                        + ", ".join(overlap[:2])
                        + " and aligns with the case rationale or trial context."
                    ),
                )
            )
            if len(supporting_documents) >= 4:
                break

        suggested_benchmark_gaps = [
            row.title
            for row in opportunities
            if row.opportunity_type == "benchmark_gap"
            and any(topic_id in matched_topic_ids for topic_id in row.topic_ids or [])
        ][:3]
        suggested_rule_updates = [
            row.title
            for row in opportunities
            if row.opportunity_type == "rule_gap"
            and any(topic_id in matched_topic_ids for topic_id in row.topic_ids or [])
        ][:3]
        suggested_trial_updates = [
            row.title
            for row in opportunities
            if row.opportunity_type == "trial_catalog_gap"
            and any(topic_id in matched_topic_ids for topic_id in row.topic_ids or [])
        ][:3]

    topic_labels = ", ".join(topic.label for topic in matched_topics[:3]) or "current pancreatic oncology activity"
    rationale_labels = ", ".join(case.rationale_codes[:3]) or "current triage evidence"
    summary = (
        f"This case currently aligns with {topic_labels} based on {rationale_labels}. "
        "The linked documents are recent, cited items that can inform benchmark growth, "
        "rule discussions, or trial-catalog refinement without changing the case score automatically."
    )

    return ResearchCaseBrief(
        case_id=case_id,
        summary=summary,
        matched_topics=matched_topics,
        supporting_documents=supporting_documents,
        suggested_benchmark_gaps=suggested_benchmark_gaps,
        suggested_rule_updates=suggested_rule_updates,
        suggested_trial_updates=suggested_trial_updates,
    )


def _build_run_summary(row: ResearchRunRecord) -> ResearchRunSummary:
    return ResearchRunSummary(
        run_id=row.id,
        run_type=row.run_type,
        status=row.status,
        actor_user_id=row.actor_user_id,
        source_scope=row.source_scope or [],
        processed=row.processed_count,
        created=row.created_count,
        updated=row.updated_count,
        failed=row.failed_count,
        failure_counts=row.failure_counts or {},
        artifact_paths=row.artifact_paths or [],
        metadata=row.metadata_json or {},
        started_at=row.started_at,
        completed_at=row.completed_at,
    )


def _build_run_detail(
    run: ResearchRunRecord,
    items: list[ResearchRunItemRecord],
) -> ResearchRunDetail:
    summary = _build_run_summary(run)
    return ResearchRunDetail(
        **summary.model_dump(),
        items=[
            ResearchRunItem(
                item_index=item.item_index,
                stage=item.stage,
                status=item.status,
                source_identifier=item.source_identifier,
                document_id=item.document_id,
                error_bucket=item.error_bucket,
                error_detail=item.error_detail,
                created_at=item.created_at,
            )
            for item in items
        ],
    )


def _source_health(polling_config: dict[str, Any]) -> dict[str, Any]:
    return dict(polling_config.get("health") or {})


def _compute_source_schedule(
    *,
    enabled: bool,
    polling_config: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    interval_hours = _coerce_int(polling_config.get("interval_hours"))
    health = _source_health(polling_config)
    last_run_at = _parse_datetime(health.get("last_run_at"))
    consecutive_failures = max(_coerce_int(health.get("consecutive_failures")) or 0, 0)

    if not enabled:
        return {
            "priority": str(polling_config.get("priority") or "").strip() or None,
            "interval_hours": interval_hours,
            "effective_interval_hours": interval_hours,
            "schedule_state": "disabled",
            "next_run_at": None,
            "overdue_by_hours": None,
            "consecutive_failures": consecutive_failures,
        }

    if interval_hours is None:
        return {
            "priority": str(polling_config.get("priority") or "").strip() or None,
            "interval_hours": None,
            "effective_interval_hours": None,
            "schedule_state": "unscheduled",
            "next_run_at": None,
            "overdue_by_hours": None,
            "consecutive_failures": consecutive_failures,
        }

    backoff_multiplier = 1
    if str(health.get("status") or "").strip() == "error" and consecutive_failures > 0:
        backoff_multiplier = min(consecutive_failures + 1, 4)
    effective_interval_hours = interval_hours * backoff_multiplier

    if last_run_at is None:
        return {
            "priority": str(polling_config.get("priority") or "").strip() or None,
            "interval_hours": interval_hours,
            "effective_interval_hours": effective_interval_hours,
            "schedule_state": "due",
            "next_run_at": None,
            "overdue_by_hours": None,
            "consecutive_failures": consecutive_failures,
        }

    next_run_at = last_run_at + timedelta(hours=effective_interval_hours)
    overdue_by_hours = None
    schedule_state = "scheduled"
    if now >= next_run_at:
        schedule_state = "due"
        overdue_by_hours = round((now - next_run_at).total_seconds() / 3600, 2)

    return {
        "priority": str(polling_config.get("priority") or "").strip() or None,
        "interval_hours": interval_hours,
        "effective_interval_hours": effective_interval_hours,
        "schedule_state": schedule_state,
        "next_run_at": next_run_at,
        "overdue_by_hours": overdue_by_hours,
        "consecutive_failures": consecutive_failures,
    }


def _build_research_source(row: ResearchSourceRecord, *, now: datetime) -> ResearchSource:
    polling_config = row.polling_config or {}
    health = _source_health(polling_config)
    schedule = _compute_source_schedule(enabled=row.enabled, polling_config=polling_config, now=now)
    return ResearchSource(
        source_id=row.source_id,
        label=row.label,
        source_kind=row.source_kind,
        trust_level=row.trust_level,
        access_class=row.access_class,
        base_url=row.base_url,
        description=row.description,
        polling_config=polling_config,
        enabled=row.enabled,
        connector_id=str(polling_config.get("connector_id") or "") or None,
        default_mode=(polling_config.get("default_mode") or "fixture"),
        live_ready=_is_live_ready(polling_config),
        priority=schedule["priority"],
        schedule_summary=_schedule_summary(polling_config),
        schedule_state=schedule["schedule_state"],
        interval_hours=schedule["interval_hours"],
        effective_interval_hours=schedule["effective_interval_hours"],
        next_run_at=schedule["next_run_at"],
        overdue_by_hours=schedule["overdue_by_hours"],
        consecutive_failures=schedule["consecutive_failures"],
        health_status=health.get("status") or "idle",
        last_run_at=_parse_datetime(health.get("last_run_at")),
        last_success_at=_parse_datetime(health.get("last_success_at")),
        last_error_at=_parse_datetime(health.get("last_error_at")),
        last_error_detail=str(health.get("last_error_detail") or "") or None,
        last_document_count=_coerce_int(health.get("last_document_count")),
    )


def _is_live_ready(polling_config: dict[str, Any]) -> bool:
    if not polling_config:
        return False
    if polling_config.get("live_enabled") is False:
        return False
    connector_id = str(polling_config.get("connector_id") or "").strip()
    if connector_id == "europe_pmc_search":
        return bool(str(polling_config.get("query") or "").strip())
    if connector_id == "clinicaltrials_v2":
        return bool(str(polling_config.get("query") or "").strip())
    if connector_id == "rss_feed":
        return bool(str(polling_config.get("feed_url") or "").strip())
    return False


def _schedule_summary(polling_config: dict[str, Any]) -> str | None:
    interval_hours = _coerce_int(polling_config.get("interval_hours"))
    priority = str(polling_config.get("priority") or "").strip()
    default_mode = str(polling_config.get("default_mode") or "").strip()
    if interval_hours is None:
        return None
    suffix = f" • {priority} priority" if priority else ""
    mode_suffix = f" • {default_mode} mode" if default_mode else ""
    return f"Every {interval_hours}h{suffix}{mode_suffix}"


def _source_catalog_map() -> dict[str, dict[str, Any]]:
    return {item["source_id"]: item for item in load_research_source_catalog()}


def _topic_catalog_map() -> dict[str, dict[str, Any]]:
    return {item["topic_id"]: item for item in load_research_topic_catalog()}


def _select_source_ids(*, source_ids: list[str] | None, include_disabled: bool) -> list[str]:
    known = load_research_source_catalog()
    selected = []
    requested = {item for item in source_ids or [] if item}
    for descriptor in known:
        if requested and descriptor["source_id"] not in requested:
            continue
        if not include_disabled and not descriptor.get("enabled", True):
            continue
        selected.append(descriptor["source_id"])
    return selected


def _partition_due_sources(
    *,
    source_records: dict[str, ResearchSourceRecord],
    requested_source_ids: list[str],
    only_due: bool,
    now: datetime,
) -> tuple[list[str], list[str]]:
    if not only_due:
        return requested_source_ids, []

    selected: list[str] = []
    skipped: list[str] = []
    for source_id in requested_source_ids:
        record = source_records.get(source_id)
        if record is None:
            skipped.append(source_id)
            continue
        schedule = _compute_source_schedule(enabled=record.enabled, polling_config=record.polling_config or {}, now=now)
        if schedule["schedule_state"] == "due":
            selected.append(source_id)
        else:
            skipped.append(source_id)
    return selected, skipped


def _update_source_health(
    record: ResearchSourceRecord,
    *,
    status: str,
    last_run_at: datetime,
    last_success_at: datetime | None = None,
    last_error_at: datetime | None = None,
    last_error_detail: str | None = None,
    last_document_count: int | None = None,
    last_mode: str | None = None,
) -> None:
    polling_config = dict(record.polling_config or {})
    health = dict(polling_config.get("health") or {})
    prior_failures = max(_coerce_int(health.get("consecutive_failures")) or 0, 0)
    health["status"] = status
    health["last_run_at"] = last_run_at.isoformat()
    if last_success_at is not None:
        health["last_success_at"] = last_success_at.isoformat()
    if last_error_at is not None:
        health["last_error_at"] = last_error_at.isoformat()
    elif last_error_detail is None:
        health.pop("last_error_at", None)
    if last_error_detail:
        health["last_error_detail"] = last_error_detail
    elif last_error_detail is None:
        health.pop("last_error_detail", None)
    if last_document_count is not None:
        health["last_document_count"] = last_document_count
    if last_mode:
        health["last_mode"] = last_mode
    if status == "healthy":
        health["consecutive_failures"] = 0
    elif status == "error":
        health["consecutive_failures"] = prior_failures + 1
    polling_config["health"] = health
    record.polling_config = polling_config


def _normalize_seed_document(
    document: dict[str, Any],
    *,
    source_map: dict[str, dict[str, Any]],
    topic_descriptors: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_id = document["source_id"]
    source_descriptor = source_map[source_id]
    published_at = _parse_datetime(document.get("published_at"))
    title = str(document.get("title") or "").strip()
    abstract_text = str(document.get("abstract_text") or "").strip()
    body_text = "\n".join(part for part in [title, abstract_text] if part)
    graph_entities = _resolve_graph_entities(body_text)
    topic_scores, keyword_hits = _classify_topics(
        text=body_text,
        source_descriptor=source_descriptor,
        topic_descriptors=topic_descriptors,
        graph_entities=graph_entities,
    )
    topic_ids = list(topic_scores.keys())
    entity_tags = _extract_entity_tags(graph_entities)
    citation_key = _build_citation_key(document, published_at=published_at, source_label=source_descriptor["label"])
    dedupe_key = _build_dedupe_key(document)
    document_id = "rdoc-" + hashlib.sha256(dedupe_key.encode("utf-8")).hexdigest()[:12]

    evidence = _extract_evidence_items(
        text=body_text,
        citation_key=citation_key,
        keyword_hits=keyword_hits,
        topic_descriptors=topic_descriptors,
        graph_entities=graph_entities,
    )

    return {
        "document_id": document_id,
        "source_id": source_id,
        "source_identifier": document.get("source_identifier"),
        "document_type": document.get("document_type") or "research_update",
        "title": title,
        "abstract_text": abstract_text,
        "url": document.get("url"),
        "canonical_url": document.get("canonical_url") or document.get("url"),
        "doi": _clean_identifier(document.get("doi")),
        "pmid": _clean_identifier(document.get("pmid")),
        "nct_id": _clean_identifier(document.get("nct_id")),
        "citation_key": citation_key,
        "dedupe_key": dedupe_key,
        "published_at": published_at,
        "authors": [str(item).strip() for item in document.get("authors") or [] if str(item).strip()],
        "organizations": [
            str(item).strip()
            for item in document.get("organizations") or []
            if str(item).strip()
        ],
        "topic_ids": topic_ids,
        "entity_tags": entity_tags,
        "relevance_scores": topic_scores,
        "raw_metadata": {
            key: value
            for key, value in document.items()
            if key
            not in {
                "title",
                "abstract_text",
                "authors",
                "organizations",
            }
        },
        "graph_entities": graph_entities,
        "evidence": evidence,
    }


def _apply_document_provenance(
    normalized: dict[str, Any],
    *,
    batch: dict[str, Any],
    requested_mode: str,
    novelty_score: float,
) -> None:
    relevance_scores = dict(normalized.get("relevance_scores") or {})
    relevance_scores["novelty"] = novelty_score
    normalized["relevance_scores"] = relevance_scores

    raw_metadata = dict(normalized.get("raw_metadata") or {})
    raw_metadata["novelty_score"] = novelty_score
    raw_metadata["ingest_mode"] = batch.get("mode") or requested_mode
    raw_metadata["requested_ingest_mode"] = requested_mode
    raw_metadata["graph_entities"] = list(normalized.get("graph_entities") or [])
    raw_metadata["provenance"] = {
        "connector_id": batch.get("connector_id"),
        "source_url": batch.get("source_url"),
        "query": batch.get("query"),
        "fetched_at": (
            _coerce_utc(batch.get("fetched_at")).isoformat()
            if _coerce_utc(batch.get("fetched_at")) is not None
            else None
        ),
        "fixture_path": batch.get("fixture_path"),
    }
    normalized["raw_metadata"] = raw_metadata


def _calculate_novelty_score(
    *,
    document: dict[str, Any],
    source_descriptor: dict[str, Any],
    existing: ResearchDocumentRecord | None,
) -> float:
    if existing is not None:
        return 0.12

    published_at = _parse_datetime(document.get("published_at"))
    recency_bonus = 0.18
    if published_at is not None:
        age_days = max(0.0, (_utcnow() - published_at).total_seconds() / 86400.0)
        recency_bonus = max(0.02, 0.28 - min(age_days, 21) * 0.01)

    trust_bonus = _TRUST_SCORES.get(str(source_descriptor.get("trust_level") or "medium"), 0.1)
    topic_hint = 0.04 if any(
        keyword
        for keyword in ("trial", "biomarker", "screening", "workflow", "benchmark")
        if keyword in f"{document.get('title', '')} {document.get('abstract_text', '')}".lower()
    ) else 0.0
    return round(min(0.99, 0.42 + recency_bonus + trust_bonus + topic_hint), 4)


def _classify_topics(
    *,
    text: str,
    source_descriptor: dict[str, Any],
    topic_descriptors: dict[str, dict[str, Any]],
    graph_entities: list[dict[str, Any]],
) -> tuple[dict[str, float], dict[str, list[str]]]:
    text_l = text.lower()
    trust_bonus = _TRUST_SCORES.get(str(source_descriptor.get("trust_level") or "medium"), 0.1)
    topic_scores: dict[str, float] = {}
    keyword_hits: dict[str, list[str]] = {}

    for topic_id, descriptor in topic_descriptors.items():
        matches = sorted(
            {
                keyword
                for keyword in descriptor.get("keywords") or []
                if keyword.lower() in text_l
            }
        )
        if not matches:
            matches = []
        if matches:
            score = min(1.0, round(0.22 * len(matches) + trust_bonus, 4))
            topic_scores[topic_id] = score
            keyword_hits[topic_id] = matches

    for entity in graph_entities:
        for topic_id in entity.get("topic_ids") or []:
            if topic_id not in topic_descriptors:
                continue
            graph_match_terms = [str(item) for item in entity.get("match_terms") or []]
            boost = min(
                0.96,
                round(
                    (topic_scores.get(topic_id) or 0.0)
                    + 0.16
                    + 0.08 * len(graph_match_terms)
                    + 0.06 * float(entity.get("confidence") or 0.0)
                    + trust_bonus * 0.5,
                    4,
                ),
            )
            topic_scores[topic_id] = boost
            keyword_hits.setdefault(topic_id, [])
            for term in graph_match_terms[:2]:
                if term not in keyword_hits[topic_id]:
                    keyword_hits[topic_id].append(term)

    return topic_scores, keyword_hits


def _resolve_graph_entities(text: str) -> list[dict[str, Any]]:
    text_l = text.lower()
    indexes = load_research_graph_indexes()
    resolved: list[dict[str, Any]] = []

    for node in indexes["nodes"]:
        matched_terms = [
            term
            for term in node.get("match_terms") or []
            if term and term.lower() in text_l
        ]
        if not matched_terms:
            continue
        confidence = round(min(0.98, 0.42 + 0.08 * len(matched_terms) + 0.04 * len(node.get("topic_ids") or [])), 2)
        resolved.append(
            {
                "node_id": node["node_id"],
                "label": node.get("label") or node["node_id"],
                "node_type": node.get("node_type") or "entity",
                "description": node.get("description"),
                "tags": [str(item) for item in node.get("tags") or []],
                "topic_ids": [str(item) for item in node.get("topic_ids") or []],
                "match_terms": matched_terms[:3],
                "related_node_ids": [str(item) for item in node.get("related_node_ids") or []],
                "confidence": confidence,
            }
        )

    resolved.sort(
        key=lambda item: (
            -(item.get("confidence") or 0.0),
            -len(item.get("topic_ids") or []),
            str(item.get("label") or ""),
        )
    )
    return resolved


def _extract_entity_tags(graph_entities: list[dict[str, Any]]) -> list[str]:
    tags: list[str] = []
    for entity in graph_entities:
        node_id = str(entity.get("node_id") or "").strip()
        tags.append(node_id)
        tags.extend([str(item) for item in entity.get("tags") or []])

    unique = [tag for tag in dict.fromkeys(tag for tag in tags if tag)]
    return unique


def _extract_evidence_items(
    *,
    text: str,
    citation_key: str,
    keyword_hits: dict[str, list[str]],
    topic_descriptors: dict[str, dict[str, Any]],
    graph_entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for topic_id, hits in keyword_hits.items():
        descriptor = topic_descriptors[topic_id]
        claim_type = str(descriptor.get("claim_type") or topic_id)
        for hit in hits[:2]:
            sentence, start, end = _sentence_for_term(text, hit)
            evidence.append(
                {
                    "evidence_text": sentence,
                    "char_start": start,
                    "char_end": end,
                    "claim_text": (
                        f"{descriptor['label']} appears in a cited pancreatic oncology update via '{hit}'."
                    ),
                    "claim_type": claim_type,
                    "entity_tags": [topic_id, *descriptor.get("entity_tags", [])],
                    "citation_label": citation_key,
                    "confidence": round(min(0.98, 0.55 + 0.08 * len(hits)), 2),
                }
            )
    for entity in graph_entities:
        if not entity.get("match_terms"):
            continue
        primary_term = str((entity.get("match_terms") or [""])[0]).strip()
        if not primary_term:
            continue
        sentence, start, end = _sentence_for_term(text, primary_term)
        evidence.append(
            {
                "evidence_text": sentence,
                "char_start": start,
                "char_end": end,
                "claim_text": (
                    f"{entity.get('label') or entity.get('node_id')} anchors graph-backed pancreatic oncology reasoning."
                ),
                "claim_type": f"graph_entity:{entity.get('node_type') or 'entity'}",
                "entity_tags": [
                    str(entity.get("node_id") or ""),
                    *[str(item) for item in entity.get("tags") or []],
                ],
                "citation_label": citation_key,
                "confidence": float(entity.get("confidence") or 0.5),
            }
        )
    return evidence


def _sentence_for_term(text: str, term: str) -> tuple[str, int, int]:
    text_l = text.lower()
    term_l = term.lower()
    match_index = text_l.find(term_l)
    if match_index < 0:
        return text[:220], 0, 0

    sentences = _SENTENCE_SPLIT_RE.split(text)
    cursor = 0
    for sentence in sentences:
        start = cursor
        end = cursor + len(sentence)
        if start <= match_index <= end:
            relative_start = max(0, match_index - start)
            relative_end = relative_start + len(term)
            return sentence.strip(), relative_start, relative_end
        cursor = end + 1

    return text[max(0, match_index - 80) : match_index + 140], 0, len(term)


def _build_citation_key(
    document: dict[str, Any],
    *,
    published_at: datetime | None,
    source_label: str,
) -> str:
    if document.get("doi"):
        return f"DOI {document['doi']}"
    if document.get("pmid"):
        return f"PMID {document['pmid']}"
    if document.get("nct_id"):
        return f"NCT {document['nct_id']}"
    year = published_at.year if published_at else "n.d."
    source_short = "".join(_WORD_RE.findall(source_label))[:16] or "source"
    return f"{source_short} {year}"


def _build_dedupe_key(document: dict[str, Any]) -> str:
    for prefix, key in (
        ("doi", "doi"),
        ("pmid", "pmid"),
        ("nct", "nct_id"),
        ("url", "canonical_url"),
        ("url", "url"),
    ):
        value = _clean_identifier(document.get(key))
        if value:
            return f"{prefix}:{value.lower()}"
    fingerprint = "|".join(
        [
            str(document.get("source_id") or ""),
            str(document.get("title") or "").strip().lower(),
            str(document.get("published_at") or "").strip(),
        ]
    )
    return "hash:" + hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()


def _clean_identifier(value: object) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _coerce_int(value: object) -> int | None:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed


def _coerce_float(value: object) -> float | None:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed


def _parse_datetime(value: object) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _refresh_topic_metrics(session: Any) -> None:
    topics = session.execute(select(ResearchTopicRecord)).scalars().all()
    documents = session.execute(select(ResearchDocumentRecord)).scalars().all()

    for topic in topics:
        topic_docs = [
            document
            for document in documents
            if topic.topic_id in (document.topic_ids or [])
        ]
        topic.document_count = len(topic_docs)
        topic.last_document_at = max(
            (
                _coerce_utc(document.published_at)
                for document in topic_docs
                if document.published_at is not None
            ),
            default=None,
        )
        topic.topic_heat = round(
            sum((document.relevance_scores or {}).get(topic.topic_id, 0.0) for document in topic_docs),
            4,
        )


def _build_document_response(
    session: Any,
    row: ResearchDocumentRecord,
    source_map: dict[str, ResearchSourceRecord],
    topic_label_map: dict[str, str],
) -> ResearchDocument:
    evidence_rows = session.execute(
        select(ResearchEvidenceRecord)
        .where(ResearchEvidenceRecord.document_id == row.document_id)
        .order_by(ResearchEvidenceRecord.id.asc())
    ).scalars().all()
    source = source_map.get(row.source_id)
    return ResearchDocument(
        document_id=row.document_id,
        source_id=row.source_id,
        source_label=source.label if source is not None else row.source_id,
        source_kind=source.source_kind if source is not None else "unknown",
        document_type=row.document_type,
        title=row.title,
        abstract_text=row.abstract_text,
        url=row.url,
        canonical_url=row.canonical_url,
        doi=row.doi,
        pmid=row.pmid,
        nct_id=row.nct_id,
        citation_key=row.citation_key,
        published_at=row.published_at,
        authors=row.authors or [],
        organizations=row.organizations or [],
        topic_ids=row.topic_ids or [],
        topic_labels=[topic_label_map[item] for item in row.topic_ids or [] if item in topic_label_map],
        entity_tags=row.entity_tags or [],
        relevance_scores=row.relevance_scores or {},
        novelty_score=_coerce_float((row.raw_metadata or {}).get("novelty_score")),
        ingest_mode=str((row.raw_metadata or {}).get("ingest_mode") or "") or None,
        provenance=dict((row.raw_metadata or {}).get("provenance") or {}),
        graph_entities=[
            ResearchGraphEntity.model_validate(item)
            for item in list((row.raw_metadata or {}).get("graph_entities") or [])
        ],
        evidence=[
            ResearchEvidence(
                evidence_text=item.evidence_text,
                char_start=item.char_start,
                char_end=item.char_end,
                claim_text=item.claim_text,
                claim_type=item.claim_type,
                entity_tags=item.entity_tags or [],
                citation_label=item.citation_label,
                confidence=item.confidence,
            )
            for item in evidence_rows
        ],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _build_digest_payload(
    *,
    documents: list[ResearchDocumentRecord],
    topic_label_map: dict[str, str],
    source_map: dict[str, ResearchSourceRecord],
) -> dict[str, Any]:
    docs = sorted(
        documents,
        key=lambda item: item.published_at or datetime.fromtimestamp(0, tz=timezone.utc),
        reverse=True,
    )[:8]
    topic_counter: Counter[str] = Counter()
    opportunity_counter: Counter[str] = Counter()

    for document in docs:
        topic_counter.update(document.topic_ids or [])
        for topic_id in document.topic_ids or []:
            topic_descriptor = _topic_catalog_map().get(topic_id) or {}
            opportunity_counter.update(topic_descriptor.get("opportunity_types") or [])

    ranked_topics = [topic_id for topic_id, _count in topic_counter.most_common(5)]
    stage_1 = _build_stage_1_opinions(
        documents=docs,
        ranked_topics=ranked_topics,
        topic_label_map=topic_label_map,
    )
    stage_2 = _build_stage_2_rankings(
        documents=docs,
        ranked_topics=ranked_topics,
        topic_counter=topic_counter,
        opportunity_counter=opportunity_counter,
        topic_label_map=topic_label_map,
        source_map=source_map,
    )
    stage_3 = _build_stage_3_synthesis(
        documents=docs,
        ranked_topics=ranked_topics,
        topic_label_map=topic_label_map,
        stage_1=stage_1,
        stage_2=stage_2,
        source_map=source_map,
    )
    council = ResearchCouncilPayload(
        stage_1=stage_1,
        stage_2=stage_2,
        stage_3=stage_3,
    )
    disagreement_score = _calculate_disagreement_score(stage_2)
    generated_at = _utcnow()
    supporting_document_ids = [document.document_id for document in docs]
    key_takeaways = [
        (
            f"{topic_label_map.get(topic_id, topic_id)} stayed active across "
            f"{topic_counter[topic_id]} recent cited update(s)."
        )
        for topic_id in ranked_topics[:3]
    ]
    for document in docs[:2]:
        key_takeaways.append(f"{document.title} ({document.citation_key})")

    key_takeaways = key_takeaways[:5]
    summary_markdown = _render_digest_markdown(
        generated_at=generated_at,
        ranked_topics=ranked_topics,
        topic_label_map=topic_label_map,
        key_takeaways=key_takeaways,
        documents=docs,
        stage_1=stage_1,
        stage_2=stage_2,
        stage_3=stage_3,
        disagreement_score=disagreement_score,
    )
    digest_id = f"digest-{generated_at.strftime('%Y%m%d-%H%M%S')}"
    artifact_json = {
        "digest_id": digest_id,
        "title": "Pancreatic oncology research intelligence digest",
        "generated_at": generated_at.isoformat(),
        "topic_ids": ranked_topics,
        "topic_labels": [topic_label_map.get(item, item) for item in ranked_topics],
        "disagreement_score": disagreement_score,
        "key_takeaways": key_takeaways,
        "supporting_documents": [
            {
                "document_id": document.document_id,
                "title": document.title,
                "citation_key": document.citation_key,
                "url": document.url,
            }
            for document in docs
        ],
        "council": council.model_dump(mode="json"),
    }
    return {
        "digest_id": digest_id,
        "title": "Pancreatic oncology research intelligence digest",
        "window_start": min((document.published_at for document in docs if document.published_at), default=None),
        "window_end": max((document.published_at for document in docs if document.published_at), default=None),
        "generated_at": generated_at,
        "topic_ids": ranked_topics,
        "supporting_document_ids": supporting_document_ids,
        "council_payload": council.model_dump(mode="json"),
        "summary_markdown": summary_markdown,
        "summary_json": {
            "key_takeaways": key_takeaways,
        },
        "disagreement_score": disagreement_score,
        "citation_count": len(supporting_document_ids),
        "artifact_json": artifact_json,
    }


def _build_stage_1_opinions(
    *,
    documents: list[ResearchDocumentRecord],
    ranked_topics: list[str],
    topic_label_map: dict[str, str],
) -> list[ResearchCouncilStage1Opinion]:
    opinions: list[ResearchCouncilStage1Opinion] = []
    top_topics = [topic_label_map.get(item, item) for item in ranked_topics[:3]]
    top_citations = [document.citation_key for document in documents[:3]]
    graph_labels = _top_graph_labels(documents, limit=4)
    source_kinds = Counter(_document_source_kind(document) for document in documents)

    for persona in _PERSONAS:
        opportunity_types = []
        confidence_label = "medium"
        key_claims: list[str] = []
        open_questions: list[str] = []
        evidence_gaps: list[str] = []

        if persona["persona"] == "literature_scout":
            opportunity_types = ["benchmark_gap", "trial_catalog_gap"]
            confidence_label = "high" if _count_high_trust_documents(documents) >= 3 else "medium"
            key_claims = [
                f"Recent cited movement concentrates in {', '.join(top_topics) or 'general pancreatic oncology updates'}.",
                f"Graph activity is anchored by {', '.join(graph_labels[:2]) or 'broad disease-level concepts'}.",
            ]
            open_questions = [
                "Which cited signals represent durable movement rather than one-off novelty spikes?",
                "Are biomarker and screening claims replicated outside the current cohorts or source mix?",
            ]
            evidence_gaps = [
                "Need clearer replication status across cohorts and institutions.",
                "Need stronger separation between emerging and well-established evidence.",
            ]
        elif persona["persona"] == "translational_oncologist":
            opportunity_types = ["trial_catalog_gap", "case_brief"]
            confidence_label = "high" if any(document.nct_id for document in documents) else "medium"
            key_claims = [
                "Trial, procedure, and follow-up signals are useful only when kept separate from diagnosis claims.",
                f"Current digest pressure is strongest around {', '.join(top_topics[:2]) or 'screening and trial implications'}.",
            ]
            open_questions = [
                "Which cohorts require tissue confirmation, biomarker gating, or surveillance-specific branching?",
                "How should case briefs distinguish surveillance action from explicit malignancy suspicion?",
            ]
            evidence_gaps = [
                "Need more explicit cohort and eligibility detail from trial-linked sources.",
                "Need stronger procedural evidence for follow-up timing and escalation pathways.",
            ]
        else:
            opportunity_types = ["community_project", "external_tooling"]
            confidence_label = "medium" if source_kinds.get("news", 0) + source_kinds.get("preprint", 0) >= 1 else "low"
            key_claims = [
                "The most reusable output is still benchmark, tooling, and open evaluation infrastructure.",
                f"Graph links between {', '.join(graph_labels[:2]) or 'workflow and data artifacts'} suggest contributor-ready build opportunities.",
            ]
            open_questions = [
                "Which datasets, manifests, or benchmark packs could be released or expanded openly next?",
                "What tooling would let contributors validate these discoveries without relying on opaque automation?",
            ]
            evidence_gaps = [
                "Need more openly reusable labels, manifests, and benchmark metadata.",
                "Need clearer mapping from research findings to contributor-sized build tasks.",
            ]

        opinions.append(
            ResearchCouncilStage1Opinion(
                persona=persona["persona"],
                focus=persona["focus"],
                summary=(
                    f"Primary movement is around {', '.join(top_topics) or 'general pancreatic oncology'} "
                    f"with cited support from {', '.join(top_citations) or 'the current corpus'}."
                ),
                citations=top_citations,
                proposed_opportunity_types=opportunity_types,
                primary_topics=top_topics,
                confidence_label=confidence_label,
                key_claims=key_claims,
                open_questions=open_questions,
                evidence_gaps=evidence_gaps,
            )
        )
    return opinions


def _build_stage_2_rankings(
    *,
    documents: list[ResearchDocumentRecord],
    ranked_topics: list[str],
    topic_counter: Counter[str],
    opportunity_counter: Counter[str],
    topic_label_map: dict[str, str],
    source_map: dict[str, ResearchSourceRecord],
) -> list[ResearchCouncilStage2Ranking]:
    rankings: list[ResearchCouncilStage2Ranking] = []
    reversed_topics = list(reversed(ranked_topics))
    challenge_targets = {
        "literature_scout": "open_source_builder",
        "translational_oncologist": "literature_scout",
        "open_source_builder": "translational_oncologist",
    }
    high_trust_docs = _count_high_trust_documents(documents)
    preprint_like_docs = sum(
        1 for document in documents if _document_source_kind(document) in {"preprint", "news"}
    )
    for persona in _PERSONAS:
        challenge_target = challenge_targets.get(persona["persona"])
        peer_critiques: list[ResearchCouncilPeerCritique]
        preferred_actions: list[str]
        confidence_adjustment = "hold"
        if persona["persona"] == "literature_scout":
            topics = ranked_topics[:3]
            opportunities = [item for item, _count in opportunity_counter.most_common(2)]
            critique = "Breadth is improving, but benchmarkable wording variation still needs explicit capture."
            peer_critiques = [
                ResearchCouncilPeerCritique(
                    reviewer_persona="literature_scout",
                    target_persona=challenge_target or "open_source_builder",
                    alignment="mixed",
                    strengths=["Good pressure toward reusable tooling and benchmark output."],
                    concerns=["Tooling proposals may outrun the strength or maturity of the current evidence base."],
                    requested_evidence=[
                        "Show replication or independent confirmation before elevating emerging findings into roadmap commitments.",
                    ],
                )
            ]
            preferred_actions = [
                "Track which topics are moving because of high-trust sources versus preprints or news.",
                "Preserve a question backlog for signals that look novel but still under-validated.",
            ]
            confidence_adjustment = "hold" if high_trust_docs >= 2 else "lower"
        elif persona["persona"] == "translational_oncologist":
            topics = ranked_topics[:2] + reversed_topics[:1]
            opportunities = ["trial_catalog_gap", "case_brief"]
            critique = "Clinical utility rises when trial cues and follow-up implications stay separated from diagnosis claims."
            peer_critiques = [
                ResearchCouncilPeerCritique(
                    reviewer_persona="translational_oncologist",
                    target_persona=challenge_target or "literature_scout",
                    alignment="mixed",
                    strengths=["Strong topic surveillance and breadth across the cited stream."],
                    concerns=["Breadth alone does not resolve cohort eligibility, follow-up timing, or tissue-confirmation needs."],
                    requested_evidence=[
                        "Surface cohort-specific eligibility, procedure, and escalation details before promoting translational claims.",
                    ],
                )
            ]
            preferred_actions = [
                "Map cited trial and procedure language into explicit case-brief and trial-catalog follow-ups.",
                "Keep surveillance and malignancy-escalation pathways operationally separate.",
            ]
            confidence_adjustment = "raise" if any(document.nct_id for document in documents) else "hold"
        else:
            topics = reversed_topics[:2] + ranked_topics[:1]
            opportunities = ["community_project", "benchmark_gap"]
            critique = "The highest-leverage work is still tooling and dataset infrastructure, not more black-box scoring."
            peer_critiques = [
                ResearchCouncilPeerCritique(
                    reviewer_persona="open_source_builder",
                    target_persona=challenge_target or "translational_oncologist",
                    alignment="contests" if preprint_like_docs else "mixed",
                    strengths=["Keeps the digest tied to operationally meaningful trial and follow-up consequences."],
                    concerns=["A trial-centric view can underweight benchmark, dataset, and tooling work the community still needs."],
                    requested_evidence=[
                        "Show what benchmark or tooling artifact would make the cited discovery reusable by outside contributors.",
                    ],
                )
            ]
            preferred_actions = [
                "Turn graph-backed findings into benchmark specs, manifests, and issue-ready tooling proposals.",
                "Avoid promoting discovery output that does not yet map to a reproducible public artifact.",
            ]
            confidence_adjustment = "lower" if preprint_like_docs > high_trust_docs else "hold"

        rankings.append(
            ResearchCouncilStage2Ranking(
                persona=persona["persona"],
                ranked_topics=[topic_label_map.get(item, item) for item in topics if item],
                ranked_opportunity_types=[item for item in opportunities if item],
                critique=critique,
                challenge_target_persona=challenge_target,
                peer_critiques=peer_critiques,
                preferred_actions=preferred_actions,
                confidence_adjustment=confidence_adjustment,
            )
        )
    return rankings


def _build_stage_3_synthesis(
    *,
    documents: list[ResearchDocumentRecord],
    ranked_topics: list[str],
    topic_label_map: dict[str, str],
    stage_1: list[ResearchCouncilStage1Opinion],
    stage_2: list[ResearchCouncilStage2Ranking],
    source_map: dict[str, ResearchSourceRecord],
) -> ResearchCouncilStage3Synthesis:
    consensus_points = [
        (
            f"{topic_label_map.get(topic_id, topic_id)} has enough cited volume to justify a standing watchlist."
        )
        for topic_id in ranked_topics[:3]
    ]
    disagreement_points = []
    evidence_gaps = _unique_preserve_order(
        item
        for opinion in stage_1
        for item in opinion.evidence_gaps
    )[:5]
    open_questions = _unique_preserve_order(
        item
        for opinion in stage_1
        for item in opinion.open_questions
    )[:5]
    if len(ranked_topics) > 2:
        disagreement_points.append(
            "Agents diverged on whether the next step should prioritize trial catalog depth or benchmark tooling breadth."
        )
    if any(document.nct_id for document in documents):
        disagreement_points.append(
            "Trial-heavy sources point toward matching opportunities, while workflow sources point toward open benchmark work."
        )
    disagreement_points.extend(
        _unique_preserve_order(
            concern
            for ranking in stage_2
            for critique in ranking.peer_critiques
            if critique.alignment != "supports"
            for concern in critique.concerns
        )[:3]
    )
    recommended_actions = [
        "Refresh the benchmark backlog with new wording, confounder, or follow-up variants from this digest.",
        "Review trial-catalog gaps surfaced by the current cited corpus before editing rule assets.",
        "Carry unresolved questions into the next digest rather than collapsing them into a single narrative.",
        "Publish only cited takeaways and keep promotion actions human-gated.",
    ]
    next_experiments = [
        "Compare benchmark coverage against the current graph entities to see which active concepts still lack evaluation fixtures.",
        "Stress-test case briefs against trial-eligibility and follow-up language surfaced in this digest.",
        "Track whether high-novelty graph entities persist across future high-trust sources before broad promotion.",
    ]
    promotion_guardrails = [
        "Do not promote claims that remain uncited or supported only by weakly aligned sources.",
        "Separate exploratory questions from operational recommendations in every promoted artifact.",
        "Require a measurable downstream artifact such as a benchmark spec, rule change, or trial-catalog update before escalating action.",
    ]
    overall_confidence = _derive_council_confidence(documents=documents, source_map=source_map, stage_2=stage_2)
    return ResearchCouncilStage3Synthesis(
        chairman_summary=(
            "The council agrees that pancreatic oncology monitoring should feed benchmark growth, trial-catalog upkeep, "
            "and contributor tooling, while remaining separate from automatic case scoring and while preserving open questions "
            "instead of forcing false certainty."
        ),
        overall_confidence=overall_confidence,
        consensus_points=consensus_points,
        disagreement_points=disagreement_points,
        evidence_gaps=evidence_gaps,
        open_questions=open_questions,
        recommended_actions=recommended_actions,
        next_experiments=next_experiments,
        promotion_guardrails=promotion_guardrails,
    )


def _calculate_disagreement_score(stage_2: list[ResearchCouncilStage2Ranking]) -> float:
    topic_first_choices = [item.ranked_topics[0] for item in stage_2 if item.ranked_topics]
    opportunity_first_choices = [
        item.ranked_opportunity_types[0]
        for item in stage_2
        if item.ranked_opportunity_types
    ]
    peer_critiques = [critique for item in stage_2 for critique in item.peer_critiques]
    if not topic_first_choices:
        return 0.0
    topic_divergence = len(set(topic_first_choices)) / max(1, len(topic_first_choices))
    opportunity_divergence = (
        len(set(opportunity_first_choices)) / max(1, len(opportunity_first_choices))
        if opportunity_first_choices
        else 0.0
    )
    critique_tension = (
        sum(1 for critique in peer_critiques if critique.alignment != "supports") / max(1, len(peer_critiques))
        if peer_critiques
        else 0.0
    )
    return round(min(1.0, 0.45 * topic_divergence + 0.25 * opportunity_divergence + 0.30 * critique_tension), 4)


def _top_graph_labels(documents: list[ResearchDocumentRecord], *, limit: int) -> list[str]:
    counts: Counter[str] = Counter()
    for document in documents:
        for entity in list((document.raw_metadata or {}).get("graph_entities") or []):
            label = str(entity.get("label") or entity.get("node_id") or "").strip()
            if label:
                counts[label] += 1
    return [label for label, _count in counts.most_common(limit)]


def _document_source_kind(document: ResearchDocumentRecord) -> str:
    source_descriptor = _source_catalog_map().get(document.source_id) or {}
    return str(source_descriptor.get("source_kind") or "unknown")


def _count_high_trust_documents(documents: list[ResearchDocumentRecord]) -> int:
    source_catalog = _source_catalog_map()
    return sum(
        1
        for document in documents
        if str((source_catalog.get(document.source_id) or {}).get("trust_level") or "") == "high"
    )


def _derive_council_confidence(
    *,
    documents: list[ResearchDocumentRecord],
    source_map: dict[str, ResearchSourceRecord],
    stage_2: list[ResearchCouncilStage2Ranking],
) -> str:
    high_trust_docs = sum(
        1
        for document in documents
        if (
            source_map.get(document.source_id) is not None
            and source_map[document.source_id].trust_level == "high"
        )
    )
    evidence_types = {
        (source_map.get(document.source_id).source_kind if source_map.get(document.source_id) else "unknown")
        for document in documents
    }
    any_lower = any(item.confidence_adjustment == "lower" for item in stage_2)
    if high_trust_docs >= 3 and {"trial_registry", "guideline", "literature"} & evidence_types and not any_lower:
        return "high"
    if high_trust_docs >= 2:
        return "medium"
    return "low"


def _unique_preserve_order(items: Any) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output


def _normalize_council_payload(payload: Any) -> dict[str, Any]:
    value = dict(payload or {})
    value.setdefault("stage_1", [])
    value.setdefault("stage_2", [])
    value.setdefault(
        "stage_3",
        {
            "chairman_summary": "Council synthesis unavailable for this digest version.",
            "overall_confidence": "medium",
            "consensus_points": [],
            "disagreement_points": [],
            "evidence_gaps": [],
            "open_questions": [],
            "recommended_actions": [],
            "next_experiments": [],
            "promotion_guardrails": [],
        },
    )
    return value


def _render_digest_markdown(
    *,
    generated_at: datetime,
    ranked_topics: list[str],
    topic_label_map: dict[str, str],
    key_takeaways: list[str],
    documents: list[ResearchDocumentRecord],
    stage_1: list[ResearchCouncilStage1Opinion],
    stage_2: list[ResearchCouncilStage2Ranking],
    stage_3: ResearchCouncilStage3Synthesis,
    disagreement_score: float,
) -> str:
    lines = [
        "# Pancreatic oncology research intelligence digest",
        "",
        f"Generated: {generated_at.isoformat()}",
        "",
        "## Topic heat",
    ]
    for topic_id in ranked_topics[:5]:
        lines.append(f"- {topic_label_map.get(topic_id, topic_id)}")
    lines.extend(["", "## Key takeaways"])
    for takeaway in key_takeaways:
        lines.append(f"- {takeaway}")
    lines.extend(["", "## Supporting documents"])
    for document in documents:
        lines.append(f"- {document.title} ({document.citation_key})")
    lines.extend(["", "## Council stage 1"])
    for opinion in stage_1:
        lines.append(
            f"- {opinion.persona} ({opinion.confidence_label} confidence): {opinion.summary}"
        )
        if opinion.primary_topics:
            lines.append(f"  - topics: {', '.join(opinion.primary_topics)}")
        for claim in opinion.key_claims:
            lines.append(f"  - claim: {claim}")
        for question in opinion.open_questions[:2]:
            lines.append(f"  - question: {question}")
        for gap in opinion.evidence_gaps[:2]:
            lines.append(f"  - gap: {gap}")
    lines.extend(["", "## Council stage 2"])
    for ranking in stage_2:
        lines.append(
            f"- {ranking.persona}: topics {', '.join(ranking.ranked_topics)}; critique: {ranking.critique}"
        )
        if ranking.challenge_target_persona:
            lines.append(f"  - challenges: {ranking.challenge_target_persona}")
        if ranking.ranked_opportunity_types:
            lines.append(
                f"  - opportunity types: {', '.join(ranking.ranked_opportunity_types)}"
            )
        if ranking.confidence_adjustment:
            lines.append(f"  - confidence adjustment: {ranking.confidence_adjustment}")
        for action in ranking.preferred_actions[:2]:
            lines.append(f"  - preferred action: {action}")
        for critique in ranking.peer_critiques:
            lines.append(
                f"  - peer review ({critique.alignment}) on {critique.target_persona}: "
                f"{'; '.join(critique.concerns or critique.strengths)}"
            )
            for requested in critique.requested_evidence[:1]:
                lines.append(f"    - requested evidence: {requested}")
    lines.extend(
        [
            "",
            "## Chairman synthesis",
            stage_3.chairman_summary,
            "",
            f"Overall confidence: {stage_3.overall_confidence}",
            f"Disagreement score: {disagreement_score:.2f}",
            "",
            "Consensus:",
        ]
    )
    for item in stage_3.consensus_points:
        lines.append(f"- {item}")
    if stage_3.disagreement_points:
        lines.append("")
        lines.append("Disagreement:")
        for item in stage_3.disagreement_points:
            lines.append(f"- {item}")
    if stage_3.evidence_gaps:
        lines.append("")
        lines.append("Evidence gaps:")
        for item in stage_3.evidence_gaps:
            lines.append(f"- {item}")
    if stage_3.open_questions:
        lines.append("")
        lines.append("Open questions:")
        for item in stage_3.open_questions:
            lines.append(f"- {item}")
    lines.append("")
    lines.append("Recommended actions:")
    for item in stage_3.recommended_actions:
        lines.append(f"- {item}")
    if stage_3.next_experiments:
        lines.append("")
        lines.append("Next experiments:")
        for item in stage_3.next_experiments:
            lines.append(f"- {item}")
    if stage_3.promotion_guardrails:
        lines.append("")
        lines.append("Promotion guardrails:")
        for item in stage_3.promotion_guardrails:
            lines.append(f"- {item}")
    return "\n".join(lines)


def _upsert_opportunities_for_digest(
    *,
    session: Any,
    digest: ResearchDigestRecord,
    topic_record_map: dict[str, ResearchTopicRecord],
    topic_label_map: dict[str, str],
    source_map: dict[str, ResearchSourceRecord],
    documents: list[ResearchDocumentRecord],
    council: ResearchCouncilPayload,
    write_artifacts: bool,
) -> dict[str, Any]:
    created = 0
    updated = 0
    artifact_paths: list[str] = []
    topic_to_documents: dict[str, list[ResearchDocumentRecord]] = defaultdict(list)
    for document in documents:
        for topic_id in document.topic_ids or []:
            topic_to_documents[topic_id].append(document)

    for topic_id in digest.topic_ids[:4]:
        topic = topic_record_map.get(topic_id)
        if topic is None:
            continue
        supporting_documents = topic_to_documents.get(topic_id, [])[:3]
        if not supporting_documents:
            continue
        for opportunity_type in (topic.opportunity_types or [])[:2]:
            opportunity_id = f"ropp-{opportunity_type}-{topic_id}"
            action_payload = _build_opportunity_action_payload(
                opportunity_id=opportunity_id,
                digest=digest,
                opportunity_type=opportunity_type,
                topic=topic,
                topic_label_map=topic_label_map,
                source_map=source_map,
                supporting_documents=supporting_documents,
                council=council,
            )
            title = _opportunity_title(opportunity_type=opportunity_type, topic_label=topic.label)
            summary = _opportunity_summary(
                title=title,
                action_payload=action_payload,
            )
            confidence = _derive_opportunity_confidence(
                opportunity_type=opportunity_type,
                topic=topic,
                supporting_documents=supporting_documents,
                council=council,
            )
            record = session.get(ResearchOpportunityRecord, opportunity_id)
            if record is None:
                record = ResearchOpportunityRecord(
                    opportunity_id=opportunity_id,
                    opportunity_type=opportunity_type,
                    title=title,
                    summary=summary,
                    status="proposed",
                    confidence_score=confidence,
                    topic_ids=[topic_id],
                    supporting_document_ids=[item.document_id for item in supporting_documents],
                    related_rationale_codes=topic.related_rationale_codes or [],
                    related_trial_ids=topic.related_trial_tags or [],
                    action_payload=action_payload.model_dump(mode="json"),
                )
                session.add(record)
                created += 1
            else:
                record.title = title
                record.summary = summary
                record.status = "proposed" if record.status != "promoted" else record.status
                record.confidence_score = confidence
                record.topic_ids = [topic_id]
                record.supporting_document_ids = [item.document_id for item in supporting_documents]
                record.related_rationale_codes = topic.related_rationale_codes or []
                record.related_trial_ids = topic.related_trial_tags or []
                record.action_payload = action_payload.model_dump(mode="json")
                updated += 1
            if write_artifacts:
                session.flush()
                artifact_paths.extend(
                    _write_opportunity_action_artifacts(
                        row=record,
                        topic_label_map=topic_label_map,
                    )
                )
    return {"created": created, "updated": updated, "artifact_paths": artifact_paths}


def _opportunity_title(*, opportunity_type: str, topic_label: str) -> str:
    if opportunity_type == "rule_gap":
        return f"Review rule coverage for {topic_label.lower()}"
    if opportunity_type == "benchmark_gap":
        return f"Extend benchmark cases for {topic_label.lower()}"
    if opportunity_type == "trial_catalog_gap":
        return f"Refine trial catalog mapping for {topic_label.lower()}"
    if opportunity_type == "case_brief":
        return f"Add richer case-brief support for {topic_label.lower()}"
    if opportunity_type == "community_project":
        return f"Scope an open-source project around {topic_label.lower()}"
    return f"Explore external tooling for {topic_label.lower()}"


def _opportunity_summary(
    *,
    title: str,
    action_payload: ResearchOpportunityActionPayload,
) -> str:
    citations = ", ".join(item.citation_key for item in action_payload.evidence_bundle[:2]) or "the current cited corpus"
    return (
        f"{title}. {action_payload.why_now} Start from {citations} and keep any downstream change human-reviewed."
    )


def _derive_opportunity_confidence(
    *,
    opportunity_type: str,
    topic: ResearchTopicRecord,
    supporting_documents: list[ResearchDocumentRecord],
    council: ResearchCouncilPayload,
) -> float:
    base = 0.42 + 0.11 * len(supporting_documents) + 0.06 * (topic.topic_heat or 0.0)
    if opportunity_type in {"rule_gap", "trial_catalog_gap"}:
        base += 0.03
    elif opportunity_type in {"community_project", "external_tooling"}:
        base -= 0.02
    if council.stage_3.overall_confidence == "high":
        base += 0.12
    elif council.stage_3.overall_confidence == "medium":
        base += 0.06
    support_mentions = sum(
        1
        for opinion in council.stage_1
        if opportunity_type in opinion.proposed_opportunity_types
    ) + sum(
        1
        for ranking in council.stage_2
        if opportunity_type in ranking.ranked_opportunity_types
    )
    base += 0.03 * support_mentions
    if council.stage_3.overall_confidence == "low":
        base -= 0.05
    return round(min(0.99, max(0.35, base)), 4)


def _build_opportunity_action_payload(
    *,
    opportunity_id: str,
    digest: ResearchDigestRecord,
    opportunity_type: str,
    topic: ResearchTopicRecord,
    topic_label_map: dict[str, str],
    source_map: dict[str, ResearchSourceRecord],
    supporting_documents: list[ResearchDocumentRecord],
    council: ResearchCouncilPayload,
) -> ResearchOpportunityActionPayload:
    personas = _OPPORTUNITY_PERSONA_PRIORITY.get(opportunity_type, [])
    relevant_stage_1 = [item for item in council.stage_1 if item.persona in personas] or list(council.stage_1)
    open_questions = _unique_preserve_order(
        item
        for opinion in relevant_stage_1
        for item in opinion.open_questions
    )[:4]
    evidence_gaps = _unique_preserve_order(
        item
        for opinion in relevant_stage_1
        for item in opinion.evidence_gaps
    )[:4]
    if not open_questions:
        open_questions = list(council.stage_3.open_questions[:4])
    else:
        open_questions = _unique_preserve_order(open_questions + list(council.stage_3.open_questions))[:4]
    if not evidence_gaps:
        evidence_gaps = list(council.stage_3.evidence_gaps[:4])
    else:
        evidence_gaps = _unique_preserve_order(evidence_gaps + list(council.stage_3.evidence_gaps))[:4]

    evidence_bundle = [
        _build_opportunity_evidence(
            document=document,
            source_map=source_map,
            topic_label_map=topic_label_map,
            opportunity_type=opportunity_type,
        )
        for document in supporting_documents
    ]
    artifact_spec = ResearchOpportunityArtifactSpec(
        artifact_kind=_artifact_kind_for_opportunity(opportunity_type),
        title=_artifact_title_for_opportunity(opportunity_type=opportunity_type, topic_label=topic.label),
        summary=_artifact_summary_for_opportunity(opportunity_type=opportunity_type, topic_label=topic.label),
        suggested_path=_suggested_opportunity_path(opportunity_id, opportunity_type),
        target_hint=_default_promotion_target(opportunity_type),
    )
    theme_snapshot = _unique_preserve_order(
        [topic.label]
        + [item for opinion in relevant_stage_1 for item in opinion.primary_topics]
        + _top_graph_labels(supporting_documents, limit=3)
    )[:5]
    return ResearchOpportunityActionPayload(
        human_gate=True,
        digest_id=digest.digest_id,
        objective=_opportunity_objective(opportunity_type=opportunity_type, topic_label=topic.label),
        why_now=_opportunity_why_now(
            opportunity_type=opportunity_type,
            topic_label=topic.label,
            supporting_documents=supporting_documents,
            council=council,
        ),
        discovery_question=_opportunity_discovery_question(
            opportunity_type=opportunity_type,
            topic_label=topic.label,
            open_questions=open_questions,
        ),
        artifact_spec=artifact_spec,
        evidence_bundle=evidence_bundle,
        proposed_steps=_opportunity_proposed_steps(opportunity_type=opportunity_type, topic_label=topic.label),
        acceptance_gates=_acceptance_gates(opportunity_type),
        open_questions=open_questions,
        evidence_gaps=evidence_gaps,
        next_experiments=_opportunity_next_experiments(
            opportunity_type=opportunity_type,
            topic_label=topic.label,
            stage_3_experiments=council.stage_3.next_experiments,
        ),
        measurable_outcomes=_opportunity_measurable_outcomes(
            opportunity_type=opportunity_type,
            topic_label=topic.label,
        ),
        promotion_guardrails=list(council.stage_3.promotion_guardrails),
        suggested_target=_default_promotion_target(opportunity_type),
        council_confidence=council.stage_3.overall_confidence,
        council_personas=[item.persona for item in relevant_stage_1],
        theme_snapshot=theme_snapshot,
    )


def _artifact_kind_for_opportunity(opportunity_type: str) -> str:
    if opportunity_type == "rule_gap":
        return "rule_spec"
    if opportunity_type == "benchmark_gap":
        return "benchmark_spec"
    if opportunity_type == "trial_catalog_gap":
        return "trial_catalog_spec"
    if opportunity_type == "case_brief":
        return "case_brief_spec"
    if opportunity_type == "community_project":
        return "community_project_spec"
    return "external_tooling_spec"


def _artifact_title_for_opportunity(*, opportunity_type: str, topic_label: str) -> str:
    if opportunity_type == "rule_gap":
        return f"Explainable rule proposal for {topic_label.lower()}"
    if opportunity_type == "benchmark_gap":
        return f"Benchmark expansion spec for {topic_label.lower()}"
    if opportunity_type == "trial_catalog_gap":
        return f"Trial-catalog update spec for {topic_label.lower()}"
    if opportunity_type == "case_brief":
        return f"Case-brief enrichment spec for {topic_label.lower()}"
    if opportunity_type == "community_project":
        return f"Community project brief for {topic_label.lower()}"
    return f"External tooling brief for {topic_label.lower()}"


def _artifact_summary_for_opportunity(*, opportunity_type: str, topic_label: str) -> str:
    if opportunity_type == "rule_gap":
        return f"Translate cited {topic_label.lower()} findings into explainable rule coverage proposals and tests."
    if opportunity_type == "benchmark_gap":
        return f"Turn cited {topic_label.lower()} signals into reproducible benchmark additions and reviewer expectations."
    if opportunity_type == "trial_catalog_gap":
        return f"Capture trial and eligibility movement in {topic_label.lower()} without implying enrollment guidance."
    if opportunity_type == "case_brief":
        return f"Improve case-facing research briefs for {topic_label.lower()} with cited follow-up context."
    if opportunity_type == "community_project":
        return f"Shape a contributor-ready open-source build around {topic_label.lower()}."
    return f"Define reusable tooling that helps contributors work with {topic_label.lower()} evidence and artifacts."


def _suggested_opportunity_path(opportunity_id: str, opportunity_type: str) -> str:
    target = _default_promotion_target(opportunity_type)
    if target == "docs_draft":
        return f"docs/research-intel/{opportunity_id}.md"
    if target == "benchmark_task":
        return f"artifacts/research-intel/benchmark-tasks/{opportunity_id}.md"
    return f"artifacts/research-intel/github-issues/{opportunity_id}.md"


def _opportunity_objective(*, opportunity_type: str, topic_label: str) -> str:
    if opportunity_type == "rule_gap":
        return f"Propose explainable rule updates that better cover cited {topic_label.lower()} signals without weakening auditability."
    if opportunity_type == "benchmark_gap":
        return f"Add benchmark fixtures that capture wording, confounders, or follow-up patterns emerging in {topic_label.lower()}."
    if opportunity_type == "trial_catalog_gap":
        return f"Update the trial catalog so {topic_label.lower()} evidence is reflected in explainable matching traces."
    if opportunity_type == "case_brief":
        return f"Make case briefs more useful for reviewers dealing with {topic_label.lower()} by attaching current cited context."
    if opportunity_type == "community_project":
        return f"Create a contributor-scoped open-source project that makes {topic_label.lower()} discoveries reusable by the community."
    return f"Identify external or internal tooling that turns {topic_label.lower()} discovery into repeatable contributor workflows."


def _opportunity_why_now(
    *,
    opportunity_type: str,
    topic_label: str,
    supporting_documents: list[ResearchDocumentRecord],
    council: ResearchCouncilPayload,
) -> str:
    citations = ", ".join(item.citation_key for item in supporting_documents[:2]) or "the current digest corpus"
    if opportunity_type in {"rule_gap", "benchmark_gap"}:
        return (
            f"{topic_label} is active in the latest digest, and the council sees enough cited movement to justify a new "
            f"artifact instead of waiting for another manual synthesis. {citations} anchor the first pass."
        )
    if opportunity_type in {"trial_catalog_gap", "case_brief"}:
        return (
            f"The current digest ties {topic_label.lower()} to follow-up and trial implications, while council confidence is "
            f"{council.stage_3.overall_confidence}. {citations} should shape the next human-reviewed update."
        )
    return (
        f"Recent cited activity suggests {topic_label.lower()} is ready for contributor-facing research tooling work. "
        f"{citations} provide the first concrete evidence bundle."
    )


def _opportunity_discovery_question(
    *,
    opportunity_type: str,
    topic_label: str,
    open_questions: list[str],
) -> str:
    if open_questions:
        return open_questions[0]
    if opportunity_type == "benchmark_gap":
        return f"Which reproducible benchmark cases would best capture emerging {topic_label.lower()} language?"
    if opportunity_type == "trial_catalog_gap":
        return f"Which trial or cohort distinctions in {topic_label.lower()} should become explicit matching traces?"
    if opportunity_type == "rule_gap":
        return f"Which explainable rule boundary in {topic_label.lower()} is currently under-specified?"
    if opportunity_type == "case_brief":
        return f"What cited context would make {topic_label.lower()} case briefs more actionable for reviewers?"
    return f"What public artifact would make {topic_label.lower()} discoveries reusable by outside contributors?"


def _opportunity_proposed_steps(*, opportunity_type: str, topic_label: str) -> list[str]:
    if opportunity_type == "rule_gap":
        return [
            f"Compare existing rationale coverage against cited {topic_label.lower()} language and note misses.",
            "Draft explainable rule additions with evidence spans and expected rationale codes.",
            "Add targeted tests before any rule proposal is promoted.",
        ]
    if opportunity_type == "benchmark_gap":
        return [
            f"Draft synthetic or deidentified benchmark examples for {topic_label.lower()}.",
            "Document expected reviewer focus, rationale codes, and confounder handling.",
            "Link the spec to the cited digest evidence before promotion.",
        ]
    if opportunity_type == "trial_catalog_gap":
        return [
            f"Extract trial, cohort, and eligibility distinctions from cited {topic_label.lower()} sources.",
            "Turn those distinctions into explainable catalog or trace updates.",
            "Verify the proposal avoids enrollment or treatment guidance claims.",
        ]
    if opportunity_type == "case_brief":
        return [
            f"Map {topic_label.lower()} findings into case-brief language that stays separate from case scoring.",
            "Highlight the cited follow-up or surveillance implications reviewers may want to inspect.",
            "Validate the brief remains informational and human-reviewed.",
        ]
    if opportunity_type == "community_project":
        return [
            f"Define a contributor-scoped project brief centered on {topic_label.lower()}.",
            "Break the work into reusable dataset, manifest, or evaluation pieces.",
            "Promote only after the deliverable can be audited and cited publicly.",
        ]
    return [
        f"List the tooling friction currently blocking reuse of {topic_label.lower()} discovery output.",
        "Define the smallest contributor-ready integration or helper that would remove that friction.",
        "Promote only once the proposal maps cleanly to a reproducible public artifact.",
    ]


def _opportunity_next_experiments(
    *,
    opportunity_type: str,
    topic_label: str,
    stage_3_experiments: list[str],
) -> list[str]:
    extras: list[str] = []
    if opportunity_type == "benchmark_gap":
        extras.append(f"Measure whether new {topic_label.lower()} fixtures change benchmark coverage or reviewer-yield simulation.")
    elif opportunity_type == "rule_gap":
        extras.append(f"Stress-test proposed {topic_label.lower()} rule changes against known confounders and negation cases.")
    elif opportunity_type == "trial_catalog_gap":
        extras.append(f"Check whether cited {topic_label.lower()} distinctions improve trial trace clarity without overmatching.")
    elif opportunity_type == "case_brief":
        extras.append(f"Compare generated {topic_label.lower()} briefs across cases with different rationale mixes.")
    else:
        extras.append(f"Test whether the proposed {topic_label.lower()} artifact is reusable by outside contributors without extra context.")
    return _unique_preserve_order(extras + list(stage_3_experiments))[:4]


def _opportunity_measurable_outcomes(*, opportunity_type: str, topic_label: str) -> list[str]:
    if opportunity_type == "rule_gap":
        return [
            f"A cited rule proposal exists for {topic_label.lower()} with tests covering expected rationale behavior.",
            "Any score or explanation impact is measurable in benchmark output before merge.",
        ]
    if opportunity_type == "benchmark_gap":
        return [
            f"At least one new benchmark spec exists for {topic_label.lower()} with documented expected rationale codes.",
            "The proposal can be evaluated in a reproducible benchmark run.",
        ]
    if opportunity_type == "trial_catalog_gap":
        return [
            f"A cited trial-catalog proposal exists for {topic_label.lower()} with traceable eligibility distinctions.",
            "The proposal stays informational and explainable in downstream match output.",
        ]
    if opportunity_type == "case_brief":
        return [
            f"A reviewer-facing brief template for {topic_label.lower()} is generated without mutating case scores.",
            "The brief cites its supporting digest documents and open questions.",
        ]
    if opportunity_type == "community_project":
        return [
            f"A contributor-ready project brief exists for {topic_label.lower()} with a bounded write scope.",
            "The project maps to a public artifact and acceptance criteria, not just a summary.",
        ]
    return [
        f"A tooling brief exists for {topic_label.lower()} with a concrete integration boundary and cited need.",
        "The proposal can be promoted into an issue or spec without relying on hidden context.",
    ]


def _build_opportunity_evidence(
    *,
    document: ResearchDocumentRecord,
    source_map: dict[str, ResearchSourceRecord],
    topic_label_map: dict[str, str],
    opportunity_type: str,
) -> ResearchOpportunityEvidence:
    source = source_map.get(document.source_id)
    return ResearchOpportunityEvidence(
        document_id=document.document_id,
        citation_key=document.citation_key,
        title=document.title,
        source_kind=source.source_kind if source else None,
        topic_labels=[topic_label_map[item] for item in document.topic_ids or [] if item in topic_label_map],
        why_it_matters=_opportunity_evidence_reason(opportunity_type=opportunity_type, document=document),
    )


def _opportunity_evidence_reason(*, opportunity_type: str, document: ResearchDocumentRecord) -> str:
    evidence_tags = ", ".join((document.entity_tags or [])[:3])
    if opportunity_type == "rule_gap":
        return (
            f"This document contributes follow-up or confounder language that may require clearer rule handling. "
            f"Signals: {evidence_tags or 'topic-linked evidence'}."
        )
    if opportunity_type == "benchmark_gap":
        return (
            f"This document adds benchmarkable wording or workflow context that could become a reproducible fixture. "
            f"Signals: {evidence_tags or 'topic-linked evidence'}."
        )
    if opportunity_type == "trial_catalog_gap":
        return (
            f"This document may sharpen explainable trial traces or cohort distinctions. "
            f"Signals: {evidence_tags or 'topic-linked evidence'}."
        )
    if opportunity_type == "case_brief":
        return (
            f"This document provides cited context that could make reviewer-facing briefs more informative. "
            f"Signals: {evidence_tags or 'topic-linked evidence'}."
        )
    if opportunity_type == "community_project":
        return (
            f"This document suggests a reusable open-source build or dataset need. "
            f"Signals: {evidence_tags or 'topic-linked evidence'}."
        )
    return (
        f"This document points to tooling or integration work that could make research output easier to reuse. "
        f"Signals: {evidence_tags or 'topic-linked evidence'}."
    )


def _evaluate_opportunity_experiment(
    *,
    row: ResearchOpportunityRecord,
    action_payload: ResearchOpportunityActionPayload,
    run_id: int,
) -> ResearchOpportunityExperimentResult:
    experiment_kind = _experiment_kind_for_opportunity(row.opportunity_type)
    evidence_count = len(action_payload.evidence_bundle)
    measurable_count = len(action_payload.measurable_outcomes)
    step_count = len(action_payload.proposed_steps)
    gate_count = len(action_payload.acceptance_gates)
    open_question_count = len(action_payload.open_questions)
    theme_count = len(action_payload.theme_snapshot)
    rationale_count = len(row.related_rationale_codes or [])
    council_bonus = _council_confidence_bonus(action_payload.council_confidence)

    if experiment_kind == "benchmark_readiness":
        metric_name = "benchmark_readiness_score"
        threshold = 0.74
        min_delta = 0.05
        evidence_coverage_score = round(
            min(
                1.0,
                0.30
                + 0.16 * min(3, evidence_count)
                + 0.05 * min(3, theme_count)
                + 0.04 * min(2, measurable_count)
                - 0.04 * max(0, open_question_count - 2),
            ),
            4,
        )
        heuristic_baseline = round(
            min(
                0.88,
                0.42
                + 0.06 * min(3, evidence_count)
                + 0.05 * min(2, theme_count),
            ),
            4,
        )
        candidate_value = round(
            min(
                0.99,
                0.48
                + 0.08 * min(3, evidence_count)
                + 0.05 * min(3, measurable_count)
                + 0.04 * min(3, step_count)
                + 0.03 * min(3, gate_count)
                + (0.07 if action_payload.artifact_spec.artifact_kind == "benchmark_spec" else 0.0)
                + council_bonus
                + 0.05 * evidence_coverage_score
                - 0.03 * max(0, open_question_count - 2),
            ),
            4,
        )
    else:
        metric_name = "rule_explainability_score"
        threshold = 0.76
        min_delta = 0.04
        evidence_coverage_score = round(
            min(
                1.0,
                0.28
                + 0.14 * min(3, evidence_count)
                + 0.08 * min(3, rationale_count)
                + 0.04 * min(3, gate_count)
                - 0.04 * max(0, open_question_count - 1),
            ),
            4,
        )
        heuristic_baseline = round(
            min(
                0.86,
                0.40
                + 0.05 * min(3, evidence_count)
                + 0.07 * min(3, rationale_count),
            ),
            4,
        )
        candidate_value = round(
            min(
                0.99,
                0.46
                + 0.07 * min(3, evidence_count)
                + 0.07 * min(3, rationale_count)
                + 0.05 * min(3, measurable_count)
                + 0.04 * min(3, gate_count)
                + 0.04 * min(3, step_count)
                + (0.07 if action_payload.artifact_spec.artifact_kind == "rule_spec" else 0.0)
                + council_bonus
                + 0.04 * evidence_coverage_score
                - 0.03 * max(0, open_question_count - 1),
            ),
            4,
        )

    previous = action_payload.last_experiment
    baseline_value = (
        previous.candidate_value
        if previous is not None
        and previous.supported
        and previous.experiment_kind == experiment_kind
        and previous.candidate_value is not None
        else heuristic_baseline
    )
    delta = round(candidate_value - (baseline_value or 0.0), 4)
    ratchet_outcome = (
        "keep"
        if candidate_value >= threshold and delta >= min_delta and evidence_coverage_score >= 0.60
        else "discard"
    )
    notes = _experiment_notes(
        ratchet_outcome=ratchet_outcome,
        experiment_kind=experiment_kind,
        baseline_value=baseline_value,
        candidate_value=candidate_value,
        evidence_coverage_score=evidence_coverage_score,
        threshold=threshold,
        min_delta=min_delta,
        action_payload=action_payload,
    )
    return ResearchOpportunityExperimentResult(
        supported=True,
        experiment_kind=experiment_kind,
        ratchet_outcome=ratchet_outcome,
        metric_name=metric_name,
        baseline_value=baseline_value,
        candidate_value=candidate_value,
        delta=delta,
        threshold=threshold,
        min_delta=min_delta,
        evidence_coverage_score=evidence_coverage_score,
        notes=notes,
        run_id=run_id,
    )


def _experiment_kind_for_opportunity(opportunity_type: str) -> str:
    if opportunity_type == "benchmark_gap":
        return "benchmark_readiness"
    return "rule_explainability"


def _council_confidence_bonus(confidence: str) -> float:
    if confidence == "high":
        return 0.08
    if confidence == "medium":
        return 0.04
    return 0.0


def _experiment_notes(
    *,
    ratchet_outcome: str,
    experiment_kind: str,
    baseline_value: float,
    candidate_value: float,
    evidence_coverage_score: float,
    threshold: float,
    min_delta: float,
    action_payload: ResearchOpportunityActionPayload,
) -> list[str]:
    notes = [
        (
            f"{experiment_kind.replace('_', ' ')} candidate scored {candidate_value:.2f} against "
            f"threshold {threshold:.2f} with evidence coverage {evidence_coverage_score:.2f}."
        )
    ]
    if baseline_value:
        notes.append(f"Baseline reference was {baseline_value:.2f}; ratchet delta target is {min_delta:.2f}.")
    if ratchet_outcome == "keep":
        notes.append("Proposal cleared the ratchet and is safe to keep as a contributor-ready experimental candidate.")
    else:
        notes.append("Proposal did not clear the ratchet yet; keep it human-gated until evidence or measurable outcomes improve.")
    if action_payload.open_questions:
        notes.append(f"Outstanding open questions: {len(action_payload.open_questions)}.")
    if action_payload.evidence_gaps:
        notes.append(f"Outstanding evidence gaps: {len(action_payload.evidence_gaps)}.")
    return notes


def _acceptance_gates(opportunity_type: str) -> list[str]:
    if opportunity_type == "rule_gap":
        return [
            "Rule change must preserve explainability and add tests.",
            "Any benchmark movement must be explicit and reviewable.",
        ]
    if opportunity_type == "benchmark_gap":
        return [
            "New cases must be deidentified or synthetic.",
            "Reviewer focus and expected rationale codes must be documented.",
        ]
    if opportunity_type == "trial_catalog_gap":
        return [
            "Trial criteria must stay explainable and cite the motivating digest items.",
            "Do not imply enrollment guidance.",
        ]
    return [
        "Publish only cited claims.",
        "Keep promotion human-gated and audit-visible.",
    ]


def _default_promotion_target(opportunity_type: str) -> ResearchPromotionTarget:
    if opportunity_type in {"rule_gap", "trial_catalog_gap"}:
        return "docs_draft"
    if opportunity_type == "benchmark_gap":
        return "benchmark_task"
    return "github_issue"


def _write_run_artifacts(
    *,
    artifact_root: Path,
    basename: str,
    payload: dict[str, Any],
    markdown_lines: list[str],
) -> list[str]:
    artifact_root.mkdir(parents=True, exist_ok=True)
    json_path = artifact_root / f"{basename}.json"
    markdown_path = artifact_root / f"{basename}.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")
    return [
        str(json_path.relative_to(_repo_root())),
        str(markdown_path.relative_to(_repo_root())),
    ]


def _write_opportunity_promotion_artifact(
    row: ResearchOpportunityRecord,
    *,
    target: ResearchPromotionTarget,
) -> str:
    artifact_root = _artifact_root() / "promotions"
    artifact_root.mkdir(parents=True, exist_ok=True)
    path = artifact_root / f"{row.opportunity_id}-{target}.md"
    lines = [
        f"# {row.title}",
        "",
        f"- opportunity id: `{row.opportunity_id}`",
        f"- type: `{row.opportunity_type}`",
        f"- target: `{target}`",
        f"- confidence: `{row.confidence_score:.2f}`",
        "",
        row.summary,
    ]
    action_payload = ResearchOpportunityActionPayload.model_validate(row.action_payload or {})
    if action_payload.objective:
        lines.extend(["", "## Objective", action_payload.objective])
    if action_payload.why_now:
        lines.extend(["", "## Why now", action_payload.why_now])
    if action_payload.discovery_question:
        lines.extend(["", "## Discovery question", action_payload.discovery_question])
    if action_payload.proposed_steps:
        lines.extend(["", "## Proposed steps"])
        for step in action_payload.proposed_steps:
            lines.append(f"- {step}")
    lines.extend(["", "## Acceptance gates"])
    for gate in action_payload.acceptance_gates or _acceptance_gates(row.opportunity_type):
        lines.append(f"- {gate}")
    if action_payload.evidence_bundle:
        lines.extend(["", "## Evidence bundle"])
        for item in action_payload.evidence_bundle:
            lines.append(f"- {item.citation_key}: {item.title}")
            lines.append(f"  - why it matters: {item.why_it_matters}")
    if action_payload.open_questions:
        lines.extend(["", "## Open questions"])
        for item in action_payload.open_questions:
            lines.append(f"- {item}")
    if action_payload.measurable_outcomes:
        lines.extend(["", "## Measurable outcomes"])
        for item in action_payload.measurable_outcomes:
            lines.append(f"- {item}")
    if action_payload.promotion_guardrails:
        lines.extend(["", "## Promotion guardrails"])
        for item in action_payload.promotion_guardrails:
            lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Supporting topics",
            *(f"- {topic_id}" for topic_id in row.topic_ids or []),
            "",
            "## Supporting documents",
            *(f"- {document_id}" for document_id in row.supporting_document_ids or []),
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path.relative_to(_repo_root()))


def _write_opportunity_action_artifacts(
    *,
    row: ResearchOpportunityRecord,
    topic_label_map: dict[str, str],
) -> list[str]:
    artifact_root = _artifact_root() / "opportunities"
    artifact_root.mkdir(parents=True, exist_ok=True)
    response = _build_opportunity_response(row, topic_label_map)
    json_path = artifact_root / f"{row.opportunity_id}.json"
    markdown_path = artifact_root / f"{row.opportunity_id}.md"
    json_path.write_text(response.model_dump_json(indent=2), encoding="utf-8")

    action_payload = response.action_payload
    lines = [
        f"# {response.title}",
        "",
        f"- opportunity id: `{response.opportunity_id}`",
        f"- type: `{response.opportunity_type}`",
        f"- status: `{response.status}`",
        f"- confidence: `{response.confidence_score:.2f}`",
        f"- council confidence: `{action_payload.council_confidence}`",
        "",
        response.summary,
    ]
    if action_payload.objective:
        lines.extend(["", "## Objective", action_payload.objective])
    if action_payload.why_now:
        lines.extend(["", "## Why now", action_payload.why_now])
    if action_payload.discovery_question:
        lines.extend(["", "## Discovery question", action_payload.discovery_question])
    if action_payload.theme_snapshot:
        lines.extend(["", "## Theme snapshot"])
        for item in action_payload.theme_snapshot:
            lines.append(f"- {item}")
    if action_payload.evidence_bundle:
        lines.extend(["", "## Evidence bundle"])
        for item in action_payload.evidence_bundle:
            lines.append(f"- {item.citation_key}: {item.title}")
            if item.topic_labels:
                lines.append(f"  - topics: {', '.join(item.topic_labels)}")
            if item.source_kind:
                lines.append(f"  - source kind: {item.source_kind}")
            lines.append(f"  - why it matters: {item.why_it_matters}")
    if action_payload.proposed_steps:
        lines.extend(["", "## Proposed steps"])
        for item in action_payload.proposed_steps:
            lines.append(f"- {item}")
    if action_payload.measurable_outcomes:
        lines.extend(["", "## Measurable outcomes"])
        for item in action_payload.measurable_outcomes:
            lines.append(f"- {item}")
    if action_payload.acceptance_gates:
        lines.extend(["", "## Acceptance gates"])
        for item in action_payload.acceptance_gates:
            lines.append(f"- {item}")
    if action_payload.open_questions:
        lines.extend(["", "## Open questions"])
        for item in action_payload.open_questions:
            lines.append(f"- {item}")
    if action_payload.evidence_gaps:
        lines.extend(["", "## Evidence gaps"])
        for item in action_payload.evidence_gaps:
            lines.append(f"- {item}")
    if action_payload.next_experiments:
        lines.extend(["", "## Next experiments"])
        for item in action_payload.next_experiments:
            lines.append(f"- {item}")
    if action_payload.promotion_guardrails:
        lines.extend(["", "## Promotion guardrails"])
        for item in action_payload.promotion_guardrails:
            lines.append(f"- {item}")
    if action_payload.artifact_spec.title:
        lines.extend(
            [
                "",
                "## Suggested downstream artifact",
                f"- kind: `{action_payload.artifact_spec.artifact_kind}`",
                f"- title: {action_payload.artifact_spec.title}",
                f"- target hint: `{action_payload.artifact_spec.target_hint or 'n/a'}`",
            ]
        )
        if action_payload.artifact_spec.suggested_path:
            lines.append(f"- suggested path: `{action_payload.artifact_spec.suggested_path}`")
        if action_payload.artifact_spec.summary:
            lines.append(f"- summary: {action_payload.artifact_spec.summary}")

    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [
        str(json_path.relative_to(_repo_root())),
        str(markdown_path.relative_to(_repo_root())),
    ]


def _write_opportunity_experiment_artifacts(
    *,
    row: ResearchOpportunityRecord,
    action_payload: ResearchOpportunityActionPayload,
    experiment: ResearchOpportunityExperimentResult,
    topic_label_map: dict[str, str],
) -> list[str]:
    artifact_root = _artifact_root() / "experiments"
    artifact_root.mkdir(parents=True, exist_ok=True)
    basename = f"{row.opportunity_id}-run-{experiment.run_id}"
    json_path = artifact_root / f"{basename}.json"
    markdown_path = artifact_root / f"{basename}.md"
    payload = {
        "opportunity_id": row.opportunity_id,
        "opportunity_type": row.opportunity_type,
        "topic_labels": [topic_label_map[item] for item in row.topic_ids or [] if item in topic_label_map],
        "summary": row.summary,
        "experiment": experiment.model_dump(mode="json"),
        "artifact_spec": action_payload.artifact_spec.model_dump(mode="json"),
        "objective": action_payload.objective,
        "why_now": action_payload.why_now,
        "discovery_question": action_payload.discovery_question,
        "open_questions": list(action_payload.open_questions),
        "evidence_gaps": list(action_payload.evidence_gaps),
        "measurable_outcomes": list(action_payload.measurable_outcomes),
        "acceptance_gates": list(action_payload.acceptance_gates),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        f"# Experiment for {row.title}",
        "",
        f"- opportunity id: `{row.opportunity_id}`",
        f"- type: `{row.opportunity_type}`",
        f"- experiment kind: `{experiment.experiment_kind}`",
        f"- ratchet outcome: `{experiment.ratchet_outcome}`",
        f"- metric: `{experiment.metric_name}`",
        "",
        "## Scores",
        f"- baseline: {experiment.baseline_value:.2f}" if experiment.baseline_value is not None else "- baseline: n/a",
        f"- candidate: {experiment.candidate_value:.2f}" if experiment.candidate_value is not None else "- candidate: n/a",
        f"- delta: {experiment.delta:.2f}" if experiment.delta is not None else "- delta: n/a",
        f"- threshold: {experiment.threshold:.2f}" if experiment.threshold is not None else "- threshold: n/a",
        f"- min delta: {experiment.min_delta:.2f}" if experiment.min_delta is not None else "- min delta: n/a",
        (
            f"- evidence coverage: {experiment.evidence_coverage_score:.2f}"
            if experiment.evidence_coverage_score is not None
            else "- evidence coverage: n/a"
        ),
    ]
    if action_payload.objective:
        lines.extend(["", "## Objective", action_payload.objective])
    if action_payload.discovery_question:
        lines.extend(["", "## Discovery question", action_payload.discovery_question])
    if experiment.notes:
        lines.extend(["", "## Notes"])
        for item in experiment.notes:
            lines.append(f"- {item}")
    if action_payload.measurable_outcomes:
        lines.extend(["", "## Measurable outcomes"])
        for item in action_payload.measurable_outcomes:
            lines.append(f"- {item}")
    if action_payload.acceptance_gates:
        lines.extend(["", "## Acceptance gates"])
        for item in action_payload.acceptance_gates:
            lines.append(f"- {item}")
    if action_payload.evidence_bundle:
        lines.extend(["", "## Evidence bundle"])
        for item in action_payload.evidence_bundle:
            lines.append(f"- {item.citation_key}: {item.title}")
            lines.append(f"  - why it matters: {item.why_it_matters}")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [
        str(json_path.relative_to(_repo_root())),
        str(markdown_path.relative_to(_repo_root())),
    ]


def _build_opportunity_response(
    row: ResearchOpportunityRecord,
    topic_label_map: dict[str, str],
) -> ResearchOpportunity:
    return ResearchOpportunity(
        opportunity_id=row.opportunity_id,
        opportunity_type=row.opportunity_type,  # type: ignore[arg-type]
        title=row.title,
        summary=row.summary,
        status=row.status,
        confidence_score=row.confidence_score,
        topic_ids=row.topic_ids or [],
        topic_labels=[topic_label_map[item] for item in row.topic_ids or [] if item in topic_label_map],
        supporting_document_ids=row.supporting_document_ids or [],
        related_rationale_codes=row.related_rationale_codes or [],
        related_trial_ids=row.related_trial_ids or [],
        action_payload=ResearchOpportunityActionPayload.model_validate(row.action_payload or {}),
        promotion_target=row.promotion_target,
        promoted_at=row.promoted_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _build_digest_document_ref(
    document: ResearchDocumentRecord,
    *,
    topic_label_map: dict[str, str],
) -> ResearchDigestDocumentRef:
    return ResearchDigestDocumentRef(
        document_id=document.document_id,
        title=document.title,
        citation_key=document.citation_key,
        url=document.url,
        topic_labels=[topic_label_map[item] for item in document.topic_ids or [] if item in topic_label_map],
    )
