# Product Requirements Document — Pancreatic Signal

## 1. Product summary

Pancreatic Signal is an open-source, research-first pancreatic oncology platform with two primary pillars:

- a cited research-intelligence system for organizing pancreatic oncology literature, trial, guidance, and open-source signals into digest, opportunity, and case-brief workflows
- an explainable triage system for identifying radiology reports that may contain pancreatic malignancy signals, high-risk pancreatic abnormalities, or important follow-up recommendations, then routing those cases into a human-reviewed worklist

The current product is no longer an early prototype. It now includes reviewer workflow, explainable trial matching, hybrid prioritization, structured FHIR and HL7 ingestion, import-run auditing, and pilot deployment/auth packaging on top of the deterministic rule engine.

## 2. Product problem

Pancreatic oncology work is fragmented across literature, trials, guidelines, research tooling, and operational follow-up
queues. At the same time, important pancreatic findings are often delayed operationally, not only diagnostically.
Suspicious language can be:

- subtle or indirect
- buried in long report text
- attached to follow-up recommendations that are easy to miss
- surfaced in broad abdominal workflows instead of dedicated pancreatic review queues
- hard to audit consistently across retrospective or pilot environments

The product exists to turn those fragmented signals into cited, inspectable discovery artifacts and then use those artifacts
to reduce workflow misses through explainable downstream tools.

## 3. Goals

### Primary goals

- detect suspicious pancreatic report text with transparent evidence and rationale codes
- organize pancreatic oncology movement into cited digests, graph-backed topics, and open questions
- turn discovery output into concrete benchmark, rule, trial-catalog, and tooling proposals
- prioritize a reviewer worklist around risk, confidence, and operational review value
- preserve auditability for imports, reviewer actions, and pilot access controls
- support research, retrospective evaluation, and controlled pilot demonstrations
- provide an open, explainable baseline that others can benchmark against

### Secondary goals

- surface follow-up-sensitive cases even when malignancy language is indirect
- support explainable downstream trial pre-screening from current case evidence
- preserve enough metadata to support interoperability audits and site-scoped pilots
- expose hybrid ranking improvements without replacing the deterministic baseline
- create public, citation-backed pancreatic oncology digests and opportunity proposals for open-source contributors
- keep triage as an explainable applied surface rather than the only product narrative

## 4. Non-goals

- autonomous diagnosis
- patient-facing interpretation
- treatment recommendation
- image-native inference from PACS or DICOM
- unsupervised production deployment guidance
- claims of clinical validation or regulatory clearance

## 5. Primary users

- open-source contributors, benchmark curators, and research operators following pancreatic oncology signals
- nurse navigators and oncology coordinators
- radiology quality or safety teams
- research coordinators running retrospective datasets
- clinical informatics teams piloting explainable workflow tooling
- tumor-board or trial-screening support staff

## 6. Current supported workflows

### Workflow 1 — Research intelligence monitoring and case briefs

A contributor or operator runs discovery ingest and digest workflows, explores cited documents and graph activity, reviews
council output and opportunities, and links that context back to benchmarks, rules, trial upkeep, or individual cases
through generated briefs.

### Workflow 2 — Direct report triage

A user submits report-text payloads through the API and receives structured triage outputs with score, urgency, rationale codes, evidence spans, and optional hybrid analysis.

### Workflow 3 — Structured adapter imports

A user imports FHIR `DiagnosticReport` or HL7 ORU content. The system extracts report text and metadata, triages the result, persists cases and reports, and records import-run summaries plus item-level audit detail.

### Workflow 4 — Reviewer worklist and case review

A reviewer opens the web worklist, filters or sorts cases, inspects full report text, reviews evidence and rationale, checks hybrid guidance, and records review actions or feedback.

### Workflow 5 — Explainable trial matching

A reviewer or coordinator requests case-level trial matching and sees structured pancreatic abstractions plus explainable PDAC trial candidates.

### Workflow 6 — Retrospective evaluation and public benchmarking

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

- expose the research-intel workspace as a first-class discovery surface
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

### FR7 — Research intelligence

The system must:

- maintain a configurable pancreatic oncology source catalog and topic watchlist registry
- normalize research documents into persisted cited records with evidence spans, topic tags, and audit-backed run history
- expose public-read dashboard, document, digest, and opportunity surfaces while restricting run execution and promotion actions to authenticated operators
- generate case-level research briefs that inform benchmark, rule, or trial-catalog follow-up without mutating case scores
- keep opportunity promotion human-gated and citation-backed

## 8. Current product boundaries

The current release intentionally stops short of:

- enterprise identity-provider integrations beyond the pilot auth modes
- longitudinal patient threading across multiple external systems
- automated follow-up closure detection from downstream EHR state
- image-derived features or PACS-native workflows
- a closed-loop active learning queue that retrains or rewrites thresholds automatically
- autonomous live internet agent fleets or autonomous payment execution for paid research sources

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

The next requirements focus on turning the research watchtower into a steadier operating loop rather than adding another new foundation layer:

1. exercise collaborator bundles against larger benchmark and dataset contributions
2. keep triage and interoperability surfaces aligned with the discovery-first product framing without weakening explainability
3. expand connector quality and trust coverage where the current watchtower still leans on fixtures
4. preserve hosted watchtower trust with clear artifact outputs, digest gating, and human review boundaries
5. deepen graph and live-corpus quality so longer-horizon calibration remains meaningful at higher source volume

## 12. Release-readiness criteria for the current phase

The current product state is release-ready for research and controlled pilot packaging when:

- direct report, FHIR, and HL7 imports behave as documented
- import-run audit lookup matches persisted structured import behavior
- reviewer workflow, feedback, and trial matching work end to end
- deployment overlays and smoke workflows reflect the real supported auth modes
- benchmark artifacts and validation commands remain reproducible
- docs describe the implementation that actually ships, not an earlier MVP plan
