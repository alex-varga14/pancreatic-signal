# Data model

This document describes the persisted relational entities in the current implementation and the main API-facing derived surfaces that sit on top of them.

## Persisted entities

### `CaseRecord`

Represents the triage thread shown in the reviewer worklist.

Current fields:

- `case_id`: stable primary key
- `report_id`: canonical linked report identifier
- `score`: deterministic triage score
- `urgency`: current urgency band
- `status`: reviewer workflow state
- `site`: optional site or tenant hint
- `assigned_to`: current assignee, if any
- `rationale_codes`: stored rationale family codes
- `created_at`
- `updated_at`

Relationships:

- one-to-many reports
- one-to-many findings
- one-to-many review actions

### `ReportRecord`

Stores the source report text plus import metadata that explains where the report came from.

Current fields:

- `report_id`: stable primary key
- `case_id`: owning case
- `report_datetime`
- `modality`
- `site`
- `patient_identifier`
- `encounter_identifier`
- `accession_number`
- `ordering_provider`
- `source_system`
- `source_format`
- `import_source_id`
- `raw_text`
- `normalized_text`
- `created_at`

Notes:

- `source_format` distinguishes direct report, FHIR, HL7, or other supported import shapes.
- The metadata fields above are intentionally nullable because upstream payloads vary.

### `FindingRecord`

Represents a persisted piece of structured triage evidence.

Current fields:

- `id`
- `case_id`
- `report_id`
- `code`
- `label`
- `section`
- `sentence_index`
- `char_start`
- `char_end`
- `evidence_text`
- `score_contribution`
- `sort_order`
- `created_at`

Notes:

- Findings are evidence-bearing outputs from the deterministic engine, not generic annotations.
- `sort_order` preserves stable presentation order in downstream APIs and UI surfaces.

### `ReviewActionRecord`

Stores human workflow actions against a case.

Current fields:

- `id`
- `case_id`
- `action`
- `reviewer`
- `note`
- `assigned_to`
- `created_at`

Notes:

- Review actions are the current durable audit trail for workflow changes.
- The implementation does not use a separate generic audit-events table.

### `ImportRunRecord`

Summarizes one structured adapter import run.

Current fields:

- `id`
- `source_format`
- `source_name`
- `actor_user_id`
- `actor_role`
- `actor_site_scope`
- `imported_sites`
- `status`
- `processed_count`
- `flagged_count`
- `created_count`
- `updated_count`
- `failed_count`
- `failure_counts`
- `started_at`
- `completed_at`

Notes:

- This record is the top-level persisted audit surface for FHIR and HL7 import operations.
- `failure_counts` uses structured buckets such as parse, validation, unsupported payload, and site-scope rejection.

### `ImportRunItemRecord`

Stores per-item detail for a structured import run.

Current fields:

- `id`
- `run_id`
- `item_index`
- `status`
- `source_identifier`
- `site`
- `case_id`
- `report_id`
- `error_bucket`
- `error_detail`
- `created_at`

Notes:

- Item records make it possible to audit partial failures and mixed-result runs without reprocessing logs.

## API-facing derived surfaces

### `ImportMetadata`

The API groups report provenance fields into `ImportMetadata` for request and response payloads:

- `patient_identifier`
- `encounter_identifier`
- `accession_number`
- `ordering_provider`
- `source_system`
- `source_format`
- `import_source_id`

This surface is used in triage input schemas and case detail responses.

### `HybridAnalysis`

Hybrid analysis is not a separate persisted table in the current relational model. It is a derived API surface with:

- `calibrated_score`
- `confidence_label`
- `review_priority`
- `active_learning_priority`
- `summary`
- `factors`
- `sentence_candidates`

Each `sentence_candidate` includes text, section, sentence index, score, classification, matched codes, and signal-level rationale.

### Case list and case detail responses

The main reviewer APIs derive additional computed fields from persisted state, including:

- hybrid ranking deltas and confidence on list items
- review feedback counts and latest feedback labels
- full report text, import metadata, evidence, review actions, and feedback on case detail

### Trial matching response

Trial matching is also derived rather than persisted as a dedicated table. The API returns:

- a structured pancreatic abstraction
- zero or more explainable `TrialCandidate` results
- criterion-level traces for each candidate

## Workflow values in active use

The current docs and UI should assume at least these workflow concepts are active:

- case statuses such as `new`, `in_review`, `escalated`, `dismissed`, and `closed`
- import-run statuses `completed` and `failed`
- import item statuses `imported` and `failed`
- import failure buckets `parse_error`, `validation_error`, `unsupported_payload`, and `site_scope_rejection`

## Practical modeling rules

- Keep explainability close to the stored case and finding records.
- Preserve provenance on reports even when an upstream payload is incomplete.
- Prefer explicit structured failure buckets over free-form import failure states.
- Treat review actions, feedback, and import runs as separate but complementary audit surfaces.
