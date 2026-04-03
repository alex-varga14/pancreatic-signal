from fastapi.testclient import TestClient

from app.main import app
from app.store.memory_store import CASE_STORE


def _auth_headers(user_id: str, role: str = "admin") -> dict[str, str]:
    return {"X-User-ID": user_id, "X-User-Role": role}


def _triage_case(client: TestClient, *, case_id: str, report_id: str) -> None:
    response = client.post(
        "/api/v1/triage/report",
        json={
            "report_id": report_id,
            "case_id": case_id,
            "report_datetime": "2026-03-19T10:00:00Z",
            "modality": "CT",
            "site": "Demo Hospital",
            "report_text": (
                "Findings: Abrupt cutoff of the pancreatic duct with focal atrophy. "
                "Impression: Suspicious for pancreatic neoplasm. Recommend EUS and biopsy."
            ),
        },
    )
    assert response.status_code == 200


def test_research_intel_ingest_digest_and_promotion_routes() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    response = client.get("/api/v1/research-intel/sources")
    assert response.status_code == 200
    assert any(item["source_id"] == "pubmed" for item in response.json())

    response = client.post(
        "/api/v1/research-intel/runs/ingest",
        json={"write_artifacts": True},
        headers=_auth_headers("research-admin"),
    )
    assert response.status_code == 200
    run_payload = response.json()["run"]
    assert run_payload["run_type"] == "ingest"
    assert run_payload["processed"] >= 6
    assert run_payload["created"] >= 6
    assert len(run_payload["items"]) == run_payload["processed"]

    response = client.get(
        "/api/v1/research-intel/runs",
        headers=_auth_headers("research-admin"),
    )
    assert response.status_code == 200
    assert response.json()[0]["run_type"] == "ingest"

    response = client.get("/api/v1/research-intel/documents")
    assert response.status_code == 200
    documents = response.json()
    assert any(item["nct_id"] == "NCT06001234" for item in documents)
    assert any("early_detection" in item["topic_ids"] for item in documents)

    response = client.post(
        "/api/v1/research-intel/runs/digest",
        json={"publish": True, "write_artifacts": True},
        headers=_auth_headers("research-admin"),
    )
    assert response.status_code == 200
    digest_run = response.json()["run"]
    assert digest_run["run_type"] == "digest"
    assert digest_run["created"] >= 1

    response = client.get("/api/v1/research-intel/digests")
    assert response.status_code == 200
    digests = response.json()
    assert len(digests) == 1
    digest_id = digests[0]["digest_id"]

    response = client.get(f"/api/v1/research-intel/digests/{digest_id}")
    assert response.status_code == 200
    digest = response.json()
    assert digest["supporting_documents"]
    assert len(digest["council"]["stage_1"]) == 3
    assert digest["council"]["stage_3"]["recommended_actions"]

    response = client.get("/api/v1/research-intel/opportunities")
    assert response.status_code == 200
    opportunities = response.json()
    assert opportunities
    opportunity_id = opportunities[0]["opportunity_id"]

    promote_response = client.post(
        f"/api/v1/research-intel/opportunities/{opportunity_id}/promote",
        json={"target": "docs_draft"},
        headers=_auth_headers("research-admin"),
    )
    assert promote_response.status_code == 200
    assert promote_response.json()["status"] == "promoted"
    assert promote_response.json()["artifact_path"]


def test_research_intel_case_brief_maps_case_to_topics_and_documents() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    ingest_response = client.post(
        "/api/v1/research-intel/runs/ingest",
        json={"write_artifacts": False},
        headers=_auth_headers("research-admin"),
    )
    assert ingest_response.status_code == 200

    digest_response = client.post(
        "/api/v1/research-intel/runs/digest",
        json={"publish": True, "write_artifacts": False},
        headers=_auth_headers("research-admin"),
    )
    assert digest_response.status_code == 200

    _triage_case(client, case_id="C-RI-1", report_id="R-RI-1")

    response = client.get(
        "/api/v1/research-intel/cases/C-RI-1/brief",
        headers=_auth_headers("reviewer-a", "reviewer"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["matched_topics"]
    assert payload["supporting_documents"]
    assert "case score automatically" in payload["summary"]


def test_research_intel_documents_support_filters_and_viewer_cannot_trigger_runs() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    response = client.post(
        "/api/v1/research-intel/runs/ingest",
        json={"write_artifacts": False},
        headers=_auth_headers("viewer-a", "viewer"),
    )
    assert response.status_code == 403

    response = client.post(
        "/api/v1/research-intel/runs/ingest",
        json={"write_artifacts": False},
        headers=_auth_headers("research-admin"),
    )
    assert response.status_code == 200

    response = client.get("/api/v1/research-intel/documents", params={"source_kind": "preprint"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["source_kind"] == "preprint"

    response = client.get("/api/v1/research-intel/documents", params={"topic": "oss_opportunities"})
    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert all("oss_opportunities" in item["topic_ids"] for item in payload)
