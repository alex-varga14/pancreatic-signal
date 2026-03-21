from fastapi.testclient import TestClient

from app.main import app
from app.store.memory_store import CASE_STORE


def _triage_report(
    client: TestClient,
    *,
    report_id: str,
    case_id: str,
    site: str,
    report_text: str,
    report_datetime: str = "2026-03-19T10:00:00Z",
    modality: str = "CT",
    import_metadata: dict[str, str] | None = None,
) -> None:
    payload = {
        "report_id": report_id,
        "case_id": case_id,
        "report_datetime": report_datetime,
        "modality": modality,
        "site": site,
        "report_text": report_text,
    }
    if import_metadata is not None:
        payload["import_metadata"] = import_metadata

    response = client.post(
        "/api/v1/triage/report",
        json=payload,
    )
    assert response.status_code == 200


def _auth_headers(user_id: str, role: str = "reviewer") -> dict[str, str]:
    return {"X-User-ID": user_id, "X-User-Role": role}


def test_case_list_supports_filters_and_pagination() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_report(
        client,
        report_id="R-CASE-1",
        case_id="C-CASE-1",
        site="Demo Hospital",
        report_datetime="2026-03-19T12:00:00Z",
        report_text=(
            "Findings: Abrupt cutoff of the pancreatic duct with an ill-defined "
            "pancreatic head lesion. Impression: Findings are suspicious for "
            "pancreatic neoplasm."
        ),
    )
    _triage_report(
        client,
        report_id="R-CASE-2",
        case_id="C-CASE-2",
        site="North Clinic",
        report_datetime="2026-03-18T08:00:00Z",
        modality="MRI",
        report_text=(
            "Findings: Double duct sign is present with focal pancreatic atrophy. "
            "Impression: Recommend EUS for further evaluation."
        ),
    )
    _triage_report(
        client,
        report_id="R-CASE-3",
        case_id="C-CASE-3",
        site="Demo Hospital",
        report_datetime="2026-03-17T08:00:00Z",
        report_text="Findings: Pancreas is unremarkable. Impression: No acute abnormality.",
    )

    response = client.post(
        "/api/v1/cases/C-CASE-1/review",
        json={"action": "assign", "assigned_to": "navigator-a"},
        headers=_auth_headers("alex"),
    )
    assert response.status_code == 200

    response = client.post(
        "/api/v1/cases/C-CASE-1/review",
        json={"action": "escalate", "note": "High-risk morphology."},
        headers=_auth_headers("alex"),
    )
    assert response.status_code == 200

    response = client.post(
        "/api/v1/cases/C-CASE-2/review",
        json={"action": "in_review"},
        headers=_auth_headers("sam"),
    )
    assert response.status_code == 200

    response = client.get("/api/v1/cases", params={"status": "escalated"})
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == ["C-CASE-1"]
    assert payload[0]["assigned_to"] == "navigator-a"

    response = client.get("/api/v1/cases", params={"reviewer": "alex"})
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == ["C-CASE-1"]

    response = client.get("/api/v1/cases", params={"site": "North Clinic"})
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == ["C-CASE-2"]

    response = client.get("/api/v1/cases", params={"modality": "MRI"})
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == ["C-CASE-2"]

    response = client.get("/api/v1/cases", params={"rationale": "DOUBLE_DUCT_SIGN"})
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == ["C-CASE-2"]

    response = client.get("/api/v1/cases", params={"q": "R-CASE-1"})
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == ["C-CASE-1"]

    response = client.get("/api/v1/cases", params={"sort_by": "report_datetime", "sort_dir": "asc"})
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == ["C-CASE-3", "C-CASE-2", "C-CASE-1"]

    response = client.get("/api/v1/cases", params={"limit": 1, "offset": 1})
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == ["C-CASE-2"]


def test_review_actions_update_assignment_and_status() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_report(
        client,
        report_id="R-REVIEW-1",
        case_id="C-REVIEW-1",
        site="Demo Hospital",
        report_text="Impression: Suspicious for pancreatic neoplasm. Recommend biopsy.",
    )

    response = client.post(
        "/api/v1/cases/C-REVIEW-1/review",
        json={"action": "assign", "assigned_to": "navigator-b"},
        headers=_auth_headers("alex"),
    )
    assert response.status_code == 200
    assert response.json()["assigned_to"] == "navigator-b"
    assert response.json()["status"] == "new"

    response = client.post(
        "/api/v1/cases/C-REVIEW-1/review",
        json={"action": "dismiss", "note": "False positive after review."},
        headers=_auth_headers("alex"),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "dismissed"

    response = client.post(
        "/api/v1/cases/C-REVIEW-1/review",
        json={"action": "reopen", "note": "Re-evaluating based on addendum."},
        headers=_auth_headers("alex"),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "new"

    response = client.get("/api/v1/cases/C-REVIEW-1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["assigned_to"] == "navigator-b"
    assert payload["status"] == "new"
    assert payload["modality"] == "CT"
    assert payload["report_datetime"].startswith("2026-03-19T10:00:00")
    assert [item["action"] for item in payload["review_actions"]] == ["assign", "dismiss", "reopen"]


def test_research_case_view_redacts_phi_and_preserves_evidence_offsets() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    report_text = (
        "Patient Name: John Doe. MRN: 12345678. Findings: Abrupt cutoff of the pancreatic duct with an "
        "ill-defined pancreatic head lesion. Impression: Suspicious for pancreatic neoplasm. "
        "Recommend biopsy."
    )

    _triage_report(
        client,
        report_id="R-RESEARCH-1",
        case_id="C-RESEARCH-1",
        site="Demo Hospital",
        report_text=report_text,
        import_metadata={
            "patient_identifier": "MRN-123456",
            "encounter_identifier": "ENC-654321",
            "accession_number": "ACC-112233",
            "ordering_provider": "Dr. Jane Smith",
            "source_system": "RADSYS",
            "source_format": "hl7-oru",
            "import_source_id": "MSG-9",
        },
    )

    review_response = client.post(
        "/api/v1/cases/C-RESEARCH-1/review",
        json={"action": "assign", "assigned_to": "navigator-a", "note": "Call John Doe at 780-555-1212."},
        headers=_auth_headers("alex"),
    )
    assert review_response.status_code == 200

    feedback_response = client.post(
        "/api/v1/cases/C-RESEARCH-1/feedback",
        json={
            "label": "true_positive",
            "disposition": "escalate",
            "notes": "Patient John Doe reviewed on 2026-03-19.",
        },
        headers=_auth_headers("alex"),
    )
    assert feedback_response.status_code == 200

    response = client.get("/api/v1/cases/C-RESEARCH-1/research")
    assert response.status_code == 200
    payload = response.json()

    assert payload["case_id"] != "C-RESEARCH-1"
    assert payload["report_id"] != "R-RESEARCH-1"
    assert payload["deidentified"] is True
    assert payload["report_date"] == "2026-03-19"
    assert len(payload["report_text"]) == len(report_text)
    assert payload["import_metadata"]["patient_identifier"] != "MRN-123456"
    assert payload["import_metadata"]["encounter_identifier"] != "ENC-654321"
    assert payload["import_metadata"]["accession_number"] != "ACC-112233"
    assert payload["import_metadata"]["ordering_provider"] != "Dr. Jane Smith"
    assert payload["import_metadata"]["source_system"] == "RADSYS"
    assert payload["import_metadata"]["source_format"] == "hl7-oru"
    assert payload["import_metadata"]["import_source_id"] != "MSG-9"
    assert "John Doe" not in payload["report_text"]
    assert "12345678" not in payload["report_text"]
    assert "780-555-1212" not in payload["review_actions"][0]["note"]
    assert payload["review_actions"][0]["reviewer"] != "alex"
    assert payload["review_actions"][0]["assigned_to"] != "navigator-a"
    assert payload["review_feedback"][0]["reviewer"] != "alex"
    assert "2026-03-19" not in (payload["review_feedback"][0]["notes"] or "")
    assert payload["redaction_summary"]["redaction_count"] >= 4
    assert "case_id" in payload["redaction_summary"]["pseudonymized_fields"]
    assert "import_metadata.patient_identifier" in payload["redaction_summary"]["pseudonymized_fields"]
    assert "review_feedback.reviewer" in payload["redaction_summary"]["pseudonymized_fields"]
    first_evidence = payload["evidence"][0]
    assert payload["report_text"][first_evidence["start"]:first_evidence["end"]] == first_evidence["text"]


def test_research_case_list_returns_pseudonymized_identifiers() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_report(
        client,
        report_id="R-RESEARCH-LIST-1",
        case_id="C-RESEARCH-LIST-1",
        site="Demo Hospital",
        report_text="Impression: Suspicious for pancreatic neoplasm. Recommend biopsy.",
    )

    response = client.get("/api/v1/cases/research", params={"include_hybrid": True})
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["case_id"] != "C-RESEARCH-LIST-1"
    assert payload[0]["report_id"] != "R-RESEARCH-LIST-1"
    assert payload[0]["report_date"] == "2026-03-19"
    assert payload[0]["deidentified"] is True


def test_case_hybrid_analysis_endpoint_returns_explainable_sentence_ranking() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_report(
        client,
        report_id="R-HYBRID-CASE-1",
        case_id="C-HYBRID-CASE-1",
        site="Demo Hospital",
        report_text=(
            "Findings: Double duct sign is present with focal pancreatic atrophy. "
            "Impression: Occult pancreatic malignancy cannot be excluded. Recommend EUS."
        ),
    )

    response = client.get("/api/v1/cases/C-HYBRID-CASE-1/hybrid")
    assert response.status_code == 200

    payload = response.json()
    assert payload["calibrated_score"] >= 0.45
    assert payload["review_priority"] in {"review", "expedite"}
    assert payload["active_learning_priority"] in {"medium", "high"}
    assert len(payload["sentence_candidates"]) >= 1
    assert any(candidate["matched_codes"] for candidate in payload["sentence_candidates"])


def test_case_list_supports_hybrid_filters_and_sorting() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_report(
        client,
        report_id="R-HWORK-1",
        case_id="C-HWORK-1",
        site="Demo Hospital",
        report_text=(
            "Findings: Abrupt cutoff of the pancreatic duct with an ill-defined pancreatic head lesion. "
            "Impression: Findings are suspicious for pancreatic neoplasm."
        ),
    )
    _triage_report(
        client,
        report_id="R-HWORK-2",
        case_id="C-HWORK-2",
        site="Demo Hospital",
        report_text=(
            "Findings: Cystic lesion in the pancreatic tail measuring 1.2 cm without suspicious enhancement. "
            "Impression: Likely side-branch IPMN; recommend routine imaging follow-up."
        ),
    )
    _triage_report(
        client,
        report_id="R-HWORK-3",
        case_id="C-HWORK-3",
        site="Demo Hospital",
        report_text="Findings: Pancreas is unremarkable. Impression: No acute abnormality.",
    )

    response = client.get("/api/v1/cases", params={"include_hybrid": True, "hybrid_review_priority": "review"})
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == ["C-HWORK-2"]
    assert payload[0]["hybrid_score"] >= 0.3
    assert payload[0]["active_learning_priority"] == "high"

    response = client.get(
        "/api/v1/cases",
        params={"include_hybrid": True, "active_learning_only": True, "sort_by": "hybrid_score", "sort_dir": "desc"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == ["C-HWORK-1", "C-HWORK-2"]
    assert payload[0]["hybrid_score"] >= payload[1]["hybrid_score"]


def test_case_list_supports_disagreement_queue_filters() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_report(
        client,
        report_id="R-DISAGREE-1",
        case_id="C-DISAGREE-1",
        site="Demo Hospital",
        report_text=(
            "Findings: Cystic lesion in the pancreatic tail measuring 1.2 cm without suspicious enhancement. "
            "Impression: Likely side-branch IPMN; recommend routine imaging follow-up."
        ),
    )
    _triage_report(
        client,
        report_id="R-DISAGREE-2",
        case_id="C-DISAGREE-2",
        site="Demo Hospital",
        report_text=(
            "Findings: Abrupt cutoff of the pancreatic duct with an ill-defined pancreatic head lesion. "
            "Impression: Findings are suspicious for pancreatic neoplasm."
        ),
    )
    _triage_report(
        client,
        report_id="R-DISAGREE-3",
        case_id="C-DISAGREE-3",
        site="Demo Hospital",
        report_text="Findings: Pancreas is unremarkable. Impression: No acute abnormality.",
    )

    response = client.get(
        "/api/v1/cases",
        params={
            "include_hybrid": True,
            "disagreement_only": True,
            "hybrid_delta_min": 0.2,
            "sort_by": "hybrid_delta",
            "sort_dir": "desc",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == ["C-DISAGREE-1"]
    assert payload[0]["hybrid_delta"] >= 0.2
    assert payload[0]["disagreement_level"] == "high"


def test_case_feedback_endpoint_persists_structured_labels() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_report(
        client,
        report_id="R-FEEDBACK-1",
        case_id="C-FEEDBACK-1",
        site="Demo Hospital",
        report_text="Impression: Suspicious for pancreatic neoplasm. Recommend biopsy.",
    )

    response = client.post(
        "/api/v1/cases/C-FEEDBACK-1/feedback",
        json={
            "label": "true_positive",
            "disposition": "escalate",
            "error_bucket": "secondary_signs_only",
            "notes": "Navigator outreach started.",
        },
        headers=_auth_headers("alex"),
    )
    assert response.status_code == 200
    assert response.json()["label"] == "true_positive"

    response = client.get("/api/v1/cases/C-FEEDBACK-1/feedback")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["reviewer"] == "alex"
    assert payload[0]["disposition"] == "escalate"

    response = client.get("/api/v1/cases/C-FEEDBACK-1")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["review_feedback"]) == 1
    assert payload["review_feedback"][0]["label"] == "true_positive"
    assert any(item["action"] == "feedback" for item in payload["review_actions"])
    assert "label=true_positive" in payload["review_actions"][-1]["note"]


def test_case_feedback_recommendation_prefills_explicit_suspicion() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_report(
        client,
        report_id="R-RECO-1",
        case_id="C-RECO-1",
        site="Demo Hospital",
        report_text=(
            "Findings: Abrupt cutoff of the pancreatic duct with an ill-defined pancreatic head lesion. "
            "Impression: Findings are suspicious for pancreatic neoplasm. Recommend biopsy."
        ),
    )

    response = client.get("/api/v1/cases/C-RECO-1/feedback/recommendation")
    assert response.status_code == 200
    payload = response.json()
    assert payload["recommended_label"] == "true_positive"
    assert payload["recommended_disposition"] == "escalate"
    assert payload["confidence"] in {"high", "moderate"}
    assert payload["already_labeled"] is False


def test_case_feedback_recommendation_prefills_incidental_followup() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_report(
        client,
        report_id="R-RECO-2",
        case_id="C-RECO-2",
        site="Demo Hospital",
        report_text=(
            "Findings: Cystic lesion in the pancreatic tail measuring 1.2 cm without suspicious enhancement. "
            "Impression: Likely side-branch IPMN; recommend routine imaging follow-up."
        ),
    )

    response = client.get("/api/v1/cases/C-RECO-2/feedback/recommendation")
    assert response.status_code == 200
    payload = response.json()
    assert payload["recommended_label"] == "actionable_followup"
    assert payload["recommended_disposition"] == "routine_followup"
    assert payload["recommended_error_bucket"] == "incidental_cyst"


def test_case_feedback_recommendation_anchors_existing_label() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_report(
        client,
        report_id="R-RECO-3",
        case_id="C-RECO-3",
        site="Demo Hospital",
        report_text="Impression: Suspicious for pancreatic neoplasm. Recommend biopsy.",
    )
    response = client.post(
        "/api/v1/cases/C-RECO-3/feedback",
        json={
            "label": "false_positive",
            "disposition": "dismiss",
            "notes": "Reviewed against prior imaging.",
        },
        headers=_auth_headers("alex"),
    )
    assert response.status_code == 200

    response = client.get("/api/v1/cases/C-RECO-3/feedback/recommendation")
    assert response.status_code == 200
    payload = response.json()
    assert payload["already_labeled"] is True
    assert payload["recommended_label"] == "false_positive"
    assert payload["recommended_disposition"] == "dismiss"


def test_case_list_supports_feedback_filters() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_report(
        client,
        report_id="R-FILTER-FEEDBACK-1",
        case_id="C-FILTER-FEEDBACK-1",
        site="Demo Hospital",
        report_text="Impression: Suspicious for pancreatic neoplasm. Recommend biopsy.",
    )
    _triage_report(
        client,
        report_id="R-FILTER-FEEDBACK-2",
        case_id="C-FILTER-FEEDBACK-2",
        site="Demo Hospital",
        report_text="Findings: Cystic lesion in the pancreatic tail. Impression: Recommend routine imaging follow-up.",
    )

    response = client.post(
        "/api/v1/cases/C-FILTER-FEEDBACK-1/feedback",
        json={
            "label": "true_positive",
            "disposition": "escalate",
        },
        headers=_auth_headers("alex"),
    )
    assert response.status_code == 200

    response = client.get("/api/v1/cases", params={"feedback_label": "true_positive"})
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == ["C-FILTER-FEEDBACK-1"]
    assert payload[0]["review_feedback_count"] == 1
    assert payload[0]["latest_feedback_label"] == "true_positive"

    response = client.get("/api/v1/cases", params={"needs_feedback": True, "sort_by": "case_id", "sort_dir": "asc"})
    assert response.status_code == 200
    payload = response.json()
    assert [item["case_id"] for item in payload] == ["C-FILTER-FEEDBACK-2"]
