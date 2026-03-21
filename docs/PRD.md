# Product Requirements Document — Pancreatic Signal

## 1. Product summary

Pancreatic Signal is an open-source, research-first triage platform that analyzes radiology report text for signals suspicious for pancreatic malignancy or other high-risk pancreatic abnormalities, then routes those cases into a human-reviewed workflow for faster review, escalation, and downstream navigation.

The product intentionally targets the **workflow gap** between imaging interpretation and timely follow-up, rather than trying to autonomously diagnose pancreatic cancer from scans.

## 2. Problem statement

Pancreatic cancer is frequently detected late. In practice, many clinically important delays happen not only because lesions are difficult to see, but because suspicious findings are:
- subtle or described indirectly
- buried in free-text radiology reports
- recommended for follow-up without reliable closed-loop tracking
- not consistently routed to navigators, tumor boards, or oncology review
- discovered in non-specialist workflows where pancreatic suspicion is not the primary clinical question

A lightweight, explainable triage layer can help identify and queue these reports for faster human review.

## 3. Goals

### Primary goals
- Identify radiology reports suspicious for pancreatic cancer or high-risk pancreatic findings.
- Surface exact evidence phrases and structured rationales.
- Route flagged cases into a prioritized reviewer / navigator queue.
- Create an auditable retrospective and prospective workflow.
- Provide a clean open-source foundation for research collaborations.

### Secondary goals
- Track downstream actions and timing metrics.
- Support trial pre-screening extensions.
- Enable future imaging-assisted modules without redesigning the platform.

## 4. Non-goals
- Replacing radiologists or oncologists.
- Providing direct patient-facing diagnosis.
- Autonomous treatment recommendations.
- Production-grade EHR integration in MVP.
- Standalone image inference in v1.

## 5. Target users

### Primary users
- Nurse navigators
- Oncology program coordinators
- Radiology quality teams
- Research coordinators
- GI / pancreatic tumor board support staff

### Secondary users
- Radiologists validating retrospective findings
- Clinical informatics teams
- Pancreatic cancer researchers
- Trial screening teams

## 6. Core use cases

### UC1 — Retrospective quality audit
A research coordinator uploads historic abdominal CT/MRI reports and identifies which cases the system would have flagged, why, and whether follow-up occurred.

### UC2 — Daily navigator worklist
A navigator receives a queue of new suspicious pancreatic reports with priority score, evidence spans, and status controls.

### UC3 — Reviewer case inspection
A reviewer opens a case, sees the full report text with highlighted evidence, reviews structured findings and rationale codes, and records an action.

### UC4 — Follow-up gap detection
The system identifies reports with follow-up recommendations but no documented closure.

### UC5 — Trial matching extension
A coordinator uses structured findings and basic patient abstractions to pre-screen for pancreatic oncology trials.

## 7. Functional requirements

### FR1 — Ingestion
- Accept CSV and JSONL report batches.
- Required fields: report_id, patient_id or pseudonymous case_id, accession date, modality, report text.
- Optional fields: site, ordering service, radiologist, exam description, indication.

### FR2 — Preprocessing
- Normalize whitespace and punctuation.
- Segment report into sections if available (history, technique, findings, impression).
- Sentence split report text.
- Detect negation windows and uncertainty phrases.
- Preserve raw source text.

### FR3 — Triage engine
System must detect:
- explicit pancreatic mass mentions
- suspicious lesion language
- pancreatic duct dilation / abrupt cut-off / interruption
- double-duct sign
- focal pancreatic atrophy
- vascular involvement language
- indeterminate pancreatic lesion
- worrisome cystic lesion descriptors
- recommended EUS / biopsy / follow-up language
- pancreatitis with suspicious morphology
- relevant combinations of secondary signs

System must emit:
- risk score
- urgency band
- rationale codes
- evidence spans
- confidence metadata
- suppression reasons where applicable (e.g., clear negation)

### FR4 — Case management
- Create or update a case on ingestion.
- Store review state: new, in_review, escalated, dismissed, closed.
- Allow note-taking and assignment.
- Record reviewer action history.

### FR5 — Worklist
- Sort by urgency, confidence, recency.
- Filter by status, site, modality, rationale, reviewer.
- Search by case id / report id.

### FR6 — Case detail view
- Show full report text with evidence highlights.
- Show extracted findings and rationale codes.
- Show audit history.
- Show reviewer notes and status controls.

### FR7 — Export and evaluation
- Export triage results to CSV / JSON.
- Support confusion-matrix labeling fields.
- Provide batch evaluation script hooks.

### FR8 — Configuration
- Tune pattern weights and thresholds.
- Enable / disable rationale families.
- Support site-specific rule packs later.

## 8. Future requirements
- FHIR / HL7 ingestion
- de-identification pipeline
- PACS / DICOM links
- trial matching
- imaging overlays
- active learning loop
- LLM summarization under strict review constraints

## 9. User stories

### Navigator
As a navigator, I want the highest-risk pancreatic cases surfaced first so that I can prioritize urgent review.

### Reviewer
As a reviewer, I want to know exactly which report phrases caused a case to be flagged so that I can trust and validate the output quickly.

### Research coordinator
As a research coordinator, I want to run the system on retrospective report sets and export labeled results so that I can evaluate its potential impact.

### Informatics lead
As an informatics lead, I want clear audit logs and configurable rules so that the system can be safely tested in a research environment.

## 10. Success metrics

### Product metrics
- batch ingestion success rate
- time to triage result
- reviewer time per case
- percentage of cases with usable evidence highlights

### Quality metrics
- recall on confirmed suspicious pancreatic reports
- precision at top-k queue positions
- reviewer acceptance rate of flagged cases
- follow-up recommendation capture rate
- negation error rate

### Workflow metrics
- hypothetical time-to-review reduction
- hypothetical time-to-navigation reduction
- trial pre-screen time reduction in future phases

## 11. Risks
- false positives from chronic pancreatitis, cystic lesions, post-op anatomy, or broad abdominal malignancy wording
- false negatives from unusual wording or buried secondary signs
- overtrust if the UI presents the score as a diagnosis
- institution-specific reporting style drift

## 12. Safety requirements
- visible research-only warning
- human review required for all outputs
- preserve raw source text
- explain every flag
- never hide uncertainty / negation logic
- do not surface patient-facing language

## 13. Release criteria for MVP
- all required ingestion paths work on demo data
- rule engine outputs stable structured triage results
- web queue and case detail pages function
- reviewer actions persist
- evaluation scripts and docs are present
- example dataset and ontology ship with the repo
