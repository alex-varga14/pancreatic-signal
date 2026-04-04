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

### `ResearchSourceRecord`

Stores the research-intel connector catalog that powers the pancreatic oncology watchtower.

Current fields:

- `source_id`
- `label`
- `source_kind`
- `trust_level`
- `access_class`
- `base_url`
- `description`
- `polling_config`
- `enabled`
- `created_at`
- `updated_at`

Notes:

- `polling_config` now carries both catalog configuration and runtime discovery state, including connector id, default mode, fixture or live settings, interval and priority metadata, and source-health metadata.
- Runtime health now also tracks consecutive failure counts so schedule views can expose backoff-aware cadence without a separate scheduler table.

### `ResearchRunRecord`

Summarizes one research-intel ingest or digest run.

Current fields:

- `id`
- `run_type`
- `status`
- `actor_user_id`
- `source_scope`
- `processed_count`
- `created_count`
- `updated_count`
- `failed_count`
- `failure_counts`
- `artifact_paths`
- `metadata_json`
- `started_at`
- `completed_at`

Notes:

- Ingest run metadata now records whether the run was `only_due`, which sources were requested, and which were skipped because they were not yet due.

### `ResearchRunItemRecord`

Stores per-item detail for research-intel runs.

Current fields:

- `id`
- `run_id`
- `item_index`
- `stage`
- `status`
- `source_identifier`
- `document_id`
- `error_bucket`
- `error_detail`
- `created_at`

### `ResearchDocumentRecord`

Stores canonical pancreatic oncology research documents after deduplication and normalization.

Current fields:

- `document_id`
- `source_id`
- `source_identifier`
- `document_type`
- `title`
- `abstract_text`
- `url`
- `canonical_url`
- `doi`
- `pmid`
- `nct_id`
- `citation_key`
- `dedupe_key`
- `published_at`
- `authors`
- `organizations`
- `topic_ids`
- `entity_tags`
- `relevance_scores`
- `raw_metadata`
- `created_at`
- `updated_at`

Notes:

- `raw_metadata` now carries discovery provenance such as ingest mode, connector, source URL, fixture path when relevant, and novelty score.
- `raw_metadata` also carries graph-entity matches used for graph views and graph-backed topic reinforcement, including concept-family metadata, match strategy, and related-match counts.

### `ResearchEvidenceRecord`

Stores cited evidence spans or claim anchors for research-intel documents.

Current fields:

- `id`
- `document_id`
- `evidence_text`
- `char_start`
- `char_end`
- `claim_text`
- `claim_type`
- `entity_tags`
- `citation_label`
- `confidence`
- `created_at`

### `ResearchTopicRecord`

Represents a rolling research-intel watchlist or cluster.

Current fields:

- `topic_id`
- `label`
- `description`
- `keywords`
- `related_rationale_codes`
- `related_trial_tags`
- `opportunity_types`
- `topic_heat`
- `document_count`
- `last_document_at`
- `status`
- `created_at`
- `updated_at`

### `ResearchDigestRecord`

Stores a generated pancreatic oncology digest plus the persisted council payload.

Current fields:

- `digest_id`
- `title`
- `status`
- `publication_scope`
- `window_start`
- `window_end`
- `generated_at`
- `topic_ids`
- `supporting_document_ids`
- `council_payload`
- `summary_markdown`
- `summary_json`
- `disagreement_score`
- `citation_count`
- `created_at`
- `updated_at`

### `ResearchOpportunityRecord`

Stores human-gated research-intel proposals tied to topics and cited documents.

Current fields:

- `opportunity_id`
- `opportunity_type`
- `title`
- `summary`
- `status`
- `confidence_score`
- `topic_ids`
- `supporting_document_ids`
- `related_rationale_codes`
- `related_trial_ids`
- `action_payload`
- `promotion_target`
- `promoted_at`
- `created_at`
- `updated_at`

`action_payload` is now a structured discovery-to-action bundle rather than a loose metadata dict. It includes:

- `objective`
- `why_now`
- `discovery_question`
- `artifact_spec`
- `evidence_bundle`
- `proposed_steps`
- `acceptance_gates`
- `open_questions`
- `evidence_gaps`
- `next_experiments`
- `measurable_outcomes`
- `promotion_guardrails`
- `suggested_target`
- `council_confidence`
- `council_personas`
- `theme_snapshot`
- `last_experiment`

`last_experiment` stores the latest safe experiment result for supported benchmark or rule opportunities, including:

- `experiment_kind`
- `ratchet_outcome`
- `metric_name`
- `baseline_value`
- `candidate_value`
- `delta`
- `threshold`
- `min_delta`
- `evidence_coverage_score`
- `notes`
- `artifact_paths`
- `run_id`
- `completed_at`

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

### Research-intel responses

Research-intel adds several derived API surfaces rather than a single monolithic blob:

- research source descriptors
- normalized research documents with cited evidence
- topic watchlists with heat and document counts
- council-backed digest summaries and disagreement metrics
- human-gated opportunities for benchmark, rule, trial, case-brief, and tooling work
- case-level research briefs that map current rationale codes and trial abstractions to relevant research topics

## Workflow values in active use

The current docs and UI should assume at least these workflow concepts are active:

- case statuses such as `new`, `in_review`, `escalated`, `dismissed`, and `closed`
- import-run statuses `completed` and `failed`
- import item statuses `imported` and `failed`
- import failure buckets `parse_error`, `validation_error`, `unsupported_payload`, and `site_scope_rejection`
- research-intel run types `ingest`, `digest`, and `experiment`
- research-intel opportunity types `rule_gap`, `benchmark_gap`, `trial_catalog_gap`, `case_brief`, `community_project`, and `external_tooling`
- research-intel opportunity statuses `proposed` and `promoted`

## Practical modeling rules

- Keep explainability close to the stored case and finding records.
- Keep cited evidence close to stored research documents, digests, and opportunities.
- Preserve provenance on reports even when an upstream payload is incomplete.
- Prefer explicit structured failure buckets over free-form import failure states.
- Treat review actions, feedback, import runs, and research-intel runs as separate but complementary audit surfaces.
