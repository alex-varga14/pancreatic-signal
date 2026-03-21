from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from pydantic import ValidationError

from app.schemas.triage import ReportInput

_IMPORT_METADATA_FIELDS = {
    "patient_identifier",
    "encounter_identifier",
    "accession_number",
    "ordering_provider",
    "source_system",
    "source_format",
    "import_source_id",
}


class ImportParseError(ValueError):
    pass


def categorize_import_parse_error(exc: ImportParseError) -> str:
    message = str(exc).lower()

    if "failed validation" in message:
        return "validation_error"

    if any(
        pattern in message
        for pattern in (
            "unsupported file type",
            "diagnosticreport resource or bundle",
            "bundle import requires",
            "not an oru result message",
            "must start with an msh segment",
            "payload must be",
            "did not contain any diagnosticreport",
        )
    ):
        return "unsupported_payload"

    return "parse_error"


def parse_report_upload(
    *,
    filename: str | None,
    content_type: str | None,
    raw_bytes: bytes,
) -> tuple[str, list[ReportInput]]:
    text = raw_bytes.decode("utf-8-sig")
    suffix = Path(filename or "").suffix.lower()
    content_type = (content_type or "").lower()

    if suffix == ".csv" or content_type in {"text/csv", "application/csv"}:
        return "csv", _parse_csv(text)
    if suffix in {".jsonl", ".ndjson"} or content_type in {
        "application/x-ndjson",
        "application/jsonl",
        "application/jsonlines",
    }:
        return "jsonl", _parse_jsonl(text)
    if suffix == ".json" or content_type == "application/json":
        return "json", _parse_json(text)

    raise ImportParseError("Unsupported file type. Upload a .csv, .jsonl, .ndjson, or .json file.")


def _parse_csv(text: str) -> list[ReportInput]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ImportParseError("CSV import requires a header row.")

    reports: list[ReportInput] = []
    for row_index, row in enumerate(reader, start=2):
        reports.append(_validate_record(_normalize_record(row), row_label=f"CSV row {row_index}"))

    if not reports:
        raise ImportParseError("CSV import did not contain any data rows.")
    return reports


def _parse_jsonl(text: str) -> list[ReportInput]:
    reports: list[ReportInput] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ImportParseError(f"JSONL line {line_number} is not valid JSON.") from exc
        reports.append(_validate_record(payload, row_label=f"JSONL line {line_number}"))

    if not reports:
        raise ImportParseError("JSONL import did not contain any report rows.")
    return reports


def _parse_json(text: str) -> list[ReportInput]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportParseError("JSON import payload is not valid JSON.") from exc

    if isinstance(payload, dict) and "reports" in payload:
        payload = payload["reports"]
    if not isinstance(payload, list):
        raise ImportParseError(
            "JSON import payload must be a list of reports or an object with a 'reports' field."
        )

    reports = [
        _validate_record(record, row_label=f"JSON item {index}")
        for index, record in enumerate(payload, start=1)
    ]
    if not reports:
        raise ImportParseError("JSON import did not contain any report rows.")
    return reports


def _validate_record(record: object, *, row_label: str) -> ReportInput:
    try:
        if isinstance(record, dict):
            record = _normalize_record(record)
        return ReportInput.model_validate(record)
    except ValidationError as exc:
        raise ImportParseError(f"{row_label} failed validation: {exc}") from exc


def _normalize_record(record: dict[str, object]) -> dict[str, object]:
    cleaned: dict[str, object] = {}
    import_metadata: dict[str, object] = {}
    for key, value in record.items():
        normalized_key = key.strip() if isinstance(key, str) else key
        if isinstance(value, str):
            stripped = value.strip()
            cleaned_value: object = stripped if stripped != "" else None
        else:
            cleaned_value = value

        if normalized_key in _IMPORT_METADATA_FIELDS:
            import_metadata[str(normalized_key)] = cleaned_value
            continue
        if isinstance(normalized_key, str) and normalized_key.startswith("import_metadata."):
            metadata_key = normalized_key.split(".", 1)[1]
            if metadata_key in _IMPORT_METADATA_FIELDS:
                import_metadata[metadata_key] = cleaned_value
                continue
        cleaned[str(normalized_key)] = cleaned_value

    existing_metadata = cleaned.get("import_metadata")
    if isinstance(existing_metadata, dict):
        import_metadata = {**import_metadata, **existing_metadata}
    if import_metadata:
        cleaned["import_metadata"] = import_metadata
    return cleaned
