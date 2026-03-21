# MVP Plan — Pancreatic Signal

## MVP objective

Deliver a research-grade, open-source prototype that can ingest de-identified radiology report text, flag suspicious pancreatic cases using a transparent rule engine, and support a minimal reviewer workflow.

## Why this MVP

This version maximizes:
- feasibility for a small team or solo builder
- explainability
- retrospective evaluation readiness
- extensibility into trial matching and imaging modules

It avoids the hardest early blockers:
- raw DICOM inference
- hospital integration
- model governance for black-box AI
- patient-facing or treatment-facing claims

## MVP scope

### In scope
- CSV / JSONL ingestion
- rule-based pancreatic suspicion scoring
- evidence highlighting
- worklist UI
- case detail UI
- reviewer actions and notes
- export
- demo dataset and evaluation scaffold

### Out of scope
- PACS integration
- EHR integration
- user / org management beyond mock auth
- LLM-only inference
- active learning
- production deployment hardening

## MVP deliverables

1. API service
2. Web worklist
3. Demo dataset
4. Rule ontology
5. Evaluation scripts
6. Documentation for future autonomous implementation

## Feature breakdown

### Feature 1 — Report ingestion
#### Capability
Upload or load structured report data and persist a normalized report record.

#### Acceptance criteria
- accepts CSV and JSONL
- validates schema
- stores raw and normalized text
- returns import summary

### Feature 2 — Triage engine
#### Capability
Generate structured pancreatic suspicion output from report text.

#### Acceptance criteria
- emits risk score 0–1
- emits urgency band
- emits rationale codes
- emits evidence spans with section + sentence offsets
- handles simple negation and uncertainty

### Feature 3 — Case creation
#### Capability
Convert triage outputs into searchable queue items.

#### Acceptance criteria
- each imported report maps to a case record
- case statuses persist
- repeated imports update rather than duplicate when configured

### Feature 4 — Reviewer worklist
#### Capability
Enable reviewers to sort and inspect flagged cases.

#### Acceptance criteria
- list view with filters
- case detail page
- reviewer note / status actions
- assignment field
- audit log display

### Feature 5 — Evaluation
#### Capability
Measure usefulness of the triage engine on demo / labeled data.

#### Acceptance criteria
- precision / recall calculation script
- top-k review yield calculation
- qualitative error bucket template

## MVP architecture decisions
- backend-first: FastAPI
- frontend: Next.js App Router
- storage: SQLite locally, Postgres-ready
- triage logic: Python service layer with configurable YAML / JSON ontology
- auth: mocked
- jobs: synchronous now

## Data contract for v1
Required fields:
- report_id
- case_id or patient_id
- report_datetime
- modality
- report_text

Recommended fields:
- impression_text
- findings_text
- indication
- site
- accession_number

## Prioritized implementation order

### Sprint 1
- repo boots
- health endpoints
- schemas
- demo dataset
- ontology files

### Sprint 2
- rule engine
- triage endpoint
- batch ingestion

### Sprint 3
- database persistence
- worklist endpoint
- case detail endpoint

### Sprint 4
- web worklist
- web case detail
- reviewer actions

### Sprint 5
- export
- evaluation script
- polishing docs and examples

## Definition of done
The MVP is done when a new contributor can:
1. run the stack locally
2. load the sample dataset
3. view prioritized pancreatic-signal cases in the UI
4. inspect why each case was flagged
5. export results
6. understand what to build next from the docs
