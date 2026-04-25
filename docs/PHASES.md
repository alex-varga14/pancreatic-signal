# Phase status and next slices

This repository has already completed the early foundation and MVP-oriented phases. Late Phase 6 hosted smoke evidence
capture and pilot closeout are now complete, and the codebase now also carries the research-first repositioning work that
makes pancreatic oncology discovery the lead product narrative. The next work should deepen the live discovery system rather
than drift back toward initial product construction.

## Completed phases

### Phase 0 — Repository foundation

Completed outcomes:

- bootable API and web app
- demo data and local developer workflow
- baseline docs, packaging, and validation commands

### Phase 1 — Deterministic triage baseline

Completed outcomes:

- transparent rule-based pancreatic triage
- rationale codes and evidence spans
- bounded scoring and urgency output
- batch and direct report ingestion

### Phase 2 — Reviewer workflow

Completed outcomes:

- persisted cases, reports, findings, and review actions
- worklist filters and case detail pages
- reviewer assignment, notes, escalation, dismissal, and status tracking

### Phase 3 — Evaluation and benchmark surfaces

Completed outcomes:

- demo evaluation scripts and threshold sweeps
- benchmark proof artifacts in `docs/examples/`
- external benchmark bundle generation and submission validation

### Phase 4 — Trial matching extension

Completed outcomes:

- explainable pancreatic abstraction fields
- rule-based PDAC trial matching
- case-detail trial candidate display and API support

### Phase 5 — Hybrid prioritization upgrade

Completed outcomes:

- hybrid scoring and calibrated ranking surfaces
- confidence and review-priority outputs
- reviewer feedback capture and recommendation scaffolding

## Completed current phase

### Phase 6 — Interoperability, pilot auth, deployment hardening, and research-first repositioning

Already completed in this phase:

- trusted-proxy and header-auth pilot modes
- site-scoped access and import behavior
- de-identified research views
- FHIR ingestion
- HL7 ORU ingestion
- structured import metadata persistence
- repo-side Phase 6C interoperability hardening for structured FHIR narratives, identifier fallbacks, and import-run audit visibility
- persisted import-run audit records
- pilot Docker overlays and smoke coverage
- hosted GitHub smoke coverage for the narrower supported matrix
- hosted GitHub FHIR confirmation recorded on 2026-03-25 in run `#23563902873`
- hosted GitHub HL7 trial recorded on 2026-03-25 in run `#23564057337`
- an explicit decision to keep HL7 manual-only in the default hosted matrix to control recurring runtime and maintenance cost
- repo-side Phase 6D release-facing polish across quickstart, deployment, release-readiness, and handoff docs
- homepage, about, README, and research-intel docs now frame the project as a pancreatic oncology discovery system first
- explainable triage, benchmark proof, imports, and case briefs are now documented as downstream surfaces of the discovery engine

## Current next slices

### Post-Phase-6 research-first follow-through

Goal:

- deepen the live discovery system, contributor workflows, and research artifacts while preserving the reviewer-facing proof shape and explainability boundaries

### Research Intelligence track

Implemented outcomes:

- a sibling `/research-intel` workspace and `/api/v1/research-intel/*` namespace
- seeded source, topic, graph, and document catalogs under `data/research/`
- persisted research-intel sources, runs, documents, evidence, topics, digests, and opportunities
- manual ingest and digest scripts plus validation coverage
- case-level research briefs that inform review without changing scores
- research-intel is now the lead product narrative across landing and onboarding surfaces
- research-intel now also exposes watchtower scheduling, due-only ingest, and a dedicated schedule workspace
- research-intel now also carries broader graph families and stronger relation-aware entity resolution across biomarkers, therapies, cohorts, modalities, and datasets
- research-intel now compares digests across runs with recurring open-question and disagreement tracking
- opportunities now carry contributor packets for issue-ready, benchmark-ready, dataset-ready, rule, trial, case-brief, and tooling follow-through
- research-intel experiments now include richer benchmark and rule stress-test modes with dimension-level scoring
- governance for paid-source access and donation-funded operations is now documented without introducing autonomous spending
- the live watchtower now covers `8` live-ready sources, including official NCI and FDA feeds plus GitHub-backed open-source discovery with pancreas-aware filtering
- the watchtower can now run as one audited automation tick through API, CLI, Make, and a hosted GitHub Actions workflow with digest gating
- digests now also include longer-horizon calibration snapshots, and benchmark or dataset packets now emit collaborator bundle artifacts

Next slices:

1. exercise the new collaborator bundles against larger collaborator benchmark and dataset drops
2. deepen graph and topic quality against a larger live corpus
3. keep governance and procurement notes current before any paid-source expansion is activated
4. continue broadening trusted live connector coverage where the watchtower still leans on fixtures
5. deepen proof and cross-pack comparison once larger external bundles start landing

### Phase 7 — Audit fixes and autoresearch lab subsystem (v2.0)

Completed outcomes:

- sentence-bounded negation in the triage engine (no more 60-char regex windows leaking across sentences)
- structured `FindingRecord` rows persisted by the triage engine, not just flattened evidence
- additive scoring externalized into a `scoring` block in `data/ontologies/pancreatic_signal_rules.json` (new `OntologyConfig` schema, `extra="forbid"`)
- store implementation moved to `apps/api/app/store/case_store.py` with a thin re-export shim at `memory_store.py`
- `docs/API_SPEC.md` updated to reflect CSV/JSON/JSONL imports and label `/settings/rules` as future
- Playwright e2e smoke under `apps/web/tests/e2e/` for `/proof`, `/cases`, case detail review, and `/imports`, wired into `make web-e2e` and CI
- opt-in autoresearch lab subsystem inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch):
  - `autoresearch/program.md` (research org instructions)
  - frozen `autoresearch/baseline/pancreatic_signal_rules.json`
  - `scripts/run_autoresearch_experiment.py` (single-experiment driver: schema validation, demo eval, external snapshot lookup, determinism check, guardrails)
  - `scripts/run_autoresearch_loop.py` (orchestrator with pluggable agent CLI)
  - append-only `autoresearch/runs/` log
  - `make autoresearch-once / loop / promote / rollback`
  - read-only API at `/api/v1/autoresearch/*` with admin-gated promotion
  - `/autoresearch` web surface with run history, leaderboard, diff/eval viewer, and capability-gated promote action

## What is not a current phase target

The repo is not currently prioritizing:

- PACS-native image inference
- autonomous diagnosis or treatment logic
- opaque model-only triage replacements
- broad hospital production deployment claims
- agent editing of Python source (deferred to v2.2; see `docs/AUTORESEARCH.md`)
- hosted continuous autoresearch in CI (the loop is run by humans, locally or overnight on a workstation)

## Phase 6 exit view

Phase 6 is in a good state when:

- the hosted/manual smoke boundary is intentionally documented and verified
- the structured import paths behave consistently across report, FHIR, and HL7 inputs
- pilot auth modes remain documented, tested, and auditable
- release-facing docs match the actual product state
- new contributors understand the product as an open pancreatic oncology discovery system first
