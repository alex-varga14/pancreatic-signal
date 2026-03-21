from fastapi.testclient import TestClient

from app.main import app
from app.store.memory_store import CASE_STORE


def _auth_headers(user_id: str, role: str = "analyst", sites: str | None = None) -> dict[str, str]:
    headers = {"X-User-ID": user_id, "X-User-Role": role}
    if sites:
        headers["X-User-Sites"] = sites
    return headers


def test_successful_import_run_is_persisted_and_exposed() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    analyst_headers = _auth_headers("import-analyst")

    payload = "\n".join(
        [
            (
                '{"report_id":"R-RUN-1","case_id":"C-RUN-1","report_datetime":"2026-03-19T10:00:00Z",'
                '"modality":"CT","site":"Demo Hospital","report_text":"Impression: Suspicious for pancreatic neoplasm."}'
            ),
            (
                '{"report_id":"R-RUN-2","case_id":"C-RUN-2","report_datetime":"2026-03-19T11:00:00Z",'
                '"modality":"CT","site":"Demo Hospital","report_text":"Impression: No acute abnormality."}'
            ),
        ]
    )

    response = client.post(
        "/api/v1/imports/reports",
        files={"file": ("reports.jsonl", payload, "application/x-ndjson")},
        headers=analyst_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] is not None
    assert body["processed"] == 2
    assert body["created"] == 2
    assert body["updated"] == 0
    assert body["failed"] == 0

    runs_response = client.get("/api/v1/imports/runs", headers=analyst_headers)
    assert runs_response.status_code == 200
    runs = runs_response.json()
    assert len(runs) == 1
    assert runs[0]["run_id"] == body["run_id"]
    assert runs[0]["actor_user_id"] == "import-analyst"
    assert runs[0]["actor_role"] == "analyst"
    assert runs[0]["source_format"] == "jsonl"
    assert runs[0]["imported_sites"] == ["Demo Hospital"]
    assert runs[0]["status"] == "completed"
    assert runs[0]["processed"] == 2

    detail_response = client.get(f"/api/v1/imports/runs/{body['run_id']}", headers=analyst_headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert len(detail["items"]) == 2
    assert detail["items"][0]["status"] == "imported"
    assert detail["items"][0]["case_id"] == "C-RUN-1"
    assert detail["items"][0]["report_id"] == "R-RUN-1"
    assert detail["items"][1]["case_id"] == "C-RUN-2"


def test_import_run_counts_updates_for_reimported_reports() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    analyst_headers = _auth_headers("import-updater")

    payload = (
        '{"report_id":"R-UPDATE-1","case_id":"C-UPDATE-1","report_datetime":"2026-03-19T10:00:00Z",'
        '"modality":"CT","site":"Demo Hospital","report_text":"Impression: Suspicious for pancreatic neoplasm."}'
    )

    first_response = client.post(
        "/api/v1/imports/reports",
        files={"file": ("reports.jsonl", payload, "application/x-ndjson")},
        headers=analyst_headers,
    )
    assert first_response.status_code == 200
    assert first_response.json()["created"] == 1

    second_response = client.post(
        "/api/v1/imports/reports",
        files={"file": ("reports.jsonl", payload, "application/x-ndjson")},
        headers=analyst_headers,
    )
    assert second_response.status_code == 200
    second_body = second_response.json()
    assert second_body["created"] == 0
    assert second_body["updated"] == 1

    detail_response = client.get(f"/api/v1/imports/runs/{second_body['run_id']}", headers=analyst_headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["created"] == 0
    assert detail["updated"] == 1
    assert detail["items"][0]["case_id"] == "C-UPDATE-1"
    assert detail["items"][0]["report_id"] == "R-UPDATE-1"


def test_successful_import_run_is_visible_to_other_scoped_actor() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    owner_headers = _auth_headers("demo-analyst", sites="Demo Hospital")

    response = client.post(
        "/api/v1/imports/reports",
        files={
            "file": (
                "reports.jsonl",
                (
                    '{"report_id":"R-SHARED-1","case_id":"C-SHARED-1","report_datetime":"2026-03-19T10:00:00Z",'
                    '"modality":"CT","site":"Demo Hospital","report_text":"Impression: Suspicious for pancreatic neoplasm."}'
                ),
                "application/x-ndjson",
            )
        },
        headers=owner_headers,
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    peer_headers = _auth_headers("peer-analyst", sites="Demo Hospital")
    peer_detail_response = client.get(f"/api/v1/imports/runs/{run_id}", headers=peer_headers)
    assert peer_detail_response.status_code == 200
    peer_detail = peer_detail_response.json()
    assert peer_detail["run_id"] == run_id
    assert peer_detail["actor_user_id"] == "demo-analyst"
    assert peer_detail["status"] == "completed"

    peer_runs_response = client.get("/api/v1/imports/runs", headers=peer_headers)
    assert peer_runs_response.status_code == 200
    peer_runs = peer_runs_response.json()
    assert any(run["run_id"] == run_id for run in peer_runs)


def test_fhir_import_run_is_visible_to_other_scoped_actor() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    owner_headers = _auth_headers("fhir-owner", sites="Demo Hospital")

    payload = {
        "resourceType": "DiagnosticReport",
        "id": "dr-shared-1",
        "effectiveDateTime": "2026-03-19T10:00:00Z",
        "category": [{"text": "CT abdomen"}],
        "performer": [{"display": "Demo Hospital"}],
        "conclusion": "Suspicious for pancreatic neoplasm. Recommend biopsy.",
    }

    response = client.post(
        "/api/v1/imports/fhir/diagnostic-reports",
        json=payload,
        headers=owner_headers,
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    peer_headers = _auth_headers("fhir-peer", sites="Demo Hospital")
    peer_detail_response = client.get(f"/api/v1/imports/runs/{run_id}", headers=peer_headers)
    assert peer_detail_response.status_code == 200
    peer_detail = peer_detail_response.json()
    assert peer_detail["run_id"] == run_id
    assert peer_detail["actor_user_id"] == "fhir-owner"
    assert peer_detail["source_format"] == "fhir-diagnostic-report"
    assert peer_detail["status"] == "completed"

    peer_runs_response = client.get("/api/v1/imports/runs", headers=peer_headers)
    assert peer_runs_response.status_code == 200
    peer_runs = peer_runs_response.json()
    assert any(run["run_id"] == run_id for run in peer_runs)


def test_hl7_import_run_is_visible_to_other_scoped_actor() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    owner_headers = _auth_headers("hl7-owner", sites="Demo Hospital")

    payload = "\r".join(
        [
            "MSH|^~\\&|RADSYS|Demo Hospital|PS|PS|20260319100000||ORU^R01|MSG-SHARED|P|2.5",
            "PID|1||PAT-SHARED^^^MRN||Doe^Jamie",
            "PV1|1|O|RAD^^^Demo Hospital",
            "OBR|1|PLAC-SHARED|R-HL7-SHARED|CT ABDOMEN^CT Abdomen|||20260319100000",
            "OBX|1|TX|IMPRESSION^Impression||Suspicious for pancreatic neoplasm. Recommend biopsy.|",
        ]
    )

    response = client.post(
        "/api/v1/imports/hl7/oru",
        content=payload,
        headers={"Content-Type": "text/plain", **owner_headers},
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    peer_headers = _auth_headers("hl7-peer", sites="Demo Hospital")
    peer_detail_response = client.get(f"/api/v1/imports/runs/{run_id}", headers=peer_headers)
    assert peer_detail_response.status_code == 200
    peer_detail = peer_detail_response.json()
    assert peer_detail["run_id"] == run_id
    assert peer_detail["actor_user_id"] == "hl7-owner"
    assert peer_detail["source_format"] == "hl7-oru"
    assert peer_detail["status"] == "completed"

    peer_runs_response = client.get("/api/v1/imports/runs", headers=peer_headers)
    assert peer_runs_response.status_code == 200
    peer_runs = peer_runs_response.json()
    assert any(run["run_id"] == run_id for run in peer_runs)


def test_import_run_records_validation_failure_bucket() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    analyst_headers = _auth_headers("validation-analyst")

    response = client.post(
        "/api/v1/imports/reports",
        files={"file": ("reports.jsonl", '{"report_id":"R-BAD-1","case_id":"C-BAD-1"}', "application/x-ndjson")},
        headers=analyst_headers,
    )
    assert response.status_code == 400
    assert response.headers["x-import-run-id"]
    run_id = int(response.headers["x-import-run-id"])

    runs_response = client.get("/api/v1/imports/runs", headers=analyst_headers)
    assert runs_response.status_code == 200
    runs = runs_response.json()
    assert len(runs) == 1
    assert runs[0]["status"] == "failed"
    assert runs[0]["source_format"] == "jsonl"
    assert runs[0]["run_id"] == run_id
    assert runs[0]["failed"] == 1
    assert runs[0]["failure_counts"]["validation_error"] == 1

    detail_response = client.get(f"/api/v1/imports/runs/{run_id}", headers=analyst_headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["failure_counts"]["validation_error"] == 1


def test_validation_failure_import_run_is_visible_to_other_scoped_actor() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    owner_headers = _auth_headers("validation-owner", sites="Demo Hospital")

    response = client.post(
        "/api/v1/imports/reports",
        files={
            "file": (
                "reports.jsonl",
                '{"report_id":"R-VAL-SHARED","case_id":"C-VAL-SHARED","site":"Demo Hospital"}',
                "application/x-ndjson",
            )
        },
        headers=owner_headers,
    )
    assert response.status_code == 400
    assert response.headers["x-import-run-id"]
    run_id = int(response.headers["x-import-run-id"])

    peer_headers = _auth_headers("validation-peer", sites="Demo Hospital")
    peer_detail_response = client.get(f"/api/v1/imports/runs/{run_id}", headers=peer_headers)
    assert peer_detail_response.status_code == 200
    peer_detail = peer_detail_response.json()
    assert peer_detail["run_id"] == run_id
    assert peer_detail["actor_user_id"] == "validation-owner"
    assert peer_detail["status"] == "failed"
    assert peer_detail["failure_counts"]["validation_error"] == 1
    assert peer_detail["items"] == []

    peer_runs_response = client.get("/api/v1/imports/runs", headers=peer_headers)
    assert peer_runs_response.status_code == 200
    peer_runs = peer_runs_response.json()
    assert any(run["run_id"] == run_id for run in peer_runs)


def test_import_run_records_unsupported_payload_failures() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    analyst_headers = _auth_headers("fhir-analyst")

    response = client.post(
        "/api/v1/imports/fhir/diagnostic-reports",
        json={"resourceType": "Observation", "id": "obs-only"},
        headers=analyst_headers,
    )
    assert response.status_code == 400
    assert response.headers["x-import-run-id"]
    run_id = int(response.headers["x-import-run-id"])

    runs_response = client.get("/api/v1/imports/runs", headers=analyst_headers)
    assert runs_response.status_code == 200
    run = runs_response.json()[0]
    assert run["status"] == "failed"
    assert run["run_id"] == run_id
    assert run["source_format"] == "fhir-diagnostic-report"
    assert run["failure_counts"]["unsupported_payload"] == 1


def test_import_run_records_site_scope_rejection_and_visibility() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    north_headers = _auth_headers("north-analyst", sites="North Clinic")

    response = client.post(
        "/api/v1/imports/reports",
        files={
            "file": (
                "reports.jsonl",
                (
                    '{"report_id":"R-SITE-FAIL","case_id":"C-SITE-FAIL","report_datetime":"2026-03-19T10:00:00Z",'
                    '"modality":"CT","site":"Demo Hospital","report_text":"Impression: Suspicious for pancreatic neoplasm."}'
                ),
                "application/x-ndjson",
            )
        },
        headers=north_headers,
    )
    assert response.status_code == 403
    assert response.headers["x-import-run-id"]
    run_id = int(response.headers["x-import-run-id"])

    own_run_response = client.get(f"/api/v1/imports/runs/{run_id}", headers=north_headers)
    assert own_run_response.status_code == 200
    own_run = own_run_response.json()
    assert own_run["failure_counts"]["site_scope_rejection"] == 1
    assert own_run["items"][0]["error_bucket"] == "site_scope_rejection"
    assert own_run["items"][0]["site"] == "Demo Hospital"

    other_scoped_response = client.get(
        f"/api/v1/imports/runs/{run_id}",
        headers=_auth_headers("other-north-analyst", sites="North Clinic"),
    )
    assert other_scoped_response.status_code == 404


def test_viewer_cannot_access_import_run_audit_routes() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    viewer_headers = _auth_headers("viewer-1", role="viewer")

    list_response = client.get("/api/v1/imports/runs", headers=viewer_headers)
    assert list_response.status_code == 403

    detail_response = client.get("/api/v1/imports/runs/1", headers=viewer_headers)
    assert detail_response.status_code == 403
