from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass

from app.core.config import settings
from app.schemas.triage import ImportMetadata, ReportInput
from app.services.imports import ImportParseError
from app.services.text_utils import normalize_text

_MODALITY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("CT", re.compile(r"\b(ct|computed tomography)\b", flags=re.IGNORECASE)),
    ("MRI", re.compile(r"\b(mri|mr imaging|magnetic resonance)\b", flags=re.IGNORECASE)),
    ("US", re.compile(r"\b(us|ultrasound|sonography)\b", flags=re.IGNORECASE)),
    ("PET", re.compile(r"\b(pet|positron emission tomography)\b", flags=re.IGNORECASE)),
    ("EUS", re.compile(r"\b(eus|endoscopic ultrasound)\b", flags=re.IGNORECASE)),
    ("XR", re.compile(r"\b(x-?ray|radiograph)\b", flags=re.IGNORECASE)),
)
_HL7_PATIENT_IDENTIFIER_FIELD_ORDER = ("PID-3", "PID-2")
_HL7_SOURCE_SYSTEM_FIELD_ORDER = ("MSH-3", "MSH-4")


@dataclass(frozen=True)
class HL7Separators:
    field: str = "|"
    component: str = "^"
    repetition: str = "~"
    escape: str = "\\"
    subcomponent: str = "&"


def parse_hl7_oru_messages(message_text: str) -> list[ReportInput]:
    normalized = _normalize_hl7_text(message_text)
    if not normalized:
        raise ImportParseError("HL7 ORU import payload is empty.")

    messages = _split_messages(normalized)
    reports: list[ReportInput] = []
    for message_index, segments in enumerate(messages, start=1):
        reports.extend(_parse_message_segments(segments, message_index=message_index))

    if not reports:
        raise ImportParseError("HL7 ORU import did not contain any OBR report groups.")
    return reports


def _normalize_hl7_text(message_text: str) -> str:
    return (
        message_text.replace("\x0b", "")
        .replace("\x1c", "")
        .replace("\r\n", "\r")
        .replace("\n", "\r")
        .strip("\r\n\t ")
    )


def _split_messages(normalized_text: str) -> list[list[str]]:
    messages: list[list[str]] = []
    current: list[str] = []

    for raw_segment in normalized_text.split("\r"):
        segment = raw_segment.strip()
        if not segment:
            continue
        if segment.startswith("MSH"):
            if current:
                messages.append(current)
            current = [segment]
            continue
        if not current:
            raise ImportParseError("HL7 ORU import must start with an MSH segment.")
        current.append(segment)

    if current:
        messages.append(current)
    return messages


def _parse_message_segments(segments: list[str], *, message_index: int) -> list[ReportInput]:
    if not segments or not segments[0].startswith("MSH"):
        raise ImportParseError(f"HL7 message {message_index} is missing an MSH segment.")

    field_separator = segments[0][3] if len(segments[0]) > 3 else "|"
    parsed = [_split_segment(segment, field_separator) for segment in segments]
    msh = parsed[0]
    separators = _message_separators(msh, field_separator)

    message_type = _segment_field(msh, 9)
    primary_message_type = _component(message_type, 1, separators=separators) or message_type
    if primary_message_type.upper() != "ORU":
        raise ImportParseError(
            f"HL7 message {message_index} is not an ORU result message (found '{message_type or 'unknown'}')."
        )

    message_control_id = _segment_field(msh, 10)
    message_datetime = _segment_field(msh, 7)
    sending_application = _segment_field(msh, 3)
    sending_facility = _component(_segment_field(msh, 4), 1, separators=separators)

    pid: list[str] | None = None
    pv1: list[str] | None = None
    reports: list[ReportInput] = []
    current_obr: list[str] | None = None
    current_obx: list[list[str]] = []
    current_nte: list[list[str]] = []

    def finalize_group() -> None:
        nonlocal current_obr, current_obx, current_nte
        if current_obr is None:
            return
        reports.append(
            _build_report_input(
                current_obr,
                obx_segments=current_obx,
                nte_segments=current_nte,
                pid_segment=pid,
                pv1_segment=pv1,
                sending_application=sending_application,
                sending_facility=sending_facility,
                message_datetime=message_datetime,
                message_control_id=message_control_id,
                group_index=len(reports) + 1,
                separators=separators,
            )
        )
        current_obr = None
        current_obx = []
        current_nte = []

    for segment in parsed[1:]:
        segment_type = segment[0] if segment else ""
        if segment_type == "PID":
            pid = segment
            continue
        if segment_type == "PV1":
            pv1 = segment
            continue
        if segment_type == "OBR":
            finalize_group()
            current_obr = segment
            continue
        if segment_type == "OBX" and current_obr is not None:
            current_obx.append(segment)
            continue
        if segment_type == "NTE" and current_obr is not None:
            current_nte.append(segment)

    finalize_group()
    return reports


def _build_report_input(
    obr_segment: list[str],
    *,
    obx_segments: list[list[str]],
    nte_segments: list[list[str]],
    pid_segment: list[str] | None,
    pv1_segment: list[str] | None,
    sending_application: str | None,
    sending_facility: str | None,
    message_datetime: str | None,
    message_control_id: str | None,
    group_index: int,
    separators: HL7Separators,
) -> ReportInput:
    report_id = _first_non_empty(
        _repeat_component(_segment_field(obr_segment, 3), 1, separators=separators),
        _repeat_component(_segment_field(obr_segment, 2), 1, separators=separators),
        _with_group_suffix(message_control_id, group_index),
    )
    if not report_id:
        raise ImportParseError("HL7 ORU report group is missing OBR-3 / OBR-2 identifiers.")

    report_datetime = _first_non_empty(
        _segment_field(obr_segment, 7),
        _segment_field(obr_segment, 22),
        message_datetime,
    )
    if not report_datetime:
        raise ImportParseError(f"HL7 ORU report '{report_id}' is missing OBR-7, OBR-22, or MSH-7 timestamp.")

    site = _first_non_empty(_pv1_site(pv1_segment, separators=separators), sending_facility)
    modality = _infer_modality(
        _first_non_empty(_segment_field(obr_segment, 24), _segment_field(obr_segment, 4)) or ""
    )
    report_text = _build_report_text(obx_segments, nte_segments, separators=separators)
    if not report_text:
        raise ImportParseError(f"HL7 ORU report '{report_id}' did not contain any OBX or NTE report text.")

    import_metadata = _build_import_metadata(
        obr_segment,
        pid_segment=pid_segment,
        pv1_segment=pv1_segment,
        sending_application=sending_application,
        sending_facility=sending_facility,
        message_control_id=message_control_id,
        group_index=group_index,
        separators=separators,
    )

    return ReportInput.model_validate(
        {
            "report_id": report_id,
            "case_id": report_id,
            "report_datetime": report_datetime,
            "modality": modality,
            "site": site,
            "report_text": report_text,
            "import_metadata": import_metadata.model_dump(),
        }
    )


def _build_report_text(
    obx_segments: list[list[str]],
    nte_segments: list[list[str]],
    *,
    separators: HL7Separators,
) -> str:
    findings: list[str] = []
    impression: list[str] = []
    other: list[str] = []

    for obx in obx_segments:
        text = _obx_text(obx, separators=separators)
        if not text:
            continue
        observation_label = _first_non_empty(
            _component(_segment_field(obx, 3), 2, separators=separators),
            _component(_segment_field(obx, 3), 1, separators=separators),
        ) or ""
        label_l = observation_label.lower()
        text_l = text.lower()

        if "impression" in label_l or "conclusion" in label_l or text_l.startswith("impression:"):
            impression.append(text.removeprefix("Impression: ").removeprefix("impression: ").strip())
        elif "finding" in label_l or "result" in label_l or text_l.startswith("findings:"):
            findings.append(text.removeprefix("Findings: ").removeprefix("findings: ").strip())
        else:
            other.append(text)

    note_texts = [_segment_field(nte, 3) for nte in nte_segments if _segment_field(nte, 3)]
    sections: list[str] = []

    findings_block = " ".join(item for item in [*findings, *other] if item)
    if findings_block:
        sections.append(f"Findings: {findings_block}")

    impression_block = " ".join(item for item in [*impression, *note_texts] if item)
    if impression_block:
        sections.append(f"Impression: {impression_block}")
    elif note_texts:
        sections.append(f"Report: {' '.join(note_texts)}")

    return normalize_text(" ".join(sections))


def _obx_text(obx_segment: list[str], *, separators: HL7Separators) -> str:
    value_type = _segment_field(obx_segment, 2).upper()
    raw_value = _segment_field(obx_segment, 5)
    if not raw_value:
        return ""

    if value_type == "ED":
        return " ".join(
            item
            for item in (_ed_text(repeat, separators=separators) for repeat in _value_repeats(raw_value, separators=separators))
            if item
        )
    if value_type in {"CE", "CWE"}:
        return " ".join(
            item
            for item in (
                (
                    _component(repeat, 2, separators=separators)
                    or _component(repeat, 1, separators=separators)
                    or ""
                )
                for repeat in _value_repeats(raw_value, separators=separators)
            )
            if item
        )
    return " ".join(item for item in _value_repeats(raw_value, separators=separators) if item)


def _ed_text(value: str, *, separators: HL7Separators) -> str:
    components = [item.strip() for item in value.split(separators.component)]
    if len(components) < 5:
        return ""

    encoding = components[3].lower()
    data = components[4].strip()
    if not data:
        return ""

    if encoding in {"", "a"}:
        return data
    if encoding in {"base64", "b64"}:
        try:
            return base64.b64decode(data, validate=False).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            return ""
    return data


def _value_repeats(value: str, separators: HL7Separators) -> list[str]:
    return [item.strip() for item in value.split(separators.repetition) if item.strip()]


def _pv1_site(pv1_segment: list[str] | None, *, separators: HL7Separators) -> str | None:
    if pv1_segment is None:
        return None
    location = _segment_field(pv1_segment, 3)
    return _first_non_empty(
        _component(location, 4, separators=separators),
        _component(location, 1, separators=separators),
    )


def _infer_modality(text: str) -> str:
    for modality, pattern in _MODALITY_PATTERNS:
        if pattern.search(text):
            return modality
    return "Imaging"


def _build_import_metadata(
    obr_segment: list[str],
    *,
    pid_segment: list[str] | None,
    pv1_segment: list[str] | None,
    sending_application: str | None,
    sending_facility: str | None,
    message_control_id: str | None,
    group_index: int,
    separators: HL7Separators,
) -> ImportMetadata:
    patient_identifier_candidates = {
        "PID-3": _repeat_component(_segment_field(pid_segment or [], 3), 1, separators=separators),
        "PID-2": _repeat_component(_segment_field(pid_segment or [], 2), 1, separators=separators),
    }
    source_system_candidates = {
        "MSH-3": _repeat_component(sending_application or "", 1, separators=separators),
        "MSH-4": sending_facility,
    }
    return ImportMetadata(
        patient_identifier=_select_configured_candidate(
            configured_order=settings.hl7_patient_identifier_field_order_list,
            default_order=_HL7_PATIENT_IDENTIFIER_FIELD_ORDER,
            candidates=patient_identifier_candidates,
        ),
        encounter_identifier=_first_non_empty(
            _repeat_component(_segment_field(pv1_segment or [], 19), 1, separators=separators),
            _repeat_component(_segment_field(pv1_segment or [], 50), 1, separators=separators),
        ),
        accession_number=_first_non_empty(
            _repeat_component(_segment_field(obr_segment, 18), 1, separators=separators),
            _repeat_component(_segment_field(obr_segment, 3), 1, separators=separators),
            _repeat_component(_segment_field(obr_segment, 2), 1, separators=separators),
        ),
        ordering_provider=_xcn_display(_segment_field(obr_segment, 16), separators=separators),
        source_system=_select_configured_candidate(
            configured_order=settings.hl7_source_system_field_order_list,
            default_order=_HL7_SOURCE_SYSTEM_FIELD_ORDER,
            candidates=source_system_candidates,
        ),
        source_format="hl7-oru",
        import_source_id=_first_non_empty(
            _with_group_suffix(message_control_id, group_index),
            _repeat_component(_segment_field(obr_segment, 3), 1, separators=separators),
        ),
    )


def _split_segment(segment: str, field_separator: str) -> list[str]:
    return segment.split(field_separator)


def _message_separators(msh_segment: list[str], field_separator: str) -> HL7Separators:
    encoding_characters = _segment_field(msh_segment, 2)
    return HL7Separators(
        field=field_separator,
        component=encoding_characters[0] if len(encoding_characters) >= 1 else "^",
        repetition=encoding_characters[1] if len(encoding_characters) >= 2 else "~",
        escape=encoding_characters[2] if len(encoding_characters) >= 3 else "\\",
        subcomponent=encoding_characters[3] if len(encoding_characters) >= 4 else "&",
    )


def _segment_field(segment: list[str], field_number: int) -> str:
    if not segment:
        return ""
    if segment[0] == "MSH":
        if field_number == 1:
            return "|"
        index = field_number - 1
    else:
        index = field_number
    if index < len(segment):
        return segment[index].strip()
    return ""


def _component(value: str, position: int, *, separators: HL7Separators) -> str | None:
    if not value:
        return None
    parts = [item.strip() for item in value.split(separators.component)]
    index = position - 1
    if 0 <= index < len(parts):
        return parts[index] or None
    return None


def _first_repeat(value: str, *, separators: HL7Separators) -> str:
    if not value:
        return ""
    return value.split(separators.repetition, 1)[0].strip()


def _repeat_component(value: str, position: int, *, separators: HL7Separators) -> str | None:
    return _component(_first_repeat(value, separators=separators), position, separators=separators)


def _xcn_display(value: str, *, separators: HL7Separators) -> str | None:
    first_repeat = _first_repeat(value, separators=separators)
    family = _component(first_repeat, 2, separators=separators)
    given = _component(first_repeat, 3, separators=separators)
    if family and given:
        return f"{given} {family}"
    return _first_non_empty(family, given, _component(first_repeat, 1, separators=separators))


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value
    return None


def _with_group_suffix(value: str | None, group_index: int) -> str | None:
    if not value:
        return None
    if group_index == 1:
        return value
    return f"{value}-{group_index}"


def _select_configured_candidate(
    *,
    configured_order: list[str],
    default_order: tuple[str, ...],
    candidates: dict[str, str | None],
) -> str | None:
    order = [item for item in configured_order if item in default_order] or list(default_order)
    for key in order:
        value = candidates.get(key)
        if value:
            return value
    return None
