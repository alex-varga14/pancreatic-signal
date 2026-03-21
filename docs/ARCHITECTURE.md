# Architecture

## 1. Overview

Pancreatic Signal is organized as a modular monorepo with:
- `apps/api` — ingestion, triage, persistence, evaluation endpoints
- `apps/web` — reviewer-facing dashboard
- `data` — demo reports and ontology files
- `docs` — specification and handoff materials
- `scripts` — local bootstrapping and packaging

## 2. High-level flow

1. Reports are imported from CSV / JSONL.
2. API normalizes and segments report text.
3. Triage engine scores pancreatic suspicion.
4. Findings and evidence spans are persisted.
5. Cases are shown in a prioritized worklist.
6. Reviewer actions update status and audit logs.
7. Exports and evaluation pipelines consume structured outputs.

## 3. Component diagram

```text
[Importer / CLI / Upload]
          |
          v
   [FastAPI ingestion]
          |
          v
 [Preprocessor + Parser]
          |
          v
   [Triage Engine v1]
          |
   +------+------+
   |             |
   v             v
[DB models]   [Export / Eval]
   |
   v
[Cases API]
   |
   v
[Next.js worklist UI]
```

## 4. API design principles
- clean JSON contracts
- deterministic triage output
- auditable rationale codes
- API should be UI-agnostic
- versionable endpoints from day one

## 5. Triage engine design

### Stage 1 — sectioning
Split report into findings / impression when possible.

### Stage 2 — sentence analysis
Run pattern matching over each sentence.

### Stage 3 — evidence extraction
Collect evidence spans, offsets, section name, and matched ontology codes.

### Stage 4 — scoring
Aggregate matches using weighted heuristics:
- explicit mass terms = high weight
- secondary sign combinations = medium-high weight
- follow-up recommendations = additive
- negations / benign explanations = subtractive or suppressive

### Stage 5 — output normalization
Emit:
- score
- urgency band
- finding list
- rationale summary
- explainability metadata

## 6. Persistence model
The core entities are:
- Case
- Report
- Finding
- ReviewAction
- TrialCandidate (future)
- AuditEvent

See `docs/DATA_MODEL.md`.

## 7. Extensibility plan
The architecture intentionally allows:
- swapping rule engine for hybrid rules + ML
- replacing local file ingestion with FHIR / HL7 adapters
- integrating trial matching
- connecting imaging outputs later

## 8. Operational modes

### Research mode
- local or sandbox deployment
- de-identified data
- retrospective analysis
- configurable thresholds

### Pilot mode
- daily imports
- human navigator queue
- no autonomous escalation

## 9. Security posture for MVP
- no PHI is included in demo data
- local-only defaults
- simple mock auth
- visible audit logging
- secrets via environment variables only

## 10. Future architecture additions
- async jobs for large batches
- vector / retrieval layer for trial eligibility explanations
- site-specific rule packs
- report deduplication / longitudinal threading
