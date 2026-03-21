# Agent implementation guide

This repository is intentionally scaffolded for phased autonomous implementation.

## Primary objective

Build a research-first, open-source triage stack that identifies radiology reports suspicious for pancreatic cancer or high-risk pancreatic abnormalities and routes them to a human-reviewed worklist.

## Non-goals

- autonomous diagnosis
- direct clinical decision making without human review
- PACS-native image inference in the initial phases
- production hospital deployment in the MVP
- medical-device style claims

## Implementation priorities

### Phase A — foundation
- Ensure API boots, healthcheck passes, and demo data loads.
- Keep the data model simple and evolvable.
- Preserve full auditability of every flag and reviewer action.

### Phase B — rule-based triage MVP
- Build transparent pattern-based extraction for explicit findings and secondary signs.
- Every flag must include evidence spans and a rationale code.
- Prioritize false-negative reduction, but expose threshold controls.

### Phase C — reviewer workflow
- Worklist with filters: new, in-review, escalated, closed.
- Case details page with report text, highlighted evidence, structured findings, and notes.
- Reviewer actions: assign, escalate, dismiss, request follow-up.

### Phase D — evaluation
- Batch evaluation pipeline against labeled retrospective data.
- Metrics: precision, recall, sensitivity at top-k, reviewer yield, time-saved simulation.
- Error buckets: wording variance, negation failure, incidental cysts, pancreatitis confounders.

### Phase E — trial matching extension
- Add structured patient / disease abstraction fields.
- Match against PDAC trial criteria using explainable rules and retrieval.

## Engineering constraints

- API: Python + FastAPI
- Web: Next.js + TypeScript
- Database: Postgres in docker-compose, SQLite allowed for local fallback
- Background jobs: stubbed now, Celery / Dramatiq later
- Auth: mock auth now, pluggable SSO later
- Data ingestion: CSV / JSONL first, HL7/FHIR later
- Prefer simple modules over frameworks that obscure logic

## Quality bar

Do not add opaque ML before the rule engine is stable and benchmarked.
Do not remove explainability from any triage output.
Do not hardcode UI assumptions into the API.
Do not claim clinical validation.

## Acceptance criteria for MVP
- A user can load example reports.
- The system scores and stores cases.
- The web app shows a prioritized queue.
- A reviewer can inspect why a case was flagged.
- Reviewer actions are persisted.
- Evaluation scripts can run on the demo dataset.
