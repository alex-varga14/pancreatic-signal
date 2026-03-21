# Data model

## Case
Represents a logical patient episode or triage thread.

Fields:
- id
- external_case_id
- patient_key
- status
- urgency
- score
- assigned_to
- site
- created_at
- updated_at

## Report
Source radiology report.

Fields:
- id
- case_id
- report_id
- accession_number
- modality
- exam_description
- report_datetime
- raw_text
- normalized_text
- findings_text
- impression_text
- source_file
- created_at

## Finding
Structured output produced by triage engine.

Fields:
- id
- case_id
- report_id
- code
- label
- polarity
- certainty
- score_contribution
- evidence_text
- section
- char_start
- char_end
- sentence_index
- metadata_json

## ReviewAction
Human action taken on a case.

Fields:
- id
- case_id
- reviewer
- action
- note
- created_at
- metadata_json

## AuditEvent
System or user audit record.

Fields:
- id
- entity_type
- entity_id
- event_type
- actor
- payload_json
- created_at

## TrialCandidate (future)
Potential trial match for a case.

Fields:
- id
- case_id
- trial_id
- title
- source
- match_score
- rationale
- status
- created_at

## Suggested enums

### CaseStatus
- new
- in_review
- escalated
- dismissed
- closed

### ReviewActionType
- assign
- note
- escalate
- dismiss
- close
- reopen

### UrgencyBand
- low
- medium
- high
- critical
