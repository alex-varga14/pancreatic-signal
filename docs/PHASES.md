# Phase status and next slices

This repository has already completed the early foundation and MVP-oriented phases. The current work is late Phase 6 interoperability and pilot hardening, not initial product construction.

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

## Active phase

### Phase 6 — Interoperability, pilot auth, and deployment hardening

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

## Current next slices

### Phase 6A — Hosted FHIR smoke confirmation

Goal:

- record the first green GitHub-hosted attachment-backed FHIR smoke run using the current `Pilot Smoke` workflow

### Phase 6B — HL7 hosting decision

Goal:

- decide whether HL7 success-path smoke should join the hosted matrix or remain operator-triggered based on reliability and maintenance cost

### Phase 6D — Release-facing polish

Goal:

- keep deployment, readiness, benchmark, and handoff docs aligned with the shipping implementation so contributors and operators can work without private context

## What is not a current phase target

The repo is not currently prioritizing:

- PACS-native image inference
- autonomous diagnosis or treatment logic
- opaque model-only triage replacements
- broad hospital production deployment claims

## Phase 6 exit view

Phase 6 is in a good state when:

- the hosted/manual smoke boundary is intentionally documented and verified
- the structured import paths behave consistently across report, FHIR, and HL7 inputs
- pilot auth modes remain documented, tested, and auditable
- release-facing docs match the actual product state
