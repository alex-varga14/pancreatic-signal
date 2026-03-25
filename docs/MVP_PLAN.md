# Platform Snapshot And Near-Term Plan

This repository is no longer in MVP planning mode. The core research-first triage platform is implemented, validated, and in late Phase 6 hosted smoke evidence capture and pilot-closeout work.

This document keeps the old filename for continuity, but it now serves as the current-state snapshot plus the near-term execution plan for the next few slices.

## Current platform status

Pancreatic Signal already supports:

- report-text ingestion for direct triage and batch imports
- structured FHIR `DiagnosticReport` imports
- HL7 ORU import handling, including recent metadata and parser hardening
- persisted case, report, finding, review-action, and import-run audit records
- a reviewer worklist with filters, case detail, notes, assignment, escalation, dismissal, and feedback capture
- hybrid prioritization alongside the deterministic rule engine
- explainable PDAC trial matching from current case evidence
- pilot auth and deployment modes for mock auth, trusted-proxy auth, and header-based auth
- de-identified research views, benchmark artifacts, and external evaluation bundle generation

## What the current platform is optimized for

The platform is designed for:

- research-first workflow support rather than autonomous diagnosis
- transparent text triage with evidence spans and rationale codes
- human-reviewed queueing and escalation workflows
- auditable import, review, and pilot smoke behavior
- open benchmarking and reproducible evaluation

The platform is intentionally not designed for:

- image-native inference from DICOM or PACS
- patient-facing recommendations
- unsupervised clinical deployment
- opaque model-only decision making
- production EHR rollout claims

## Current capability areas

### Ingestion and normalization

- Direct report imports accept structured report text with optional import metadata.
- FHIR imports preserve attachment-backed narratives, structured identifiers, and source metadata.
- HL7 imports preserve source identifiers, accession/provider metadata, and parser failure detail.
- Every structured import path can persist an import-run summary and item-level audit trail.

### Triage and prioritization

- The deterministic rule engine remains the baseline scoring layer.
- Triage outputs include a normalized score, urgency, rationale codes, and evidence spans.
- Hybrid analysis adds calibrated ranking, confidence, review-priority hints, factors, and sentence-level candidates without replacing explainability.
- Threshold and scoring proof surfaces are already wired into the demo evaluation workflow.

### Reviewer workflow

- The web app exposes a live worklist with sort/filter support and case detail views.
- Reviewers can assign, escalate, dismiss, close, or annotate cases.
- Reviewer feedback is stored and summarized separately from review actions.
- Trial matching is available on case detail as an explainable downstream support feature.

### Pilot operations

- Local development defaults to mock auth so the stack is easy to boot.
- Pilot overlays support trusted-proxy identity envelopes and field-level header auth.
- Site scoping, import denial behavior, audit visibility, and failure-path smoke coverage exist in both pilot auth modes.
- Hosted GitHub smoke coverage now includes the base report success path, attachment-backed FHIR success path, and site-rejection checks, with a narrower `fhir-success-only` dispatch option.

### Evaluation and public proof

- Demo benchmark artifacts are generated and checked into `docs/examples/`.
- The repo can generate comparable external benchmark bundles and validate third-party submissions.
- Release-readiness, deployment, and handoff docs are maintained as active operator references rather than aspirational notes.

## What remains near term

The next work is not foundation work. It is targeted late-Phase-6 execution:

1. Record the first green GitHub-hosted FHIR-only pilot smoke run.
2. Decide whether HL7 success smoke should join the hosted workflow matrix or remain operator-triggered.
3. Keep release-facing docs and release evidence aligned as hosted smoke evidence lands.
4. Expand real benchmark and retrospective evaluation inputs beyond the synthetic/demo set.
5. Keep improving reviewer ergonomics and feedback loops without weakening explainability.

## What is still intentionally incomplete

- There is no production-ready enterprise SSO integration yet; the current pilot modes are mock, trusted-proxy, and fixed-header auth.
- Trial matching is implemented, but the trial catalog and abstraction layer remain curated and rules-based.
- Hybrid analysis exposes active-learning-oriented prioritization fields, but there is not yet a full closed-loop active learning workflow.
- Deployment guidance targets research and controlled pilot environments, not general hospital production rollout.

## Current definition of ready

The repository is in a good operational state when a new contributor can:

1. boot the API and web app locally
2. import sample data through the supported report or structured adapter paths
3. inspect cases, evidence, import metadata, and reviewer actions in the UI
4. review import-run audit summaries and failure details
5. run the benchmark and validation workflows
6. understand the next late-Phase-6 priorities from the docs without private handoff
