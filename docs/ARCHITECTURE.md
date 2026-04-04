# Architecture

## 1. Overview

Pancreatic Signal is a modular monorepo with two primary product pillars: explainable report triage and pancreatic oncology research intelligence. The implementation keeps clear boundaries between ingestion, triage, reviewer workflow, research monitoring, evaluation, and pilot packaging:

- `apps/api` handles ingestion, triage, research-intel runs, persistence, auth, evaluation, and trial matching
- `apps/web` provides the reviewer worklist, case detail experience, import workspace, and the `/research-intel` workspace
- `data` stores demo reports, ontology files, trial-matching rule assets, and research-intel source/topic catalogs
- `docs` contains the operator, product, benchmark, and handoff materials
- `scripts` provides local tooling, smoke helpers, and evaluation/export helpers

## 2. Current end-to-end flow

1. A user imports report text directly or submits structured FHIR/HL7 content.
2. The API extracts report text, structured identifiers, and source metadata.
3. The rule engine normalizes text, sections content, extracts evidence spans, and assigns pancreatic rationale codes.
4. Hybrid analysis optionally augments the deterministic result with calibrated scoring, confidence, sentence candidates, and review-priority hints.
5. The API creates or updates case, report, and finding records.
6. Structured adapter imports also persist an import-run summary plus per-item audit results.
7. In parallel, research-intel ingests a pancreatic oncology watch catalog through seeded, fixture-backed, or opt-in live connector modes, computes a watchtower schedule over those sources, records source health plus provenance, applies pancreas-aware feed or repository filters where needed, resolves graph-backed pancreatic oncology entities, classifies documents into topic watchlists, extracts cited evidence, and stores council-ready artifacts.
8. Digest generation turns those research documents into persisted council summaries, multi-run history snapshots, disagreement metrics, and human-gated opportunities.
9. The web app reads persisted case detail, review history, feedback, hybrid guidance, import metadata, trial matches, and case-linked research briefs for human review.
10. Evaluation and benchmark helpers consume the same stored or generated outputs for reproducible proof artifacts, while research-intel opportunities can propose future benchmark, rule, or trial-catalog work.

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
      |            +------------------------+
      v                                     v
[Hybrid analysis]                 [Research-intel schedule + ingest + topic clustering]
      |                                     |
      v                                     v
[Trial abstraction helpers]     [Council digest + opportunity generation]
      |            |                         |
      +-----+------+-------------------------+
            |
            v
 [SQLAlchemy persistence layer]
            |
      +-----------+-------------+
      |           |             |
      v           v             v
[Cases API] [Research-intel API] [Eval + benchmark helpers]
      |           |
      +-----+-----+
            |
            v
[Next.js reviewer, import, and research-intel UI]
```

## 4. API architecture principles

- deterministic baseline behavior remains inspectable
- hybrid outputs may improve ranking but must not replace explainability
- research-intel outputs may guide contributors and reviewers but must not automatically rewrite case scores
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

### Research intelligence

Research-intel is intentionally a sibling domain, not an extension of the case-level deidentification views. Its first implementation is deterministic and artifact-driven:

- a curated source registry plus seeded pancreatic oncology watch catalog
- schedule-aware source planning with due-only ingestion, next-run timing, and failure-aware cadence
- topic classification against a lightweight pancreatic ontology and graph
- cited evidence extraction for every stored research document
- three-stage council generation with persisted stage outputs and disagreement score
- digest-history snapshots that compare the current digest against recent runs and preserve recurring open questions plus disagreement points
- opportunity generation for benchmark gaps, rule gaps, trial-catalog gaps, case briefs, community projects, and external tooling
- typed discovery-to-action specs that connect each opportunity to evidence bundles, open questions, measurable outcomes, contributor packets, and downstream artifact hints
- proposal-only experiment runs for benchmark and rule opportunities, with readiness or stress-test modes, ratchet outcomes, and artifact-backed audit trails

These outputs are allowed to inform case briefs, benchmark planning, and contributor priorities, but not to mutate the triage engine automatically.

## 6. Persistence and audit model

The durable relational core is:

- `CaseRecord`
- `ReportRecord`
- `FindingRecord`
- `ReviewActionRecord`
- `ImportRunRecord`
- `ImportRunItemRecord`
- `ResearchSourceRecord`
- `ResearchRunRecord`
- `ResearchRunItemRecord`
- `ResearchDocumentRecord`
- `ResearchEvidenceRecord`
- `ResearchTopicRecord`
- `ResearchDigestRecord`
- `ResearchOpportunityRecord`

There is no separate generic `AuditEvent` table in the current implementation. Instead, auditability is expressed through:

- review-action history on cases
- timestamps on persisted domain records
- structured import-run summaries and item-level import results
- structured research-intel run summaries, digest payloads, and promotion artifacts

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
- broader live source coverage beyond the current fixture-backed and selectively live-ready research-intel connector set
- more capable council backends and sandboxed benchmark experiments
- future async execution for heavier import or evaluation loads

What it does not currently prioritize is PACS-native imaging inference or opaque retrieval-heavy decision paths.
