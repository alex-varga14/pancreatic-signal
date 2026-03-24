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
    presented_form_text = _extract_presented_form_text(resource.get("presentedForm"))
    if presented_form_text:
        return normalize_text(presented_form_text)

    sections: list[str] = []

    findings = _extract_findings_text(resource, resource_index=resource_index)
    if findings:
        sections.append(f"Findings: {findings}")

    conclusion = _first_non_empty(
        _string_value(resource.get("conclusion")),
        _extract_narrative_text(resource),
    )
    if conclusion:
        label = "Impression" if findings else "Report"
        sections.append(f"{label}: {conclusion}")

    combined = " ".join(item for item in sections if item)
    return normalize_text(combined)


def _extract_findings_text(resource: dict[str, Any], *, resource_index: dict[str, dict[str, Any]]) -> str:
    findings: list[str] = []
    results = resource.get("result")
    if isinstance(results, list):
        for item in results:
            observation = _resolve_reference_resource(item, resource_index=resource_index)
            text = _observation_to_text(observation)
            if text:
                findings.append(text)

    if findings:
        return " ".join(findings)

    code_text = _codeable_concept_text(resource.get("code"))
    if code_text and code_text.lower() != "diagnostic report":
        return code_text
    return ""


def _observation_to_text(resource: dict[str, Any] | None) -> str:
    if not resource:
        return ""

    narrative = _extract_narrative_text(resource)
    if narrative:
        return _ensure_sentence(narrative)

    label = _codeable_concept_text(resource.get("code"))
    value = _first_non_empty(
        _string_value(resource.get("valueString")),
        _codeable_concept_text(resource.get("valueCodeableConcept")),
        _quantity_text(resource.get("valueQuantity")),
        _range_text(resource.get("valueRange")),
        _note_text(resource.get("note")),
    )

    if label and value:
        return _ensure_sentence(f"{label}: {value}")
    if value:
        return _ensure_sentence(value)
    return _ensure_sentence(label)


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


def _extract_presented_form_text(value: object) -> str:
    if not isinstance(value, list):
        return ""

    for item in value:
        if not isinstance(item, dict):
            continue
        content_type = (_string_value(item.get("contentType")) or "").lower()
        if content_type and not content_type.startswith("text/"):
            continue

        raw_data = _string_value(item.get("data"))
        if raw_data:
            try:
                decoded = base64.b64decode(raw_data, validate=False).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError):
                decoded = ""
            if decoded:
                return _cleanup_text(decoded)

        inline_text = _string_value(item.get("text"))
        if inline_text:
            return _cleanup_text(inline_text)

    return ""


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
