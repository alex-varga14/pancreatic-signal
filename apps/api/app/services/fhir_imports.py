from __future__ import annotations

import base64
import binascii
import html
import re
from typing import Any

from app.core.config import settings
from app.schemas.triage import ImportMetadata, ReportInput
from app.services.imports import ImportParseError
from app.services.text_utils import normalize_text

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_REPORT_SECTION_RE = re.compile(
    r"\b(clinical history|history|technique|findings|impression|conclusion|report)\s*:",
    flags=re.IGNORECASE,
)
_MODALITY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("CT", re.compile(r"\b(ct|computed tomography)\b", flags=re.IGNORECASE)),
    ("MRI", re.compile(r"\b(mri|mr imaging|magnetic resonance)\b", flags=re.IGNORECASE)),
    ("US", re.compile(r"\b(us|ultrasound|sonography)\b", flags=re.IGNORECASE)),
    ("PET", re.compile(r"\b(pet|positron emission tomography)\b", flags=re.IGNORECASE)),
    ("EUS", re.compile(r"\b(eus|endoscopic ultrasound)\b", flags=re.IGNORECASE)),
    ("XR", re.compile(r"\b(x-?ray|radiograph)\b", flags=re.IGNORECASE)),
)
_FHIR_REFERENCE_IDENTIFIER_SOURCE_ORDER = (
    "resolved_identifier",
    "reference_identifier",
    "resolved_id",
    "reference_tail",
)
_FHIR_SOURCE_SYSTEM_SOURCE_ORDER = (
    "meta_source",
    "performer",
    "results_interpreter",
    "encounter_service_provider",
)
_FHIR_ACCESSION_SOURCE_ORDER = (
    "report_identifier_typed",
    "based_on_identifier_typed",
    "based_on_reference_identifier_typed",
    "report_identifier",
    "based_on_identifier",
    "based_on_reference_identifier",
)
_FHIR_PRESENTED_FORM_TEXT_MEDIA_TYPES = {
    "application/xhtml+xml",
    "application/xml",
    "text/xml",
}
_FHIR_PRESENTED_FORM_TEXT_ENCODINGS = (
    "utf-8",
    "utf-8-sig",
    "utf-16",
    "utf-16le",
    "utf-16be",
    "cp1252",
)


def parse_fhir_diagnostic_report_payload(payload: object) -> list[ReportInput]:
    if isinstance(payload, list):
        resources = payload
        resource_index = _build_resource_index(resources)
        reports = [
            _diagnostic_report_to_report_input(item, resource_index=resource_index)
            for item in resources
            if _resource_type(item) == "DiagnosticReport"
        ]
        if not reports:
            raise ImportParseError("FHIR import payload did not contain any DiagnosticReport resources.")
        return reports

    if not isinstance(payload, dict):
        raise ImportParseError("FHIR import payload must be a DiagnosticReport resource or Bundle.")

    resource_type = _resource_type(payload)
    if resource_type == "DiagnosticReport":
        resource_index = _build_resource_index([payload])
        return [_diagnostic_report_to_report_input(payload, resource_index=resource_index)]

    if resource_type == "Bundle":
        entries = payload.get("entry")
        if not isinstance(entries, list):
            raise ImportParseError("FHIR Bundle import requires an 'entry' array.")
        resources = [entry.get("resource") for entry in entries if isinstance(entry, dict)]
        resource_index = _build_resource_index(resources, entries=entries)
        reports = [
            _diagnostic_report_to_report_input(item, resource_index=resource_index)
            for item in resources
            if _resource_type(item) == "DiagnosticReport"
        ]
        if not reports:
            raise ImportParseError("FHIR Bundle did not contain any DiagnosticReport resources.")
        return reports

    raise ImportParseError("FHIR import payload must be a DiagnosticReport resource or Bundle.")


def _diagnostic_report_to_report_input(
    resource: object,
    *,
    resource_index: dict[str, dict[str, Any]],
) -> ReportInput:
    if not isinstance(resource, dict):
        raise ImportParseError("DiagnosticReport resource must be a JSON object.")

    report_id = _first_non_empty(
        _extract_identifier_value(resource.get("identifier")),
        _string_value(resource.get("id")),
    )
    if not report_id:
        raise ImportParseError("DiagnosticReport import requires an 'id' or identifier value.")

    report_datetime = _first_non_empty(
        _string_value(resource.get("effectiveDateTime")),
        _string_value(resource.get("issued")),
        _nested_string_value(resource, "meta", "lastUpdated"),
    )
    if not report_datetime:
        raise ImportParseError(f"DiagnosticReport '{report_id}' is missing effectiveDateTime, issued, or meta.lastUpdated.")

    modality = _infer_modality(resource)
    site = _extract_site(resource, resource_index=resource_index)
    report_text = _build_report_text(resource, resource_index=resource_index)
    import_metadata = _build_import_metadata(resource, resource_index=resource_index)
    if not report_text:
        raise ImportParseError(f"DiagnosticReport '{report_id}' does not contain narrative, findings, or conclusion text.")

    return ReportInput.model_validate(
        {
            "report_id": report_id,
            "case_id": report_id,
            "report_datetime": report_datetime,
            "modality": modality,
            "site": site,
            "report_text": report_text,
            "import_metadata": import_metadata.model_dump() if import_metadata is not None else None,
        }
    )


def _build_resource_index(
    resources: list[object],
    *,
    entries: list[object] | None = None,
) -> dict[str, dict[str, Any]]:
    resource_index: dict[str, dict[str, Any]] = {}

    for item in resources:
        if not isinstance(item, dict):
            continue
        _index_resource(resource_index, item)

    for item in entries or []:
        if not isinstance(item, dict):
            continue
        resource = item.get("resource")
        full_url = item.get("fullUrl")
        if isinstance(full_url, str) and isinstance(resource, dict):
            resource_index[full_url] = resource

    return resource_index


def _index_resource(resource_index: dict[str, dict[str, Any]], resource: dict[str, Any]) -> None:
    resource_type = _resource_type(resource)
    resource_id = _string_value(resource.get("id"))
    if resource_type and resource_id:
        resource_index[f"{resource_type}/{resource_id}"] = resource
        resource_index[resource_id] = resource

    contained = resource.get("contained")
    if isinstance(contained, list):
        for item in contained:
            if not isinstance(item, dict):
                continue
            contained_id = _string_value(item.get("id"))
            contained_type = _resource_type(item)
            if contained_id:
                resource_index[f"#{contained_id}"] = item
            if contained_type and contained_id:
                resource_index[f"{contained_type}/{contained_id}"] = item


def _build_report_text(resource: dict[str, Any], *, resource_index: dict[str, dict[str, Any]]) -> str:
    presented_form_text = _extract_presented_form_text(resource.get("presentedForm"), resource_index=resource_index)
    findings = _extract_findings_text(resource, resource_index=resource_index)
    if presented_form_text and _text_matches(presented_form_text, findings):
        presented_form_text = ""

    if findings:
        sections = [f"Findings: {findings}"]
    else:
        sections = []

    conclusion = _extract_conclusion_text(resource)
    if presented_form_text and _text_matches(presented_form_text, conclusion):
        presented_form_text = ""
    if presented_form_text and _looks_like_sectioned_report(presented_form_text):
        return normalize_text(presented_form_text)
    if presented_form_text and not findings and conclusion:
        sections.append(f"Findings: {presented_form_text}")

    if conclusion:
        label = "Impression" if sections else "Report"
        sections.append(f"{label}: {conclusion}")
    elif presented_form_text and not sections:
        sections.append(f"Report: {presented_form_text}")

    combined = " ".join(item for item in sections if item)
    return normalize_text(combined)


def _extract_findings_text(resource: dict[str, Any], *, resource_index: dict[str, dict[str, Any]]) -> str:
    findings: list[str] = []
    results = resource.get("result")
    if isinstance(results, list):
        for item in results:
            observation = _resolve_reference_resource(item, resource_index=resource_index)
            text = _observation_to_text(observation, resource_index=resource_index)
            if text:
                findings.append(text)

    if findings:
        return " ".join(findings)

    code_text = _codeable_concept_text(resource.get("code"))
    if code_text and code_text.lower() != "diagnostic report":
        return code_text
    return ""


def _observation_to_text(
    resource: dict[str, Any] | None,
    *,
    resource_index: dict[str, dict[str, Any]],
    seen_observations: set[str] | None = None,
) -> str:
    if not resource:
        return ""

    observation_identity = _resource_identity(resource)
    next_seen = set(seen_observations or set())
    if observation_identity:
        if observation_identity in next_seen:
            return ""
        next_seen.add(observation_identity)

    narrative = _extract_narrative_text(resource)
    if narrative:
        return _ensure_sentence(narrative)

    component_text = _observation_component_text(resource)
    member_text = _observation_member_text(
        resource,
        resource_index=resource_index,
        seen_observations=next_seen,
    )
    direct_text = _observation_direct_text(
        resource,
        include_label_only=not (component_text or member_text),
    )
    detail_fragments: list[str] = []
    _append_unique_fragment(detail_fragments, direct_text)
    _append_unique_fragment(detail_fragments, component_text)
    _append_unique_fragment(detail_fragments, member_text)
    detail_text = " ".join(item for item in detail_fragments if item)

    if detail_text:
        return detail_text
    return _ensure_sentence(_codeable_concept_text(resource.get("code")))


def _observation_direct_text(resource: dict[str, Any], *, include_label_only: bool = True) -> str:
    label = _codeable_concept_text(resource.get("code"))
    value = _observation_value_text(resource)
    interpretation = _observation_interpretation_text(resource.get("interpretation"))
    reference_range = _observation_reference_range_text(resource.get("referenceRange"))

    fragments: list[str] = []
    if label and value:
        fragments.append(_ensure_sentence(f"{label}: {value}"))
    elif value:
        fragments.append(_ensure_sentence(value))
    elif include_label_only and label and not interpretation and not reference_range:
        fragments.append(_ensure_sentence(label))

    _append_unique_fragment(fragments, interpretation)
    _append_unique_fragment(fragments, reference_range)
    return " ".join(item for item in fragments if item)


def _observation_value_text(resource: dict[str, Any]) -> str:
    boolean_value = resource.get("valueBoolean")
    if isinstance(boolean_value, bool):
        return "present" if boolean_value else "absent"

    integer_value = resource.get("valueInteger")
    if isinstance(integer_value, int) and not isinstance(integer_value, bool):
        return str(integer_value)

    return _first_non_empty(
        _string_value(resource.get("valueString")),
        _codeable_concept_text(resource.get("valueCodeableConcept")),
        _quantity_text(resource.get("valueQuantity")),
        _range_text(resource.get("valueRange")),
        _ratio_text(resource.get("valueRatio")),
        _string_value(resource.get("valueDateTime")),
        _period_text(resource.get("valuePeriod")),
        _note_text(resource.get("note")),
    ) or ""


def _observation_component_text(resource: dict[str, Any]) -> str:
    components = resource.get("component")
    if not isinstance(components, list):
        return ""

    component_texts: list[str] = []
    for item in components:
        if not isinstance(item, dict):
            continue
        _append_unique_fragment(component_texts, _observation_direct_text(item))

    return " ".join(item for item in component_texts if item)


def _observation_member_text(
    resource: dict[str, Any],
    *,
    resource_index: dict[str, dict[str, Any]],
    seen_observations: set[str],
) -> str:
    members = resource.get("hasMember")
    if not isinstance(members, list):
        return ""

    member_texts: list[str] = []
    for item in members:
        observation = _resolve_reference_resource(item, resource_index=resource_index)
        text = _observation_to_text(
            observation,
            resource_index=resource_index,
            seen_observations=seen_observations,
        )
        _append_unique_fragment(member_texts, text)

    return " ".join(item for item in member_texts if item)


def _extract_site(resource: dict[str, Any], *, resource_index: dict[str, dict[str, Any]]) -> str | None:
    for field_name in ("performer", "resultsInterpreter"):
        values = resource.get(field_name)
        if not isinstance(values, list):
            continue
        for item in values:
            display = _reference_display(item, resource_index=resource_index)
            if display:
                return display

    encounter = _resolve_reference_resource(resource.get("encounter"), resource_index=resource_index)
    if encounter is not None:
        service_provider = encounter.get("serviceProvider")
        display = _reference_display(service_provider, resource_index=resource_index)
        if display:
            return display

    return None


def _build_import_metadata(
    resource: dict[str, Any],
    *,
    resource_index: dict[str, dict[str, Any]],
) -> ImportMetadata:
    return ImportMetadata(
        patient_identifier=_extract_reference_identifier(resource.get("subject"), resource_index=resource_index),
        encounter_identifier=_extract_reference_identifier(resource.get("encounter"), resource_index=resource_index),
        accession_number=_extract_accession_number(resource, resource_index=resource_index),
        ordering_provider=_extract_ordering_provider(resource, resource_index=resource_index),
        source_system=_extract_source_system(resource, resource_index=resource_index),
        source_format="fhir-diagnostic-report",
        import_source_id=_extract_import_source_id(resource),
    )


def _extract_conclusion_text(resource: dict[str, Any]) -> str:
    return (
        _string_value(resource.get("conclusion"))
        or _codeable_concept_text(resource.get("conclusionCode"))
        or _extract_narrative_text(resource)
    )


def _infer_modality(resource: dict[str, Any]) -> str:
    search_space = " ".join(
        item
        for item in (
            _codeable_concept_text(resource.get("category")),
            _codeable_concept_text(resource.get("code")),
            _extract_narrative_text(resource),
        )
        if item
    )
    for modality, pattern in _MODALITY_PATTERNS:
        if pattern.search(search_space):
            return modality
    return "Imaging"


def _extract_reference_identifier(
    value: object,
    *,
    resource_index: dict[str, dict[str, Any]],
) -> str | None:
    if not isinstance(value, dict):
        return None

    resource = _resolve_reference_resource(value, resource_index=resource_index)
    reference = _string_value(value.get("reference"))
    reference_tail = None
    if reference:
        reference_tail = reference.rsplit("/", 1)[-1] if "/" in reference else reference.removeprefix("#")

    candidates = {
        "resolved_identifier": (
            _extract_identifier_value(resource.get("identifier"))
            if resource is not None
            else None
        ),
        "reference_identifier": _extract_identifier_value(value.get("identifier")),
        "resolved_id": _string_value(resource.get("id")) if resource is not None else None,
        "reference_tail": reference_tail,
    }
    return _select_configured_candidate(
        configured_order=settings.fhir_reference_identifier_source_order_list,
        default_order=_FHIR_REFERENCE_IDENTIFIER_SOURCE_ORDER,
        candidates=candidates,
    )


def _extract_accession_number(resource: dict[str, Any], *, resource_index: dict[str, dict[str, Any]]) -> str | None:
    based_on_references = _based_on_reference_values(resource)
    based_on_resources = _based_on_resources(resource, resource_index=resource_index)
    candidates = {
        "report_identifier_typed": _extract_typed_identifier_value(
            resource.get("identifier"),
            patterns=("accession", "acsn"),
        ),
        "based_on_identifier_typed": _first_non_empty(
            *[
                _extract_typed_identifier_value(item.get("identifier"), patterns=("accession", "acsn"))
                for item in based_on_resources
            ]
        ),
        "based_on_reference_identifier_typed": _first_non_empty(
            *[
                _extract_typed_identifier_value(item.get("identifier"), patterns=("accession", "acsn"))
                for item in based_on_references
            ]
        ),
        "report_identifier": _extract_identifier_value(resource.get("identifier")),
        "based_on_identifier": _first_non_empty(
            *[_extract_identifier_value(item.get("identifier")) for item in based_on_resources]
        ),
        "based_on_reference_identifier": _first_non_empty(
            *[_extract_identifier_value(item.get("identifier")) for item in based_on_references]
        ),
    }
    return _select_configured_candidate(
        configured_order=settings.fhir_accession_source_order_list,
        default_order=_FHIR_ACCESSION_SOURCE_ORDER,
        candidates=candidates,
    )


def _extract_ordering_provider(
    resource: dict[str, Any],
    *,
    resource_index: dict[str, dict[str, Any]],
) -> str | None:
    for service_request in _based_on_resources(resource, resource_index=resource_index):
        requester = _reference_value_display(service_request.get("requester"), resource_index=resource_index)
        if requester:
            return requester

        performer = _reference_value_display(service_request.get("performer"), resource_index=resource_index)
        if performer:
            return performer

    return None


def _extract_source_system(
    resource: dict[str, Any],
    *,
    resource_index: dict[str, dict[str, Any]],
) -> str | None:
    encounter = _resolve_reference_resource(resource.get("encounter"), resource_index=resource_index)
    candidates = {
        "meta_source": _nested_string_value(resource, "meta", "source"),
        "performer": _reference_value_display(resource.get("performer"), resource_index=resource_index),
        "results_interpreter": _reference_value_display(
            resource.get("resultsInterpreter"),
            resource_index=resource_index,
        ),
        "encounter_service_provider": (
            _reference_display(encounter.get("serviceProvider"), resource_index=resource_index)
            if encounter is not None
            else None
        ),
    }
    return _select_configured_candidate(
        configured_order=settings.fhir_source_system_source_order_list,
        default_order=_FHIR_SOURCE_SYSTEM_SOURCE_ORDER,
        candidates=candidates,
    )


def _extract_import_source_id(resource: dict[str, Any]) -> str | None:
    resource_id = _string_value(resource.get("id"))
    if resource_id:
        return f"DiagnosticReport/{resource_id}"
    return _extract_identifier_value(resource.get("identifier"))


def _based_on_resources(
    resource: dict[str, Any],
    *,
    resource_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    items = _based_on_reference_values(resource)
    resolved: list[dict[str, Any]] = []
    for item in items:
        service_request = _resolve_reference_resource(item, resource_index=resource_index)
        if service_request is not None:
            resolved.append(service_request)
    return resolved


def _based_on_reference_values(resource: dict[str, Any]) -> list[dict[str, Any]]:
    items = resource.get("basedOn")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _reference_value_display(
    value: object,
    *,
    resource_index: dict[str, dict[str, Any]],
) -> str | None:
    if isinstance(value, list):
        for item in value:
            display = _reference_display(item, resource_index=resource_index)
            if display:
                return display
        return None
    return _reference_display(value, resource_index=resource_index)


def _extract_presented_form_text(
    value: object,
    *,
    resource_index: dict[str, dict[str, Any]],
) -> str:
    if not isinstance(value, list):
        return ""

    fragments: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        decoded = _extract_presented_form_attachment_text(item, resource_index=resource_index)
        if decoded:
            _append_presented_form_fragment(fragments, decoded)

    if not fragments:
        return ""
    return normalize_text(" ".join(fragments))


def _extract_presented_form_attachment_text(
    value: dict[str, Any],
    *,
    resource_index: dict[str, dict[str, Any]],
) -> str:
    media_type, charset = _parse_attachment_content_type(_string_value(value.get("contentType")))

    raw_data = _string_value(value.get("data"))
    if raw_data:
        return _decode_presented_form_attachment_data(raw_data, media_type=media_type, charset=charset)

    inline_text = _string_value(value.get("text"))
    if inline_text and (not media_type or _is_supported_presented_form_media_type(media_type)):
        return inline_text

    attachment_url = _string_value(value.get("url"))
    if not attachment_url:
        return ""

    binary_resource = resource_index.get(attachment_url)
    if _resource_type(binary_resource) != "Binary":
        return ""

    binary_media_type, binary_charset = _parse_attachment_content_type(
        _string_value(binary_resource.get("contentType"))
    )
    effective_media_type = binary_media_type or media_type
    effective_charset = binary_charset or charset

    binary_data = _string_value(binary_resource.get("data"))
    if binary_data:
        return _decode_presented_form_attachment_data(
            binary_data,
            media_type=effective_media_type,
            charset=effective_charset,
        )

    return ""


def _decode_presented_form_attachment_data(raw_data: str, *, media_type: str, charset: str | None) -> str:
    if media_type and not _is_supported_presented_form_media_type(media_type):
        return ""

    try:
        raw_bytes = base64.b64decode(raw_data, validate=False)
    except binascii.Error:
        return ""

    return _decode_presented_form_bytes(raw_bytes, charset=charset)


def _append_presented_form_fragment(fragments: list[str], value: str) -> None:
    _append_unique_fragment(fragments, value)


def _append_unique_fragment(fragments: list[str], value: str) -> None:
    cleaned = _cleanup_text(value)
    if not cleaned:
        return

    cleaned_cf = cleaned.casefold()
    updated_fragments: list[str] = []
    for existing in fragments:
        existing_cf = existing.casefold()
        if cleaned_cf in existing_cf:
            return
        if existing_cf in cleaned_cf:
            continue
        updated_fragments.append(existing)

    updated_fragments.append(cleaned)
    fragments[:] = updated_fragments


def _parse_attachment_content_type(value: str | None) -> tuple[str, str | None]:
    if not value:
        return "", None

    parts = [item.strip() for item in value.split(";") if item.strip()]
    if not parts:
        return "", None

    media_type = parts[0].lower()
    charset = None
    for item in parts[1:]:
        if "=" not in item:
            continue
        key, raw_value = item.split("=", 1)
        if key.strip().lower() != "charset":
            continue
        charset = raw_value.strip().strip('"').lower() or None
        break

    return media_type, charset


def _is_supported_presented_form_media_type(media_type: str) -> bool:
    return media_type.startswith("text/") or media_type in _FHIR_PRESENTED_FORM_TEXT_MEDIA_TYPES


def _decode_presented_form_bytes(raw_bytes: bytes, *, charset: str | None) -> str:
    if not raw_bytes:
        return ""

    encodings: list[str] = []
    if charset:
        encodings.append(charset)
    encodings.extend(_FHIR_PRESENTED_FORM_TEXT_ENCODINGS)

    seen: set[str] = set()
    for encoding in encodings:
        if not encoding or encoding in seen:
            continue
        seen.add(encoding)
        try:
            decoded = raw_bytes.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
        cleaned = _cleanup_text(decoded)
        if _looks_like_text(cleaned):
            return decoded

    return ""


def _looks_like_text(value: str) -> bool:
    if not value:
        return False

    control_characters = sum(1 for char in value if ord(char) < 32 and char not in "\n\r\t")
    if control_characters / max(len(value), 1) > 0.05:
        return False

    return any(char.isalnum() for char in value)


def _looks_like_sectioned_report(value: str) -> bool:
    return bool(_REPORT_SECTION_RE.search(value))


def _text_matches(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    return _cleanup_text(left).casefold() == _cleanup_text(right).casefold()


def _reference_display(value: object, *, resource_index: dict[str, dict[str, Any]]) -> str | None:
    if not isinstance(value, dict):
        return None

    direct_display = _string_value(value.get("display"))
    if direct_display:
        return direct_display

    resource = _resolve_reference_resource(value, resource_index=resource_index)
    if not resource:
        return None

    return _first_non_empty(
        _string_value(resource.get("name")),
        _human_name_text(resource.get("name")),
        _codeable_concept_text(resource.get("type")),
    )


def _resolve_reference_resource(
    value: object,
    *,
    resource_index: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    if isinstance(value, dict) and _resource_type(value):
        return value
    if not isinstance(value, dict):
        return None

    reference = _string_value(value.get("reference"))
    if not reference:
        return None
    return resource_index.get(reference)


def _extract_identifier_value(value: object) -> str | None:
    for item in _identifier_items(value):
        identifier_value = _string_value(item.get("value"))
        if identifier_value:
            return identifier_value
    return None


def _extract_typed_identifier_value(value: object, *, patterns: tuple[str, ...]) -> str | None:
    normalized_patterns = tuple(item.lower() for item in patterns)
    for item in _identifier_items(value):
        identifier_value = _string_value(item.get("value"))
        if not identifier_value:
            continue
        identifier_type = _identifier_type_text(item.get("type")).lower()
        if any(pattern in identifier_type for pattern in normalized_patterns):
            return identifier_value
    return None


def _identifier_items(value: object) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _identifier_type_text(value: object) -> str:
    if isinstance(value, dict):
        return _codeable_concept_text(value)
    return ""


def _codeable_concept_text(value: object) -> str:
    if isinstance(value, list):
        return " ".join(item for item in (_codeable_concept_text(entry) for entry in value) if item)
    if not isinstance(value, dict):
        return ""

    direct_text = _string_value(value.get("text"))
    if direct_text:
        return direct_text

    codings = value.get("coding")
    if isinstance(codings, list):
        for item in codings:
            if not isinstance(item, dict):
                continue
            coding_text = _first_non_empty(
                _string_value(item.get("display")),
                _string_value(item.get("code")),
            )
            if coding_text:
                return coding_text
    return ""


def _extract_narrative_text(resource: dict[str, Any]) -> str:
    text = resource.get("text")
    if not isinstance(text, dict):
        return ""
    div = _string_value(text.get("div"))
    return _cleanup_text(div)


def _cleanup_text(value: str | None) -> str:
    if not value:
        return ""
    stripped = html.unescape(_HTML_TAG_RE.sub(" ", value))
    return _WHITESPACE_RE.sub(" ", stripped).strip()


def _quantity_text(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    quantity_value = value.get("value")
    unit = _string_value(value.get("unit")) or _string_value(value.get("code"))
    if quantity_value is None:
        return ""
    if unit:
        return f"{quantity_value} {unit}"
    return str(quantity_value)


def _range_text(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    low = _quantity_text(value.get("low"))
    high = _quantity_text(value.get("high"))
    if low and high:
        return f"{low} to {high}"
    return low or high


def _ratio_text(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    numerator = _quantity_text(value.get("numerator"))
    denominator = _quantity_text(value.get("denominator"))
    if numerator and denominator:
        return f"{numerator} / {denominator}"
    return numerator or denominator


def _period_text(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    start = _string_value(value.get("start"))
    end = _string_value(value.get("end"))
    if start and end:
        return f"{start} to {end}"
    return start or end or ""


def _observation_interpretation_text(value: object) -> str:
    text = _codeable_concept_text(value)
    if not text:
        return ""
    return _ensure_sentence(f"Interpretation: {text}")


def _observation_reference_range_text(value: object) -> str:
    if not isinstance(value, list):
        return ""

    range_texts: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        direct_text = _string_value(item.get("text"))
        type_text = _codeable_concept_text(item.get("type"))
        bounds_text = _reference_range_bounds_text(item)

        if type_text and bounds_text:
            _append_unique_fragment(range_texts, _ensure_sentence(f"{type_text} reference range: {bounds_text}"))
        elif bounds_text:
            _append_unique_fragment(range_texts, _ensure_sentence(f"Reference range: {bounds_text}"))
        elif direct_text:
            _append_unique_fragment(range_texts, _ensure_sentence(f"Reference range: {direct_text}"))

    return " ".join(item for item in range_texts if item)


def _reference_range_bounds_text(value: dict[str, Any]) -> str:
    low = _quantity_text(value.get("low"))
    high = _quantity_text(value.get("high"))
    if low and high:
        return f"{low} to {high}"
    if high:
        return f"up to {high}"
    if low:
        return f"{low} or greater"
    return ""


def _note_text(value: object) -> str:
    if not isinstance(value, list):
        return ""
    notes = []
    for item in value:
        if not isinstance(item, dict):
            continue
        text = _string_value(item.get("text"))
        if text:
            notes.append(text)
    return " ".join(notes)


def _human_name_text(value: object) -> str:
    if isinstance(value, list):
        return " ".join(item for item in (_human_name_text(entry) for entry in value) if item)
    if not isinstance(value, dict):
        return ""

    given = value.get("given")
    family = _string_value(value.get("family"))
    parts: list[str] = []
    if isinstance(given, list):
        parts.extend(str(item) for item in given if isinstance(item, str))
    if family:
        parts.append(family)
    return " ".join(parts).strip()


def _resource_identity(value: dict[str, Any]) -> str | None:
    resource_type = _resource_type(value)
    resource_id = _string_value(value.get("id"))
    if resource_type and resource_id:
        return f"{resource_type}/{resource_id}"
    return None


def _resource_type(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    return _string_value(value.get("resourceType"))


def _string_value(value: object) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _nested_string_value(value: dict[str, Any], *keys: str) -> str | None:
    cursor: object = value
    for key in keys:
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(key)
    return _string_value(cursor)


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value
    return None


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


def _ensure_sentence(value: str | None) -> str:
    text = _cleanup_text(value)
    if not text:
        return ""
    if text.endswith((".", "!", "?")):
        return text
    return f"{text}."
