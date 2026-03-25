# Architecture

## 1. Overview

Pancreatic Signal is a modular monorepo with clear boundaries between ingestion, triage, reviewer workflow, evaluation, and pilot packaging:

- `apps/api` handles ingestion, triage, persistence, auth, evaluation, and trial matching
- `apps/web` provides the reviewer worklist, case detail experience, and import workspace
- `data` stores demo reports, ontology files, and trial-matching rule assets
- `docs` contains the operator, product, benchmark, and handoff materials
- `scripts` provides local tooling, smoke helpers, and evaluation/export helpers

## 2. Current end-to-end flow

1. A user imports report text directly or submits structured FHIR/HL7 content.
2. The API extracts report text, structured identifiers, and source metadata.
3. The rule engine normalizes text, sections content, extracts evidence spans, and assigns pancreatic rationale codes.
4. Hybrid analysis optionally augments the deterministic result with calibrated scoring, confidence, sentence candidates, and review-priority hints.
5. The API creates or updates case, report, and finding records.
6. Structured adapter imports also persist an import-run summary plus per-item audit results.
7. The web app reads persisted case detail, review history, feedback, hybrid guidance, import metadata, and trial matches for human review.
8. Evaluation and benchmark helpers consume the same stored or generated outputs for reproducible proof artifacts.

## 3. Runtime component map

```text
[Report / FHIR / HL7 import]
            |
            v
   [FastAPI auth + adapters]
            |
            v
 [Normalization + rule triage]
            |
      +-----+------+
      |            |
      v            v
[Hybrid analysis] [Trial abstraction helpers]
      |            |
      +-----+------+
            |
            v
 [SQLAlchemy persistence layer]
            |
      +-----+------+
      |            |
      v            v
[Cases / imports API] [Eval + benchmark helpers]
      |
      v
[Next.js reviewer and import UI]
```

## 4. API architecture principles

- deterministic baseline behavior remains inspectable
- hybrid outputs may improve ranking but must not replace explainability
- API contracts stay UI-agnostic and versionable
- audit visibility is a first-class product concern, not a side effect
- structured adapters should degrade into explicit failure buckets rather than silent drops

## 5. Core service layers

### Ingestion adapters

The API supports three import shapes:

- direct report-text payloads for local/demo and simple integrations
- FHIR `DiagnosticReport` ingestion for structured clinical interoperability
- HL7 ORU ingestion for legacy feed compatibility

Adapter code is responsible for extracting text, preserving import metadata, and classifying unsupported or malformed payloads clearly.

### Rule triage engine

The deterministic triage service:

- sections report text where possible
- evaluates sentence-level pattern families
- applies negation and contextual suppression
- emits evidence spans and rationale codes
- assigns a bounded score and urgency level

### Hybrid analysis

Hybrid analysis is a separate layer that enriches the baseline result with:

- calibrated score
- confidence label
- review priority
- active-learning-oriented priority hints
- summary factors
- sentence-level candidates with matched codes and rationales

This keeps the rule engine legible while still surfacing ranking improvements.

### Trial matching

Trial matching operates on persisted case/report evidence and derived abstractions. It is rule-based and explainable: every candidate includes a score, status, rationale, and criterion-level traces.

## 6. Persistence and audit model

The durable relational core is:

- `CaseRecord`
- `ReportRecord`
- `FindingRecord`
- `ReviewActionRecord`
- `ImportRunRecord`
- `ImportRunItemRecord`

There is no separate generic `AuditEvent` table in the current implementation. Instead, auditability is expressed through:

- review-action history on cases
- timestamps on persisted domain records
- structured import-run summaries and item-level import results

## 7. Auth and deployment modes

### Local development mode

- mock auth enabled by default
- fast iteration for API, web, and demo imports
- suitable for synthetic or de-identified local work

### Pilot modes

The current pilot packaging supports:

- trusted-proxy auth using an upstream identity envelope
- field-level header auth with explicit forwarded actor fields
- site-scoped imports and access decisions
- shared reviewer identities when desired for demos

These modes are documented and smoke-tested; they are not marketed as full enterprise SSO integrations.

## 8. Current smoke and deployment boundary

The pilot smoke workflow intentionally splits coverage:

- hosted GitHub Actions covers base report success, attachment-backed FHIR success, report-path site rejection, and structured adapter site rejection
- manual/operator-driven smokes still cover the broader HL7 success path, shared-visibility paths, audit-denial flows, and additional structured failure paths

This boundary is deliberate and should stay aligned with `docs/DEPLOYMENT.md` and the active workflow file.

## 9. Extensibility and remaining architecture work

The architecture still leaves room for:

- deeper FHIR and HL7 interoperability coverage
- stronger enterprise auth integrations beyond pilot modes
- broader trial catalogs and abstraction depth
- richer feedback loops around reviewer labels and hybrid prioritization
- future async execution for heavier import or evaluation loads

What it does not currently prioritize is PACS-native imaging inference or opaque retrieval-heavy decision paths.
