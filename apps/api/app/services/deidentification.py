from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass

from app.core.config import settings
from app.schemas.case import CaseDetail, CaseListItem
from app.schemas.research import (
    RedactionSummary,
    ResearchCaseDetail,
    ResearchImportMetadata,
    ResearchCaseListItem,
    ResearchEvidenceSpan,
    ResearchReviewAction,
    ResearchReviewerFeedbackRecord,
)
from app.schemas.triage import ImportMetadata


@dataclass(frozen=True)
class _PatternDef:
    category: str
    pattern: re.Pattern[str]
    group_index: int | None = None


@dataclass(frozen=True)
class TextRedaction:
    text: str
    redaction_count: int
    redacted_characters: int
    categories: dict[str, int]


_PATTERNS: tuple[_PatternDef, ...] = (
    _PatternDef(
        category="name",
        pattern=re.compile(
            r"\b(?:patient(?: name)?|name)\s*[:#]?\s*([A-Z][A-Za-z' -]+(?:\s+[A-Z][A-Za-z' -]+){0,3})\b",
            flags=re.IGNORECASE,
        ),
        group_index=1,
    ),
    _PatternDef(
        category="name",
        pattern=re.compile(
            r"\bpatient\s+([A-Z][A-Za-z' -]+(?:\s+[A-Z][A-Za-z' -]+){1,3})\b",
            flags=re.IGNORECASE,
        ),
        group_index=1,
    ),
    _PatternDef(
        category="name",
        pattern=re.compile(
            r"\b(?:call|contact|reached)\s+([A-Z][A-Za-z' -]+(?:\s+[A-Z][A-Za-z' -]+){1,3})\b",
            flags=re.IGNORECASE,
        ),
        group_index=1,
    ),
    _PatternDef(
        category="mrn",
        pattern=re.compile(
            r"\b(?:mrn|medical record(?: number)?|patient id|accession(?: number)?)\s*[:#]?\s*([A-Z0-9-]{4,})\b",
            flags=re.IGNORECASE,
        ),
        group_index=1,
    ),
    _PatternDef(
        category="dob",
        pattern=re.compile(
            r"\b(?:dob|date of birth)\s*[:#]?\s*([0-9]{1,4}[/-][0-9]{1,2}[/-][0-9]{1,4})\b",
            flags=re.IGNORECASE,
        ),
        group_index=1,
    ),
    _PatternDef(
        category="email",
        pattern=re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", flags=re.IGNORECASE),
    ),
    _PatternDef(
        category="phone",
        pattern=re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2}\d{4}\b"),
    ),
    _PatternDef(
        category="ssn",
        pattern=re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    ),
    _PatternDef(
        category="date",
        pattern=re.compile(
            r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|"
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4})\b",
            flags=re.IGNORECASE,
        ),
    ),
    _PatternDef(
        category="time",
        pattern=re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AP]M)?\b", flags=re.IGNORECASE),
    ),
    _PatternDef(
        category="doctor",
        pattern=re.compile(r"\bDr\.?\s+[A-Z][A-Za-z' -]+(?:\s+[A-Z][A-Za-z' -]+)?\b"),
    ),
    _PatternDef(
        category="identifier",
        pattern=re.compile(r"\b[A-Z]{1,4}-?\d{6,}\b"),
    ),
    _PatternDef(
        category="long_number",
        pattern=re.compile(r"\b\d{7,}\b"),
    ),
)


def deidentify_text(text: str) -> TextRedaction:
    if not text:
        return TextRedaction(text="", redaction_count=0, redacted_characters=0, categories={})

    chars = list(text)
    covered = [False] * len(text)
    counts: Counter[str] = Counter()
    redacted_characters = 0

    for pattern_def in _PATTERNS:
        for match in pattern_def.pattern.finditer(text):
            start, end = match.span(pattern_def.group_index or 0)
            if start >= end:
                continue
            if any(covered[index] for index in range(start, end)):
                continue
            for index in range(start, end):
                covered[index] = True
                replacement, did_redact = _mask_character(chars[index])
                chars[index] = replacement
                redacted_characters += int(did_redact)
            counts[pattern_def.category] += 1

    return TextRedaction(
        text="".join(chars),
        redaction_count=sum(counts.values()),
        redacted_characters=redacted_characters,
        categories=dict(counts),
    )


def pseudonymize_identifier(value: str | None, *, prefix: str) -> str | None:
    if not value:
        return None
    source = f"{settings.research_id_salt}:{prefix}:{value}".encode("utf-8")
    digest = hashlib.sha256(source).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _deidentify_import_metadata(
    metadata: ImportMetadata | None,
) -> tuple[ResearchImportMetadata | None, set[str]]:
    if metadata is None:
        return None, set()

    pseudonymized_fields: set[str] = set()
    if metadata.patient_identifier:
        pseudonymized_fields.add("import_metadata.patient_identifier")
    if metadata.encounter_identifier:
        pseudonymized_fields.add("import_metadata.encounter_identifier")
    if metadata.accession_number:
        pseudonymized_fields.add("import_metadata.accession_number")
    if metadata.ordering_provider:
        pseudonymized_fields.add("import_metadata.ordering_provider")
    if metadata.import_source_id:
        pseudonymized_fields.add("import_metadata.import_source_id")

    return (
        ResearchImportMetadata(
            patient_identifier=pseudonymize_identifier(metadata.patient_identifier, prefix="patient"),
            encounter_identifier=pseudonymize_identifier(metadata.encounter_identifier, prefix="encounter"),
            accession_number=pseudonymize_identifier(metadata.accession_number, prefix="accession"),
            ordering_provider=pseudonymize_identifier(metadata.ordering_provider, prefix="provider"),
            source_system=metadata.source_system,
            source_format=metadata.source_format,
            import_source_id=pseudonymize_identifier(metadata.import_source_id, prefix="source"),
        ),
        pseudonymized_fields,
    )


def deidentify_case_list_item(item: CaseListItem) -> ResearchCaseListItem:
    return ResearchCaseListItem(
        case_id=pseudonymize_identifier(item.case_id, prefix="case") or "",
        report_id=pseudonymize_identifier(item.report_id, prefix="report") or "",
        report_date=item.report_datetime.date() if item.report_datetime else None,
        modality=item.modality,
        score=item.score,
        urgency=item.urgency,
        status=item.status,
        site=item.site,
        assigned_to=pseudonymize_identifier(item.assigned_to, prefix="user"),
        top_rationale=item.top_rationale,
        hybrid_score=item.hybrid_score,
        hybrid_delta=item.hybrid_delta,
        hybrid_confidence=item.hybrid_confidence,
        hybrid_review_priority=item.hybrid_review_priority,
        active_learning_priority=item.active_learning_priority,
        disagreement_level=item.disagreement_level,
        review_feedback_count=item.review_feedback_count,
        latest_feedback_label=item.latest_feedback_label,
        latest_feedback_disposition=item.latest_feedback_disposition,
    )


def deidentify_case_detail(case: CaseDetail) -> ResearchCaseDetail:
    report_redaction = deidentify_text(case.report_text)
    pseudonymized_fields = {"case_id", "report_id"}
    review_redactions: list[TextRedaction] = [report_redaction]
    import_metadata, metadata_fields = _deidentify_import_metadata(case.import_metadata)
    pseudonymized_fields.update(metadata_fields)

    review_actions: list[ResearchReviewAction] = []
    for action in case.review_actions:
        note_redaction = deidentify_text(action.note or "")
        review_redactions.append(note_redaction)
        if action.assigned_to:
            pseudonymized_fields.add("assigned_to")
        pseudonymized_fields.add("review_actions.reviewer")
        review_actions.append(
            ResearchReviewAction(
                action=action.action,
                reviewer=pseudonymize_identifier(action.reviewer, prefix="user") or "user_unknown",
                note=note_redaction.text or None,
                assigned_to=pseudonymize_identifier(action.assigned_to, prefix="user"),
                created_date=action.created_at.date(),
            )
        )

    review_feedback: list[ResearchReviewerFeedbackRecord] = []
    for feedback in case.review_feedback:
        notes_redaction = deidentify_text(feedback.notes or "")
        review_redactions.append(notes_redaction)
        pseudonymized_fields.add("review_feedback.reviewer")
        review_feedback.append(
            ResearchReviewerFeedbackRecord(
                reviewer=pseudonymize_identifier(feedback.reviewer, prefix="user") or "user_unknown",
                label=feedback.label,
                disposition=feedback.disposition,
                error_bucket=feedback.error_bucket,
                notes=notes_redaction.text or None,
                created_date=feedback.created_at.date(),
            )
        )

    evidence: list[ResearchEvidenceSpan] = []
    for item in case.evidence:
        start = int(item["start"])
        end = int(item["end"])
        redacted_text = _slice_or_fallback(report_redaction.text, start, end, str(item["text"]))
        evidence.append(
            ResearchEvidenceSpan(
                text=redacted_text,
                section=str(item.get("section") or "unknown"),
                start=start,
                end=end,
                code=str(item["code"]),
                sentence_index=item.get("sentence_index"),
            )
        )

    if case.assigned_to:
        pseudonymized_fields.add("assigned_to")

    return ResearchCaseDetail(
        case_id=pseudonymize_identifier(case.case_id, prefix="case") or "",
        report_id=pseudonymize_identifier(case.report_id, prefix="report") or "",
        report_date=case.report_datetime.date() if case.report_datetime else None,
        modality=case.modality,
        score=case.score,
        urgency=case.urgency,
        status=case.status,
        site=case.site,
        assigned_to=pseudonymize_identifier(case.assigned_to, prefix="user"),
        report_text=report_redaction.text,
        import_metadata=import_metadata,
        rationale_codes=case.rationale_codes,
        evidence=evidence,
        review_actions=review_actions,
        review_feedback=review_feedback,
        redaction_summary=_summarize_redactions(review_redactions, pseudonymized_fields),
    )


def deidentify_case_export_row(row: dict[str, object]) -> dict[str, object]:
    redacted = dict(row)
    redacted["case_id"] = pseudonymize_identifier(_string_or_none(row.get("case_id")), prefix="case")
    redacted["report_id"] = pseudonymize_identifier(_string_or_none(row.get("report_id")), prefix="report")
    redacted["assigned_to"] = pseudonymize_identifier(_string_or_none(row.get("assigned_to")), prefix="user")
    redacted["patient_identifier"] = pseudonymize_identifier(
        _string_or_none(row.get("patient_identifier")),
        prefix="patient",
    )
    redacted["encounter_identifier"] = pseudonymize_identifier(
        _string_or_none(row.get("encounter_identifier")),
        prefix="encounter",
    )
    redacted["accession_number"] = pseudonymize_identifier(
        _string_or_none(row.get("accession_number")),
        prefix="accession",
    )
    redacted["ordering_provider"] = pseudonymize_identifier(
        _string_or_none(row.get("ordering_provider")),
        prefix="provider",
    )
    redacted["import_source_id"] = pseudonymize_identifier(
        _string_or_none(row.get("import_source_id")),
        prefix="source",
    )
    report_datetime = _string_or_none(row.get("report_datetime"))
    if report_datetime:
        redacted["report_datetime"] = report_datetime.split("T", 1)[0]
    redacted["deidentified"] = True
    return redacted


def deidentify_feedback_export_row(row: dict[str, object]) -> dict[str, object]:
    report_redaction = deidentify_text(_string_or_none(row.get("report_text")) or "")
    notes_redaction = deidentify_text(_string_or_none(row.get("notes")) or "")
    evidence_texts = [
        deidentify_text(str(item)).text
        for item in (row.get("evidence_texts") or [])
        if isinstance(item, str)
    ]

    redacted = dict(row)
    redacted["case_id"] = pseudonymize_identifier(_string_or_none(row.get("case_id")), prefix="case")
    redacted["report_id"] = pseudonymize_identifier(_string_or_none(row.get("report_id")), prefix="report")
    redacted["reviewer"] = pseudonymize_identifier(_string_or_none(row.get("reviewer")), prefix="user")
    redacted["patient_identifier"] = pseudonymize_identifier(
        _string_or_none(row.get("patient_identifier")),
        prefix="patient",
    )
    redacted["encounter_identifier"] = pseudonymize_identifier(
        _string_or_none(row.get("encounter_identifier")),
        prefix="encounter",
    )
    redacted["accession_number"] = pseudonymize_identifier(
        _string_or_none(row.get("accession_number")),
        prefix="accession",
    )
    redacted["ordering_provider"] = pseudonymize_identifier(
        _string_or_none(row.get("ordering_provider")),
        prefix="provider",
    )
    redacted["import_source_id"] = pseudonymize_identifier(
        _string_or_none(row.get("import_source_id")),
        prefix="source",
    )
    report_datetime = _string_or_none(row.get("report_datetime"))
    if report_datetime:
        redacted["report_datetime"] = report_datetime.split("T", 1)[0]
    created_at = _string_or_none(row.get("created_at"))
    if created_at:
        redacted["created_at"] = created_at.split("T", 1)[0]
    redacted["report_text"] = report_redaction.text
    redacted["evidence_texts"] = evidence_texts
    redacted["notes"] = notes_redaction.text or None
    redacted["deidentified"] = True
    pseudonymized_fields = {"case_id", "report_id", "reviewer"}
    if row.get("patient_identifier"):
        pseudonymized_fields.add("patient_identifier")
    if row.get("encounter_identifier"):
        pseudonymized_fields.add("encounter_identifier")
    if row.get("accession_number"):
        pseudonymized_fields.add("accession_number")
    if row.get("ordering_provider"):
        pseudonymized_fields.add("ordering_provider")
    if row.get("import_source_id"):
        pseudonymized_fields.add("import_source_id")
    redacted["redaction_summary"] = _summarize_redactions(
        [report_redaction, notes_redaction],
        pseudonymized_fields,
    ).model_dump(mode="json")
    return redacted


def _mask_character(char: str) -> tuple[str, bool]:
    if char.isalpha():
        return "X", True
    if char.isdigit():
        return "0", True
    return char, False


def _summarize_redactions(
    redactions: list[TextRedaction],
    pseudonymized_fields: set[str],
) -> RedactionSummary:
    counts: Counter[str] = Counter()
    total_count = 0
    total_characters = 0
    for redaction in redactions:
        counts.update(redaction.categories)
        total_count += redaction.redaction_count
        total_characters += redaction.redacted_characters
    return RedactionSummary(
        redaction_count=total_count,
        redacted_characters=total_characters,
        categories=dict(counts),
        pseudonymized_fields=sorted(pseudonymized_fields),
    )


def _slice_or_fallback(text: str, start: int, end: int, fallback: str) -> str:
    if 0 <= start < end <= len(text):
        return text[start:end]
    return deidentify_text(fallback).text


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None
