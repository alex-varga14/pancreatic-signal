import base64

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.store.memory_store import CASE_STORE


def test_import_reports_accepts_jsonl() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = "\n".join(
        [
            (
                '{"report_id":"R-IMPORT-1","case_id":"C-IMPORT-1",'
                '"report_datetime":"2026-03-19T10:00:00Z","modality":"CT",'
                '"site":"Demo Hospital","report_text":"Impression: Suspicious for pancreatic neoplasm."}'
            ),
            (
                '{"report_id":"R-IMPORT-2","case_id":"C-IMPORT-2",'
                '"report_datetime":"2026-03-19T11:00:00Z","modality":"CT",'
                '"site":"Demo Hospital","report_text":"Impression: No acute abnormality."}'
            ),
        ]
    )

    response = client.post(
        "/api/v1/imports/reports",
        files={"file": ("reports.jsonl", payload, "application/x-ndjson")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["processed"] == 2
    assert body["flagged"] == 1
    assert body["source_format"] == "jsonl"

    cases = client.get("/api/v1/cases").json()
    assert [item["case_id"] for item in cases] == ["C-IMPORT-1", "C-IMPORT-2"]


def test_import_reports_accepts_csv() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = "\n".join(
        [
            "report_id,case_id,report_datetime,modality,site,patient_identifier,source_format,report_text",
            (
                'R-CSV-1,C-CSV-1,2026-03-19T10:00:00Z,CT,Demo Hospital,PAT-CSV-1,csv,'
                '"Impression: Recommend biopsy for pancreatic mass suspicious for malignancy."'
            ),
        ]
    )

    response = client.post(
        "/api/v1/imports/reports",
        files={"file": ("reports.csv", payload, "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["processed"] == 1
    assert body["flagged"] == 1
    assert body["source_format"] == "csv"

    case_detail = client.get("/api/v1/cases/C-CSV-1").json()
    assert case_detail["report_id"] == "R-CSV-1"
    assert case_detail["site"] == "Demo Hospital"
    assert case_detail["import_metadata"]["patient_identifier"] == "PAT-CSV-1"
    assert case_detail["import_metadata"]["source_format"] == "csv"


def test_import_reports_rejects_invalid_rows() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = '{"report_id":"R-BAD-1","case_id":"C-BAD-1"}'
    response = client.post(
        "/api/v1/imports/reports",
        files={"file": ("reports.jsonl", payload, "application/x-ndjson")},
    )
    assert response.status_code == 400
    assert "failed validation" in response.json()["detail"]


def test_import_fhir_diagnostic_report_accepts_single_resource() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = {
        "resourceType": "DiagnosticReport",
        "id": "dr-single-1",
        "effectiveDateTime": "2026-03-19T10:00:00Z",
        "category": [{"text": "CT abdomen"}],
        "performer": [{"display": "Demo Hospital"}],
        "conclusion": "Suspicious for pancreatic neoplasm. Recommend biopsy.",
    }

    response = client.post("/api/v1/imports/fhir/diagnostic-reports", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["processed"] == 1
    assert body["flagged"] == 1
    assert body["source_format"] == "fhir-diagnostic-report"
    assert body["case_ids"] == ["dr-single-1"]
    assert body["report_ids"] == ["dr-single-1"]

    case_detail = client.get("/api/v1/cases/dr-single-1").json()
    assert case_detail["report_id"] == "dr-single-1"
    assert case_detail["site"] == "Demo Hospital"
    assert case_detail["modality"] == "CT"
    assert case_detail["import_metadata"]["source_system"] == "Demo Hospital"
    assert case_detail["import_metadata"]["source_format"] == "fhir-diagnostic-report"
    assert case_detail["import_metadata"]["import_source_id"] == "DiagnosticReport/dr-single-1"


def test_import_fhir_diagnostic_report_bundle_resolves_references() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "fullUrl": "urn:uuid:org-1",
                "resource": {
                    "resourceType": "Organization",
                    "id": "org-1",
                    "name": "North Clinic",
                },
            },
            {
                "fullUrl": "urn:uuid:patient-1",
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-1",
                    "identifier": [{"value": "MRN-001"}],
                    "name": [{"given": ["Jamie"], "family": "Doe"}],
                },
            },
            {
                "fullUrl": "urn:uuid:enc-1",
                "resource": {
                    "resourceType": "Encounter",
                    "id": "enc-1",
                    "identifier": [{"value": "ENC-001"}],
                    "serviceProvider": {"reference": "Organization/org-1"},
                },
            },
            {
                "fullUrl": "urn:uuid:practitioner-1",
                "resource": {
                    "resourceType": "Practitioner",
                    "id": "practitioner-1",
                    "name": [{"given": ["Jamie"], "family": "Patel"}],
                },
            },
            {
                "fullUrl": "urn:uuid:sr-1",
                "resource": {
                    "resourceType": "ServiceRequest",
                    "id": "sr-1",
                    "identifier": [
                        {
                            "type": {"text": "Accession Number"},
                            "value": "ACC-777",
                        }
                    ],
                    "requester": {"reference": "Practitioner/practitioner-1"},
                },
            },
            {
                "fullUrl": "urn:uuid:obs-1",
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs-1",
                    "code": {"text": "Pancreatic duct"},
                    "valueString": "Abrupt cutoff of the pancreatic duct with upstream dilation",
                },
            },
            {
                "fullUrl": "urn:uuid:obs-2",
                "resource": {
                    "resourceType": "Observation",
                    "id": "obs-2",
                    "code": {"text": "Pancreatic head lesion"},
                    "valueString": "Ill-defined pancreatic head lesion",
                },
            },
            {
                "fullUrl": "urn:uuid:dr-1",
                "resource": {
                    "resourceType": "DiagnosticReport",
                    "id": "dr-bundle-1",
                    "meta": {"source": "urn:source:fhir-gateway"},
                    "effectiveDateTime": "2026-03-19T11:00:00Z",
                    "subject": {"reference": "Patient/patient-1"},
                    "encounter": {"reference": "Encounter/enc-1"},
                    "basedOn": [{"reference": "ServiceRequest/sr-1"}],
                    "category": [{"text": "MRI abdomen"}],
                    "performer": [{"reference": "Organization/org-1"}],
                    "result": [
                        {"reference": "Observation/obs-1"},
                        {"reference": "Observation/obs-2"},
                    ],
                    "conclusion": "Suspicious for pancreatic neoplasm. Recommend EUS.",
                },
            },
        ],
    }

    response = client.post("/api/v1/imports/fhir/diagnostic-reports", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["processed"] == 1
    assert body["flagged"] == 1

    case_detail = client.get("/api/v1/cases/dr-bundle-1").json()
    assert case_detail["site"] == "North Clinic"
    assert case_detail["modality"] == "MRI"
    assert case_detail["score"] >= 0.3
    assert case_detail["import_metadata"]["patient_identifier"] == "MRN-001"
    assert case_detail["import_metadata"]["encounter_identifier"] == "ENC-001"
    assert case_detail["import_metadata"]["accession_number"] == "ACC-777"
    assert case_detail["import_metadata"]["ordering_provider"] == "Jamie Patel"
    assert case_detail["import_metadata"]["source_system"] == "urn:source:fhir-gateway"
    assert case_detail["import_metadata"]["source_format"] == "fhir-diagnostic-report"
    assert case_detail["import_metadata"]["import_source_id"] == "DiagnosticReport/dr-bundle-1"
    assert any(item["code"] == "DUCT_CUTOFF" for item in case_detail["evidence"])


def test_import_fhir_diagnostic_report_decodes_presented_form_attachment_bundle() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    attachment_html = (
        '<div xmlns="http://www.w3.org/1999/xhtml">'
        "<p><strong>Findings:</strong> Abrupt cutoff of the pancreatic duct with ill-defined pancreatic head lesion.</p>"
        "<p><strong>Impression:</strong> Suspicious for pancreatic neoplasm. Recommend EUS.</p>"
        "</div>"
    )
    attachment_data = base64.b64encode(attachment_html.encode("utf-16")).decode("ascii")

    payload = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Organization",
                    "id": "org-attachment-1",
                    "name": "Attachment Hospital",
                },
            },
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-attachment-1",
                    "identifier": [{"value": "MRN-ATTACH-1"}],
                },
            },
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": "enc-attachment-1",
                    "identifier": [{"value": "ENC-ATTACH-1"}],
                    "serviceProvider": {"reference": "Organization/org-attachment-1"},
                },
            },
            {
                "resource": {
                    "resourceType": "Practitioner",
                    "id": "practitioner-attachment-1",
                    "name": [{"given": ["Jamie"], "family": "Patel"}],
                },
            },
            {
                "resource": {
                    "resourceType": "ServiceRequest",
                    "id": "sr-attachment-1",
                    "identifier": [
                        {
                            "type": {"text": "Accession Number"},
                            "value": "ACC-ATTACH-1",
                        }
                    ],
                    "requester": {"reference": "Practitioner/practitioner-attachment-1"},
                },
            },
            {
                "resource": {
                    "resourceType": "DiagnosticReport",
                    "id": "dr-attachment-1",
                    "meta": {"source": "urn:source:attachment-feed"},
                    "effectiveDateTime": "2026-03-19T11:15:00Z",
                    "subject": {"reference": "Patient/patient-attachment-1"},
                    "encounter": {"reference": "Encounter/enc-attachment-1"},
                    "basedOn": [{"reference": "ServiceRequest/sr-attachment-1"}],
                    "category": [{"text": "MRI abdomen"}],
                    "performer": [{"reference": "Organization/org-attachment-1"}],
                    "presentedForm": [
                        {
                            "contentType": "application/xhtml+xml; charset=utf-16",
                            "data": attachment_data,
                        }
                    ],
                },
            },
        ],
    }

    response = client.post("/api/v1/imports/fhir/diagnostic-reports", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["processed"] == 1
    assert body["flagged"] == 1

    case_detail = client.get("/api/v1/cases/dr-attachment-1").json()
    assert case_detail["site"] == "Attachment Hospital"
    assert case_detail["modality"] == "MRI"
    assert case_detail["score"] >= 0.3
    assert case_detail["report_text"].startswith("Findings: Abrupt cutoff of the pancreatic duct")
    assert "Impression: Suspicious for pancreatic neoplasm. Recommend EUS." in case_detail["report_text"]
    assert case_detail["import_metadata"]["patient_identifier"] == "MRN-ATTACH-1"
    assert case_detail["import_metadata"]["encounter_identifier"] == "ENC-ATTACH-1"
    assert case_detail["import_metadata"]["accession_number"] == "ACC-ATTACH-1"
    assert case_detail["import_metadata"]["ordering_provider"] == "Jamie Patel"
    assert case_detail["import_metadata"]["source_system"] == "urn:source:attachment-feed"
    assert case_detail["import_metadata"]["import_source_id"] == "DiagnosticReport/dr-attachment-1"
    assert any(item["code"] == "DUCT_CUTOFF" for item in case_detail["evidence"])


def test_import_fhir_diagnostic_report_merges_unstructured_presented_form_with_conclusion() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    attachment_text = "Abrupt cutoff of the pancreatic duct with ill-defined pancreatic head lesion."
    payload = {
        "resourceType": "DiagnosticReport",
        "id": "dr-attachment-merge-1",
        "effectiveDateTime": "2026-03-19T11:20:00Z",
        "category": [{"text": "CT abdomen"}],
        "performer": [{"display": "Merge Hospital"}],
        "presentedForm": [
            {
                "contentType": "text/plain; charset=utf-8",
                "data": base64.b64encode(attachment_text.encode("utf-8")).decode("ascii"),
            }
        ],
        "conclusion": "Suspicious for pancreatic neoplasm. Recommend biopsy.",
    }

    response = client.post("/api/v1/imports/fhir/diagnostic-reports", json=payload)
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/dr-attachment-merge-1").json()
    assert case_detail["site"] == "Merge Hospital"
    assert case_detail["report_text"] == (
        "Findings: Abrupt cutoff of the pancreatic duct with ill-defined pancreatic head lesion. "
        "Impression: Suspicious for pancreatic neoplasm. Recommend biopsy."
    )
    assert any(item["code"] == "DUCT_CUTOFF" for item in case_detail["evidence"])


def test_import_fhir_diagnostic_report_falls_back_to_reference_identifiers() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = {
        "resourceType": "DiagnosticReport",
        "id": "dr-fallback-1",
        "effectiveDateTime": "2026-03-19T11:30:00Z",
        "identifier": [{"value": "ACC-FHIR-FALLBACK"}],
        "subject": {"reference": "Patient/patient-fallback"},
        "encounter": {"reference": "Encounter/encounter-fallback"},
        "performer": [{"display": "Fallback Hospital"}],
        "conclusion": "Suspicious for pancreatic neoplasm.",
    }

    response = client.post("/api/v1/imports/fhir/diagnostic-reports", json=payload)
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/ACC-FHIR-FALLBACK").json()
    assert case_detail["import_metadata"]["patient_identifier"] == "patient-fallback"
    assert case_detail["import_metadata"]["encounter_identifier"] == "encounter-fallback"
    assert case_detail["import_metadata"]["accession_number"] == "ACC-FHIR-FALLBACK"
    assert case_detail["import_metadata"]["source_system"] == "Fallback Hospital"


def test_import_fhir_diagnostic_report_supports_reference_identifier_preference_override(monkeypatch) -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    monkeypatch.setattr(
        settings,
        "fhir_reference_identifier_source_order",
        "reference_tail,resolved_identifier,resolved_id",
    )

    payload = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-config",
                    "identifier": [{"value": "MRN-CONFIG"}],
                },
            },
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": "enc-config",
                    "identifier": [{"value": "ENC-CONFIG"}],
                },
            },
            {
                "resource": {
                    "resourceType": "DiagnosticReport",
                    "id": "dr-config-1",
                    "effectiveDateTime": "2026-03-19T11:45:00Z",
                    "subject": {"reference": "Patient/patient-config"},
                    "encounter": {"reference": "Encounter/enc-config"},
                    "performer": [{"display": "Config Hospital"}],
                    "conclusion": "Suspicious for pancreatic neoplasm.",
                },
            },
        ],
    }

    response = client.post("/api/v1/imports/fhir/diagnostic-reports", json=payload)
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/dr-config-1").json()
    assert case_detail["import_metadata"]["patient_identifier"] == "patient-config"
    assert case_detail["import_metadata"]["encounter_identifier"] == "enc-config"


def test_import_fhir_diagnostic_report_supports_inline_reference_identifiers() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = {
        "resourceType": "DiagnosticReport",
        "id": "dr-inline-reference-1",
        "effectiveDateTime": "2026-03-19T11:50:00Z",
        "subject": {"identifier": {"value": "MRN-INLINE-1"}},
        "encounter": {"identifier": {"value": "ENC-INLINE-1"}},
        "basedOn": [
            {
                "identifier": {
                    "type": {"text": "Accession Number"},
                    "value": "ACC-INLINE-1",
                }
            }
        ],
        "performer": [{"display": "Inline Hospital"}],
        "conclusion": "Suspicious for pancreatic neoplasm. Recommend EUS.",
    }

    response = client.post("/api/v1/imports/fhir/diagnostic-reports", json=payload)
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/dr-inline-reference-1").json()
    assert case_detail["site"] == "Inline Hospital"
    assert case_detail["import_metadata"]["patient_identifier"] == "MRN-INLINE-1"
    assert case_detail["import_metadata"]["encounter_identifier"] == "ENC-INLINE-1"
    assert case_detail["import_metadata"]["accession_number"] == "ACC-INLINE-1"
    assert case_detail["import_metadata"]["source_system"] == "Inline Hospital"


def test_import_fhir_diagnostic_report_supports_inline_reference_identifier_preference_override(
    monkeypatch,
) -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    monkeypatch.setattr(
        settings,
        "fhir_reference_identifier_source_order",
        "reference_tail,reference_identifier,resolved_identifier,resolved_id",
    )

    payload = {
        "resourceType": "DiagnosticReport",
        "id": "dr-inline-config-1",
        "effectiveDateTime": "2026-03-19T11:55:00Z",
        "subject": {
            "reference": "Patient/patient-inline-tail",
            "identifier": {"value": "MRN-INLINE-CONFIG"},
        },
        "encounter": {
            "reference": "Encounter/encounter-inline-tail",
            "identifier": {"value": "ENC-INLINE-CONFIG"},
        },
        "performer": [{"display": "Config Inline Hospital"}],
        "conclusion": "Suspicious for pancreatic neoplasm.",
    }

    response = client.post("/api/v1/imports/fhir/diagnostic-reports", json=payload)
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/dr-inline-config-1").json()
    assert case_detail["import_metadata"]["patient_identifier"] == "patient-inline-tail"
    assert case_detail["import_metadata"]["encounter_identifier"] == "encounter-inline-tail"


def test_import_fhir_diagnostic_report_respects_site_scope() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = {
        "resourceType": "DiagnosticReport",
        "id": "dr-scope-1",
        "effectiveDateTime": "2026-03-19T12:00:00Z",
        "category": [{"text": "CT abdomen"}],
        "performer": [{"display": "Demo Hospital"}],
        "conclusion": "Suspicious for pancreatic neoplasm.",
    }

    response = client.post(
        "/api/v1/imports/fhir/diagnostic-reports",
        json=payload,
        headers={"X-User-ID": "north-analyst", "X-User-Role": "analyst", "X-User-Sites": "North Clinic"},
    )
    assert response.status_code == 403
    assert "Demo Hospital" in response.json()["detail"]


def test_import_fhir_diagnostic_report_rejects_non_diagnostic_report_payload() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = {"resourceType": "Observation", "id": "obs-only"}
    response = client.post("/api/v1/imports/fhir/diagnostic-reports", json=payload)
    assert response.status_code == 400
    assert "DiagnosticReport resource or Bundle" in response.json()["detail"]


def test_import_hl7_oru_accepts_single_message() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    pv1_fields = ["PV1", "1", "O", "RAD^^^Demo Hospital", *[""] * 15, "ENC-1"]
    obr_fields = [
        "OBR",
        "1",
        "PLAC-1",
        "R-HL7-1",
        "CT ABDOMEN^CT Abdomen",
        "",
        "",
        "20260319100000",
        *[""] * 8,
        "PROV-1^Patel^Jamie",
        "",
        "ACC-HL7-1",
    ]
    payload = "\r".join(
        [
            "MSH|^~\\&|RADSYS|Demo Hospital|PS|PS|20260319100000||ORU^R01|MSG-1|P|2.5",
            "PID|1||PAT-1^^^MRN||Doe^John",
            "|".join(pv1_fields),
            "|".join(obr_fields),
            "OBX|1|TX|FINDINGS^Findings||Abrupt cutoff of the pancreatic duct with ill-defined pancreatic head lesion.|",
            "OBX|2|TX|IMPRESSION^Impression||Suspicious for pancreatic neoplasm. Recommend biopsy.|",
        ]
    )

    response = client.post(
        "/api/v1/imports/hl7/oru",
        content=payload,
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["processed"] == 1
    assert body["flagged"] == 1
    assert body["source_format"] == "hl7-oru"
    assert body["case_ids"] == ["R-HL7-1"]
    assert body["report_ids"] == ["R-HL7-1"]

    case_detail = client.get("/api/v1/cases/R-HL7-1").json()
    assert case_detail["site"] == "Demo Hospital"
    assert case_detail["modality"] == "CT"
    assert case_detail["score"] >= 0.3
    assert case_detail["import_metadata"]["patient_identifier"] == "PAT-1"
    assert case_detail["import_metadata"]["encounter_identifier"] == "ENC-1"
    assert case_detail["import_metadata"]["accession_number"] == "ACC-HL7-1"
    assert case_detail["import_metadata"]["ordering_provider"] == "Jamie Patel"
    assert case_detail["import_metadata"]["source_system"] == "RADSYS"
    assert case_detail["import_metadata"]["source_format"] == "hl7-oru"
    assert case_detail["import_metadata"]["import_source_id"] == "MSG-1"


def test_import_hl7_oru_accepts_multiple_obr_groups() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = "\r".join(
        [
            "MSH|^~\\&|RADSYS|North Clinic|PS|PS|20260319110000||ORU^R01|MSG-2|P|2.5",
            "PID|1||PAT-2^^^MRN||Doe^Jane",
            "PV1|1|O|RAD^^^North Clinic",
            "OBR|1|PLAC-A|R-HL7-A|MRI ABDOMEN^MRI Abdomen|||20260319110000",
            "OBX|1|TX|FINDINGS^Findings||Double duct sign with focal pancreatic atrophy.|",
            "OBX|2|TX|IMPRESSION^Impression||Recommend EUS for further evaluation.|",
            "OBR|2|PLAC-B|R-HL7-B|CT ABDOMEN^CT Abdomen|||20260319113000",
            "OBX|1|TX|FINDINGS^Findings||Pancreas is unremarkable.|",
            "OBX|2|TX|IMPRESSION^Impression||No acute abnormality.|",
        ]
    )

    response = client.post(
        "/api/v1/imports/hl7/oru",
        content=payload,
        headers={"Content-Type": "application/hl7-v2"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["processed"] == 2
    assert body["flagged"] == 1
    assert body["case_ids"] == ["R-HL7-A", "R-HL7-B"]

    cases = client.get("/api/v1/cases").json()
    assert [item["case_id"] for item in cases] == ["R-HL7-A", "R-HL7-B"]


def test_import_hl7_oru_falls_back_when_optional_metadata_fields_are_missing() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = "\r".join(
        [
            "MSH|^~\\&||Fallback Hospital|PS|PS|20260319111500||ORU^R01|MSG-FALLBACK|P|2.5",
            "PID|1||PAT-FALLBACK^^^MRN||Doe^John",
            "OBR|1|PLAC-FALLBACK|R-HL7-FALLBACK|CT ABDOMEN^CT Abdomen|||20260319111500",
            "OBX|1|TX|IMPRESSION^Impression||Suspicious for pancreatic neoplasm.|",
        ]
    )

    response = client.post(
        "/api/v1/imports/hl7/oru",
        content=payload,
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/R-HL7-FALLBACK").json()
    assert case_detail["import_metadata"]["patient_identifier"] == "PAT-FALLBACK"
    assert case_detail["import_metadata"]["encounter_identifier"] is None
    assert case_detail["import_metadata"]["accession_number"] == "R-HL7-FALLBACK"
    assert case_detail["import_metadata"]["ordering_provider"] is None
    assert case_detail["import_metadata"]["source_system"] == "Fallback Hospital"
    assert case_detail["import_metadata"]["import_source_id"] == "MSG-FALLBACK"


def test_import_hl7_oru_supports_patient_identifier_field_order_override(monkeypatch) -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    monkeypatch.setattr(settings, "hl7_patient_identifier_field_order", "PID-2,PID-3")

    payload = "\r".join(
        [
            "MSH|^~\\&|RADSYS|Demo Hospital|PS|PS|20260319111600||ORU^R01|MSG-CONFIG|P|2.5",
            "PID|1|ALT-PAT|PRIMARY-PAT^^^MRN||Doe^John",
            "OBR|1|PLAC-CONFIG|R-HL7-CONFIG|CT ABDOMEN^CT Abdomen|||20260319111600",
            "OBX|1|TX|IMPRESSION^Impression||Suspicious for pancreatic neoplasm.|",
        ]
    )

    response = client.post(
        "/api/v1/imports/hl7/oru",
        content=payload,
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/R-HL7-CONFIG").json()
    assert case_detail["import_metadata"]["patient_identifier"] == "ALT-PAT"


def test_import_hl7_oru_decodes_base64_ed_obx_text() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    encoded_impression = base64.b64encode(
        b"Suspicious for pancreatic neoplasm. Recommend biopsy."
    ).decode()

    payload = "\r".join(
        [
            "MSH|^~\\&|RADSYS|Demo Hospital|PS|PS|20260319111700||ORU^R01|MSG-ED|P|2.5",
            "PID|1||PAT-ED^^^MRN||Doe^John",
            "OBR|1|PLAC-ED|R-HL7-ED|CT ABDOMEN^CT Abdomen|||20260319111700",
            f"OBX|1|ED|IMPRESSION^Impression||^^^Base64^{encoded_impression}|",
        ]
    )

    response = client.post(
        "/api/v1/imports/hl7/oru",
        content=payload,
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/R-HL7-ED").json()
    assert case_detail["score"] >= 0.3
    assert "Suspicious for pancreatic neoplasm." in case_detail["report_text"]
    assert "Recommend biopsy." in case_detail["report_text"]


def test_import_hl7_oru_normalizes_repeated_obx_values() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = "\r".join(
        [
            "MSH|^~\\&|RADSYS|Demo Hospital|PS|PS|20260319111800||ORU^R01|MSG-REPEAT|P|2.5",
            "PID|1||PAT-REPEAT^^^MRN||Doe^John",
            "OBR|1|PLAC-REPEAT|R-HL7-REPEAT|CT ABDOMEN^CT Abdomen|||20260319111800",
            (
                "OBX|1|TX|FINDINGS^Findings||Abrupt cutoff of the pancreatic duct~"
                "with ill-defined pancreatic head lesion.|"
            ),
            (
                "OBX|2|TX|IMPRESSION^Impression||Suspicious for pancreatic neoplasm.~"
                "Recommend EUS for further evaluation.|"
            ),
        ]
    )

    response = client.post(
        "/api/v1/imports/hl7/oru",
        content=payload,
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/R-HL7-REPEAT").json()
    assert case_detail["score"] >= 0.3
    assert "Abrupt cutoff of the pancreatic duct" in case_detail["report_text"]
    assert "ill-defined pancreatic head lesion." in case_detail["report_text"]
    assert "Recommend EUS for further evaluation." in case_detail["report_text"]
    assert any(item["code"] == "DUCT_CUTOFF" for item in case_detail["evidence"])


def test_import_hl7_oru_respects_custom_msh2_delimiters() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    encoded_impression = base64.b64encode(
        b"Suspicious for pancreatic neoplasm. Recommend biopsy."
    ).decode()

    pv1_fields = ["PV1", "1", "O", "RAD!!!Demo Hospital", *[""] * 15, "ENC-DELIM"]
    obr_fields = [
        "OBR",
        "1",
        "PLAC-DELIM",
        "R-HL7-DELIM",
        "CT ABDOMEN!CT Abdomen",
        "",
        "",
        "20260319111900",
        *[""] * 8,
        "PROV-DELIM!Patel!Jamie",
        "",
        "ACC-HL7-DELIM",
    ]
    payload = "\r".join(
        [
            "MSH|!%?@|RADSYS|Demo Hospital|PS|PS|20260319111900||ORU!R01|MSG-DELIM|P|2.5",
            "PID|1||PAT-DELIM!!!MRN||Doe!John",
            "|".join(pv1_fields),
            "|".join(obr_fields),
            (
                "OBX|1|TX|FINDINGS!Findings||Abrupt cutoff of the pancreatic duct%"
                "with upstream dilation.|"
            ),
            f"OBX|2|ED|IMPRESSION!Impression||!!!Base64!{encoded_impression}|",
        ]
    )

    response = client.post(
        "/api/v1/imports/hl7/oru",
        content=payload,
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/R-HL7-DELIM").json()
    assert case_detail["site"] == "Demo Hospital"
    assert case_detail["modality"] == "CT"
    assert case_detail["score"] >= 0.3
    assert case_detail["import_metadata"]["patient_identifier"] == "PAT-DELIM"
    assert case_detail["import_metadata"]["encounter_identifier"] == "ENC-DELIM"
    assert case_detail["import_metadata"]["accession_number"] == "ACC-HL7-DELIM"
    assert case_detail["import_metadata"]["ordering_provider"] == "Jamie Patel"
    assert case_detail["import_metadata"]["source_system"] == "RADSYS"
    assert "Abrupt cutoff of the pancreatic duct" in case_detail["report_text"]
    assert "with upstream dilation." in case_detail["report_text"]
    assert "Suspicious for pancreatic neoplasm." in case_detail["report_text"]
    assert "Recommend biopsy." in case_detail["report_text"]
    assert any(item["code"] == "DUCT_CUTOFF" for item in case_detail["evidence"])


def test_import_hl7_oru_normalizes_default_escape_sequences() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = "\r".join(
        [
            "MSH|^~\\&|RADSYS|Demo Hospital|PS|PS|20260319111930||ORU^R01|MSG-ESCAPE|P|2.5",
            "PID|1||PAT-ESCAPE^^^MRN||Doe^John",
            "OBR|1|PLAC-ESCAPE|R-HL7-ESCAPE|CT ABDOMEN^CT Abdomen|||20260319111930|||||||||PROV-ESCAPE^O\\S\\Neil^Jamie",
            (
                "OBX|1|TX|FINDINGS^Findings||\\H\\Abrupt cutoff of the pancreatic duct\\N\\"
                "\\.br\\with upstream dilation.|"
            ),
            "NTE|1||Recommend EUS\\.br\\Consider MRI follow-up.|",
        ]
    )

    response = client.post(
        "/api/v1/imports/hl7/oru",
        content=payload,
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/R-HL7-ESCAPE").json()
    assert case_detail["score"] >= 0.3
    assert "Abrupt cutoff of the pancreatic duct with upstream dilation." in case_detail["report_text"]
    assert "Recommend EUS Consider MRI follow-up." in case_detail["report_text"]
    assert case_detail["import_metadata"]["ordering_provider"] == "Jamie O^Neil"
    assert "\\.br\\" not in case_detail["report_text"]
    assert any(item["code"] == "DUCT_CUTOFF" for item in case_detail["evidence"])


def test_import_hl7_oru_normalizes_custom_escape_sequences() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = "\r".join(
        [
            "MSH|!%?@|RADSYS|Demo Hospital|PS|PS|20260319111945||ORU!R01|MSG-ESCAPE-CUSTOM|P|2.5",
            "PID|1||PAT-ESCAPE-CUSTOM!!!MRN||Doe!John",
            "OBR|1|PLAC-ESCAPE-CUSTOM|R-HL7-ESCAPE-CUSTOM|CT ABDOMEN!CT Abdomen|||20260319111945|||||||||PROV-ESCAPE-CUSTOM!Mc?S?Kay!Jamie",
            (
                "OBX|1|TX|IMPRESSION!Impression||?.br??H?Suspicious for pancreatic neoplasm.?N?"
                " Recommend biopsy.?X0A?Urgent review.|"
            ),
        ]
    )

    response = client.post(
        "/api/v1/imports/hl7/oru",
        content=payload,
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/R-HL7-ESCAPE-CUSTOM").json()
    assert case_detail["score"] >= 0.3
    assert "Suspicious for pancreatic neoplasm." in case_detail["report_text"]
    assert "Recommend biopsy." in case_detail["report_text"]
    assert "Urgent review." in case_detail["report_text"]
    assert case_detail["import_metadata"]["ordering_provider"] == "Jamie Mc!Kay"
    assert "?.br?" not in case_detail["report_text"]


def test_import_hl7_oru_extracts_subcomponent_metadata_with_custom_msh2() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    pv1_fields = [
        "PV1",
        "1",
        "O",
        "RAD!READ1!BED1!Demo Hospital@2.16.840.1@ISO",
        *[""] * 15,
        "ENC-SUBCOMP@VISIT@ISO",
    ]
    obr_fields = [
        "OBR",
        "1",
        "PLAC-SUBCOMP",
        "R-HL7-SUBCOMP",
        "CT ABDOMEN!CT Abdomen",
        "",
        "",
        "20260319112000",
        *[""] * 8,
        "12345@NPI@ISO!Patel@MD!Jamie@Ann",
        "",
        "ACC-SUBCOMP@PLACER@ISO",
    ]
    payload = "\r".join(
        [
            "MSH|!%?@|RADSYS!1.2.3.4!ISO|North Hub|PS|PS|20260319112000||ORU!R01|MSG-SUBCOMP|P|2.5",
            "PID|1||PAT-SUBCOMP!!!MRN@2.16.840.1@ISO||Doe!John",
            "|".join(pv1_fields),
            "|".join(obr_fields),
            "OBX|1|TX|FINDINGS!Findings||Abrupt cutoff of the pancreatic duct.|",
            "OBX|2|TX|IMPRESSION!Impression||Suspicious for pancreatic neoplasm.|",
        ]
    )

    response = client.post(
        "/api/v1/imports/hl7/oru",
        content=payload,
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200

    case_detail = client.get("/api/v1/cases/R-HL7-SUBCOMP").json()
    assert case_detail["site"] == "Demo Hospital"
    assert case_detail["score"] >= 0.3
    assert case_detail["import_metadata"]["patient_identifier"] == "PAT-SUBCOMP"
    assert case_detail["import_metadata"]["encounter_identifier"] == "ENC-SUBCOMP"
    assert case_detail["import_metadata"]["accession_number"] == "ACC-SUBCOMP"
    assert case_detail["import_metadata"]["ordering_provider"] == "Jamie Patel"
    assert case_detail["import_metadata"]["source_system"] == "RADSYS"


def test_import_hl7_oru_respects_site_scope() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = "\r".join(
        [
            "MSH|^~\\&|RADSYS|Demo Hospital|PS|PS|20260319120000||ORU^R01|MSG-3|P|2.5",
            "PID|1||PAT-3^^^MRN||Doe^John",
            "PV1|1|O|RAD^^^Demo Hospital",
            "OBR|1|PLAC-3|R-HL7-SCOPE|CT ABDOMEN^CT Abdomen|||20260319120000",
            "OBX|1|TX|IMPRESSION^Impression||Suspicious for pancreatic neoplasm.|",
        ]
    )

    response = client.post(
        "/api/v1/imports/hl7/oru",
        content=payload,
        headers={
            "Content-Type": "text/plain",
            "X-User-ID": "north-analyst",
            "X-User-Role": "analyst",
            "X-User-Sites": "North Clinic",
        },
    )
    assert response.status_code == 403
    assert "Demo Hospital" in response.json()["detail"]


def test_import_hl7_oru_rejects_non_oru_message() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    payload = "\r".join(
        [
            "MSH|^~\\&|RADSYS|Demo Hospital|PS|PS|20260319130000||ADT^A01|MSG-4|P|2.5",
            "PID|1||PAT-4^^^MRN||Doe^John",
        ]
    )

    response = client.post(
        "/api/v1/imports/hl7/oru",
        content=payload,
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 400
    assert "not an ORU result message" in response.json()["detail"]
