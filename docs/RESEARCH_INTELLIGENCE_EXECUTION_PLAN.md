# Research Intelligence Execution Plan

This document is the operating contract for the next six research-intel phases. It is meant to keep implementation, runs, artifacts, and accumulated context aligned as the project shifts toward auto research and scientific discovery.

## How To Use This Plan

Treat this as the companion to [RESEARCH_INTELLIGENCE.md](./RESEARCH_INTELLIGENCE.md).

- `RESEARCH_INTELLIGENCE.md` explains what the subsystem is.
- This document explains how we execute and document it over time.
- `CODEX_HANDOFF.md` records milestone state once a phase materially lands.
- `artifacts/research-intel/` stores per-run outputs that should back future decisions.

## Documentation Stack

These files should stay in sync as work advances:

1. `README.md`
   Use for top-level product framing and contributor entry points.
2. `docs/RESEARCH_INTELLIGENCE.md`
   Use for user-facing capability overview, boundaries, and local workflow.
3. `docs/RESEARCH_INTELLIGENCE_EXECUTION_PLAN.md`
   Use for phased execution, run discipline, and context-building rules.
4. `docs/API_SPEC.md`
   Update whenever request or response shapes change.
5. `docs/ARCHITECTURE.md`
   Update whenever ingestion, scheduling, storage, or agent flow changes.
6. `docs/DATA_MODEL.md`
   Update whenever persisted entities, metadata contracts, or artifact schema change.
7. `docs/CODEX_HANDOFF.md`
   Update at the end of meaningful phase slices so the next operator inherits real state instead of assumptions.

## Run Contract

Every research-intel run should leave behind enough durable context that future runs can build on it safely.

Required for ingest runs:

- requested mode and effective mode
- source scope
- per-source health outcome
- connector used
- document counts
- provenance for fetched documents
- novelty signals for newly seen documents

Required for digest or council runs:

- supporting document set
- ranked topics
- disagreement state
- recommended next actions
- citations that justify those actions

Required for promotion or action runs:

- what was promoted
- why it crossed the threshold
- where it was promoted to
- what human gate was applied

## Context-Building Rules

When a phase advances, update context in this order:

1. write the artifacts under `artifacts/research-intel/`
2. update API, data-model, and architecture docs if contracts changed
3. update `RESEARCH_INTELLIGENCE.md` if user-facing behavior changed
4. update `CODEX_HANDOFF.md` if the new slice materially changes what the next operator should do

Do not let context drift by relying on:

- chat history alone
- transient run logs
- undocumented connector behavior
- implied milestone completion without artifacts or tests

## Phase Map

### Phase 1. Live Discovery Ingest

Goal:
- move from seeded-only ingestion to a discovery-oriented collector with fixture-backed reproducibility and opt-in live connector support

Required outputs:
- connector registry and source-health behavior
- per-document provenance
- novelty scoring
- reproducible fixture ingestion path for validation

Acceptance gate:
- ingest can run in reproducible offline mode
- source health is visible
- provenance and novelty are persisted and exposed

### Phase 2. Scientific Knowledge Graph

Goal:
- turn keyword buckets into richer pancreatic oncology entities and relationships

Required outputs:
- expanded graph schema
- entity-resolution rules
- clearer mapping from papers to biomarkers, therapies, cohorts, and trial concepts

Acceptance gate:
- graph-backed tags are stable enough to support cross-document reasoning and clustering

Current progress:
- typed graph nodes and edges are now implemented
- graph-backed entity resolution is part of ingest normalization
- graph activity is exposed through a dedicated research-intel graph surface

### Phase 3. Multi-Agent Research Council

Goal:
- move from deterministic council scaffolding to a stronger deliberation system that captures competing interpretations and open questions

Required outputs:
- independent opinions
- peer critique
- synthesis with confidence and disagreement handling
- explicit question backlog where evidence is insufficient

Acceptance gate:
- council outputs are durable, comparable across runs, and citation-backed

Current progress:
- stage 1 now persists primary topics, key claims, confidence labels, open questions, and evidence gaps
- stage 2 now persists peer critique, challenge targets, preferred actions, and confidence adjustments
- stage 3 now persists overall confidence, open questions, evidence gaps, next experiments, and promotion guardrails
- legacy council payloads remain readable so future runs can compare new and old digests safely

### Phase 4. Discovery-to-Action Engine

Goal:
- transform research findings into concrete OSS and product work

Required outputs:
- benchmark proposals
- rule proposals
- trial-catalog proposals
- community-tool or dataset proposals

Acceptance gate:
- promoted opportunities can be traced back to cited evidence and clear downstream actions

Current progress:
- opportunities now store typed action specs with objective, why-now rationale, discovery question, measurable outcomes, and artifact hints
- digest runs now emit opportunity JSON and Markdown artifacts alongside digest artifacts
- promotion artifacts now preserve cited evidence bundles, open questions, and measurable outcomes for downstream contributors

### Phase 5. Safe Scientific Experimentation

Goal:
- add sandboxed experimentation around discovery outputs without allowing uncontrolled automation

Required outputs:
- experiment definitions
- keep or discard criteria
- reproducible benchmark and rule stress tests

Acceptance gate:
- no proposal is accepted without an explicit metric or ratchet outcome

### Phase 6. Research-First Repositioning

Goal:
- make Research Intelligence the primary product narrative while triage becomes one applied downstream surface

Required outputs:
- updated product framing
- contributor workflow centered on discovery and open research tooling
- docs and roadmap that reflect the scientific-discovery mission

Acceptance gate:
- new contributors understand the product as an open pancreatic oncology research-and-discovery system first

## Phase Review Checklist

Before a phase is considered complete, confirm:

- code exists
- tests exist
- validation covers the slice
- docs explain the slice
- artifacts show the slice working
- handoff notes tell the next operator what remains

## Immediate Next Slice

The current next step is Phase 1:

- discovery ingest with fixture-backed connectors for reproducible validation
- opt-in live connector support where the contract is stable enough to implement safely
- visible source health, provenance, and novelty to support future scientific-discovery work
