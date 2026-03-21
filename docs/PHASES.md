# Phased implementation plan

## Phase 0 — Repository foundation
### Goal
Make the repo runnable and understandable.

### Deliverables
- bootable API and web shell
- demo data
- docs complete enough for contributors
- packaging scripts

### Exit criteria
- `uvicorn app.main:app` works
- `npm run dev` works
- example files exist

---

## Phase 1 — Deterministic triage MVP
### Goal
Flag suspicious pancreatic reports from text.

### Work items
- ontology completion
- report normalization
- negation handling
- weighted rule scoring
- structured findings model
- triage endpoints

### Exit criteria
- batch import produces structured triage outputs
- evidence spans visible in API output
- tests cover core rule families

---

## Phase 2 — Reviewer workflow
### Goal
Turn triage outputs into a usable queue.

### Work items
- case persistence
- worklist filters
- case detail page
- status transitions
- reviewer notes and assignments

### Exit criteria
- cases can be reviewed end to end
- audit actions persist
- UI reads live API data

---

## Phase 3 — Evaluation and retrospective studies
### Goal
Quantify value.

### Work items
- evaluation scripts
- error bucket templates
- export files
- calibration / threshold analysis
- charting notebook placeholders

### Exit criteria
- reproducible evaluation run on demo / labeled data
- documented benchmark procedure

---

## Phase 4 — Trial matching extension
### Goal
Assist downstream pancreatic oncology coordination.

### Work items
- structured abstractions
- trial criteria retrieval
- explainable rule-based matching
- eligibility trace UI

### Exit criteria
- a case can show potential PDAC trial candidates with explanation

---

## Phase 5 — Hybrid AI upgrade
### Goal
Improve sensitivity and robustness while preserving explainability.

### Work items
- sentence classifier
- ranking model
- confidence calibration
- active learning queue
- site-specific adaptation

### Exit criteria
- hybrid system benchmarks above rules-only baseline
- explanations remain reviewer-usable

---

## Phase 6 — Integration and deployment
### Goal
Support real research pilots.

### Work items
- FHIR / HL7 adapters
- SSO
- observability
- de-identification pipeline
- deployment manifests

### Exit criteria
- documented pilot deployment path
