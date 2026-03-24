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
