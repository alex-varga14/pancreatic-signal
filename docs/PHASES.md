# Phase status and next slices

This repository has already completed the early foundation and MVP-oriented phases. Late Phase 6 hosted smoke evidence capture and pilot closeout are now complete, so the next work should move beyond smoke-baseline capture rather than back toward initial product construction.

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
- hosted GitHub FHIR confirmation recorded on 2026-03-25 in run `#23563902873`
- hosted GitHub HL7 trial recorded on 2026-03-25 in run `#23564057337`
- an explicit decision to keep HL7 manual-only in the default hosted matrix to control recurring runtime and maintenance cost
- repo-side Phase 6D release-facing polish across quickstart, deployment, release-readiness, and handoff docs

## Current next slices

### Post-Phase-6 follow-through

Goal:

- move beyond the now-expanded synthetic casebook toward de-identified or externally supplied benchmark inputs while preserving the reviewer-facing proof shape

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
