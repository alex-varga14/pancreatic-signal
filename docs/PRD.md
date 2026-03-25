# Product Requirements Document — Pancreatic Signal

## 1. Product summary

Pancreatic Signal is an open-source, research-first triage platform for identifying radiology reports that may contain pancreatic malignancy signals, high-risk pancreatic abnormalities, or important follow-up recommendations, then routing those cases into a human-reviewed worklist.

The current product is no longer an early prototype. It now includes reviewer workflow, explainable trial matching, hybrid prioritization, structured FHIR and HL7 ingestion, import-run auditing, and pilot deployment/auth packaging on top of the deterministic rule engine.

## 2. Product problem

Important pancreatic findings are often delayed operationally, not only diagnostically. Suspicious language can be:

- subtle or indirect
- buried in long report text
- attached to follow-up recommendations that are easy to miss
- surfaced in broad abdominal workflows instead of dedicated pancreatic review queues
- hard to audit consistently across retrospective or pilot environments

The product exists to reduce those workflow misses by surfacing high-value reports for faster human review without obscuring why they were flagged.

## 3. Goals

### Primary goals

- detect suspicious pancreatic report text with transparent evidence and rationale codes
- prioritize a reviewer worklist around risk, confidence, and operational review value
- preserve auditability for imports, reviewer actions, and pilot access controls
- support research, retrospective evaluation, and controlled pilot demonstrations
- provide an open, explainable baseline that others can benchmark against

### Secondary goals

- surface follow-up-sensitive cases even when malignancy language is indirect
- support explainable downstream trial pre-screening from current case evidence
- preserve enough metadata to support interoperability audits and site-scoped pilots
- expose hybrid ranking improvements without replacing the deterministic baseline

## 4. Non-goals

- autonomous diagnosis
- patient-facing interpretation
- treatment recommendation
- image-native inference from PACS or DICOM
- unsupervised production deployment guidance
- claims of clinical validation or regulatory clearance

## 5. Primary users

- nurse navigators and oncology coordinators
- radiology quality or safety teams
- research coordinators running retrospective datasets
- clinical informatics teams piloting explainable workflow tooling
- tumor-board or trial-screening support staff

## 6. Current supported workflows

### Workflow 1 — Direct report triage

A user submits report-text payloads through the API and receives structured triage outputs with score, urgency, rationale codes, evidence spans, and optional hybrid analysis.

### Workflow 2 — Structured adapter imports

A user imports FHIR `DiagnosticReport` or HL7 ORU content. The system extracts report text and metadata, triages the result, persists cases and reports, and records import-run summaries plus item-level audit detail.

### Workflow 3 — Reviewer worklist and case review

A reviewer opens the web worklist, filters or sorts cases, inspects full report text, reviews evidence and rationale, checks hybrid guidance, and records review actions or feedback.

### Workflow 4 — Explainable trial matching

A reviewer or coordinator requests case-level trial matching and sees structured pancreatic abstractions plus explainable PDAC trial candidates.

### Workflow 5 — Retrospective evaluation and public benchmarking

A contributor runs the demo evaluation or external benchmark workflow, generates comparable benchmark artifacts, and publishes results with consistent labels and validation.

## 7. Functional requirements

### FR1 — Ingestion and interoperability

The system must:

- accept direct report-text payloads and batch report imports
- accept supported FHIR `DiagnosticReport` payloads
- accept supported HL7 ORU payloads
- preserve source metadata such as patient identifier, encounter identifier, accession number, ordering provider, source system, source format, and import source identifier when available
- persist run-level and item-level audit detail for structured imports
- surface structured failure buckets for parse, validation, unsupported payload, and site-scope rejection paths

### FR2 — Explainable triage

The system must:

- score pancreatic risk on a bounded scale
- emit urgency and rationale codes
- preserve evidence spans with section and character offsets
- remain explainable at the sentence and finding level
- support hybrid analysis that augments ranking without hiding the deterministic baseline

### FR3 — Case persistence and review

The system must:

- create or update cases and reports on import
- persist findings separately from reports
- support reviewer assignment, notes, escalation, dismissal, closure, and reopen-style follow-up actions through review records
- expose reviewer feedback history in addition to action history
- keep site scoping visible in case and import behavior where applicable

### FR4 — Reviewer-facing product surfaces

The web experience must:

- expose a prioritized case list
- allow filtering and sorting by workflow-relevant fields
- show full report text, import metadata, evidence, review history, and feedback on case detail
- expose explainable trial matches without presenting them as definitive enrollment guidance
- preserve research-only framing throughout the experience

### FR5 — Pilot auth and deployment support

The platform must:

- remain easy to run locally with mock auth
- support trusted-proxy and field-level header auth for controlled pilots
- preserve audit visibility around site-scope acceptance and denial behavior
- ship with smokeable deployment overlays and documented operator workflows

### FR6 — Evaluation and open comparison

The repository must:

- support reproducible demo evaluation and threshold sweeps
- generate benchmark proof artifacts from the demo dataset
- generate comparable external benchmark bundles
- validate public submission JSON against the shared schema
- keep documentation aligned with the actual implementation state

## 8. Current product boundaries

The current release intentionally stops short of:

- enterprise identity-provider integrations beyond the pilot auth modes
- longitudinal patient threading across multiple external systems
- automated follow-up closure detection from downstream EHR state
- image-derived features or PACS-native workflows
- a closed-loop active learning queue that retrains or rewrites thresholds automatically

## 9. Success measures

### Workflow measures

- import success rate across report, FHIR, and HL7 paths
- reviewer time-to-understand why a case was flagged
- queue usefulness at the top reviewed ranks
- visibility of failed or denied imports during pilot operations

### Quality measures

- recall and precision on labeled datasets
- sensitivity and precision at top-k review depth
- follow-up recommendation capture on the demo and benchmark flows
- reduction in unexplained false positives and negation failures

### Platform measures

- repeatable `make validate-strict` health
- accurate deployment and handoff documentation
- successful pilot smoke coverage for the intended hosted/manual matrix

## 10. Known risks

- wording variance and secondary-sign-only reports can still evade deterministic rules
- inflammatory or cystic confounders can still overcall risk
- reviewers may overtrust scores if explanations are not kept prominent
- interoperability inputs vary by site and vendor, especially for structured narratives and identifiers
- pilot auth and site-scope behavior can drift if smoke coverage is not kept current

## 11. Near-term roadmap

The next requirements focus on late-Phase-6 hardening rather than new foundation work:

1. deepen benchmark coverage with more realistic labeled datasets
2. strengthen reviewer ergonomics and feedback utilization without weakening explainability
3. keep release-facing docs and onboarding surfaces aligned with the recorded hosted smoke evidence
4. preserve the intentional hosted/manual smoke boundary as release cadence evolves
5. continue interoperability hardening only where new pilot fixtures expose concrete gaps

## 12. Release-readiness criteria for the current phase

The current product state is release-ready for research and controlled pilot packaging when:

- direct report, FHIR, and HL7 imports behave as documented
- import-run audit lookup matches persisted structured import behavior
- reviewer workflow, feedback, and trial matching work end to end
- deployment overlays and smoke workflows reflect the real supported auth modes
- benchmark artifacts and validation commands remain reproducible
- docs describe the implementation that actually ships, not an earlier MVP plan
