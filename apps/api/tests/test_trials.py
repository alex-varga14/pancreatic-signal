from fastapi.testclient import TestClient

from app.main import app
from app.store.memory_store import CASE_STORE


def _triage_case(client: TestClient, *, case_id: str, report_id: str, report_text: str) -> None:
    response = client.post(
        "/api/v1/triage/report",
        json={
            "report_id": report_id,
            "case_id": case_id,
            "report_datetime": "2026-03-19T10:00:00Z",
            "modality": "CT",
            "site": "Demo Hospital",
            "report_text": report_text,
        },
    )
    assert response.status_code == 200


def test_trial_matching_returns_explainable_candidates_for_suspicious_case() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_case(
        client,
        case_id="C-TRIAL-1",
        report_id="R-TRIAL-1",
        report_text=(
            "Findings: There is abrupt cutoff of the pancreatic duct with an "
            "ill-defined pancreatic head lesion. Impression: Findings are "
            "suspicious for pancreatic neoplasm. Recommend endoscopic ultrasound "
            "with tissue sampling."
        ),
    )

    response = client.get("/api/v1/trials/match/C-TRIAL-1")
    assert response.status_code == 200
    payload = response.json()

    assert payload["case_id"] == "C-TRIAL-1"
    assert payload["abstraction"]["suspected_pdac"] is True
    assert payload["abstraction"]["pancreatic_head_focus"] is True
    assert payload["abstraction"]["needs_tissue_confirmation"] is True
    assert len(payload["matches"]) >= 2
    assert payload["matches"][0]["match_status"] in {"potential", "strong"}
    assert any(candidate["trial_id"] == "PDAC-HEAD-002" for candidate in payload["matches"])
    assert any(
        trace["status"] == "met"
        for candidate in payload["matches"]
        for trace in candidate["criteria"]
    )


def test_trial_matching_returns_no_candidates_for_benign_case() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_case(
        client,
        case_id="C-TRIAL-2",
        report_id="R-TRIAL-2",
        report_text=(
            "Findings: Pancreas is unremarkable. No pancreatic duct dilation. "
            "Impression: No acute abnormality."
        ),
    )

    response = client.get("/api/v1/trials/match/C-TRIAL-2")
    assert response.status_code == 200
    payload = response.json()

    assert payload["abstraction"]["high_risk_pancreatic_signal"] is False
    assert payload["abstraction"]["localized_disease_suspected"] is False
    assert payload["matches"] == []
