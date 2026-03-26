from fastapi.testclient import TestClient

from app.main import app
from app.store.memory_store import CASE_STORE


def _triage_demo_case(
    client: TestClient,
    case_id: str,
    report_id: str,
    report_text: str,
    *,
    site: str = "Demo Hospital",
    import_metadata: dict[str, str] | None = None,
) -> None:
    payload = {
        "report_id": report_id,
        "case_id": case_id,
        "report_datetime": "2026-03-19T10:00:00Z",
        "modality": "CT",
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


def _scoped_headers(user_id: str, role: str, sites: str) -> dict[str, str]:
    return {"X-User-ID": user_id, "X-User-Role": role, "X-User-Sites": sites}


def test_export_cases_csv_returns_expected_columns() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_demo_case(
        client,
        case_id="C-EXPORT-1",
        report_id="R-EXPORT-1",
        report_text="Impression: Suspicious for pancreatic neoplasm. Recommend biopsy.",
        import_metadata={
            "patient_identifier": "PAT-EXPORT-1",
            "encounter_identifier": "ENC-EXPORT-1",
            "accession_number": "ACC-EXPORT-1",
            "ordering_provider": "Dr. Jamie Patel",
            "source_system": "RADSYS",
            "source_format": "hl7-oru",
            "import_source_id": "MSG-EXPORT-1",
        },
    )

    response = client.get("/api/v1/exports/cases.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "case_id,report_id,report_datetime,modality,patient_identifier,encounter_identifier,accession_number,ordering_provider,source_system,source_format,import_source_id,score,hybrid_score,hybrid_delta,urgency,disagreement_level,status,site,assigned_to,top_rationale,review_feedback_count" in response.text
    assert "C-EXPORT-1" in response.text
    assert "Demo Hospital" in response.text
    assert "PAT-EXPORT-1" in response.text
    assert "RADSYS" in response.text


def test_export_cases_csv_supports_redacted_mode() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_demo_case(
        client,
        case_id="C-EXPORT-RESEARCH-1",
        report_id="R-EXPORT-RESEARCH-1",
        report_text="Patient Name: John Doe. Impression: Suspicious for pancreatic neoplasm. Recommend biopsy.",
        import_metadata={
            "patient_identifier": "PAT-EXPORT-RESEARCH-1",
            "encounter_identifier": "ENC-EXPORT-RESEARCH-1",
            "accession_number": "ACC-EXPORT-RESEARCH-1",
            "ordering_provider": "Dr. Research User",
            "source_system": "RADSYS",
            "source_format": "hl7-oru",
            "import_source_id": "MSG-EXPORT-RESEARCH-1",
        },
    )
    assign_response = client.post(
        "/api/v1/cases/C-EXPORT-RESEARCH-1/review",
        json={"action": "assign", "assigned_to": "navigator-a"},
        headers=_auth_headers("alex"),
    )
    assert assign_response.status_code == 200

    response = client.get("/api/v1/exports/cases.csv", params={"redact": "true"})
    assert response.status_code == 200
    assert "C-EXPORT-RESEARCH-1" not in response.text
    assert "R-EXPORT-RESEARCH-1" not in response.text
    assert "navigator-a" not in response.text
    assert "PAT-EXPORT-RESEARCH-1" not in response.text
    assert "ACC-EXPORT-RESEARCH-1" not in response.text
    assert "Dr. Research User" not in response.text
    assert "MSG-EXPORT-RESEARCH-1" not in response.text
    assert "case_" in response.text
    assert "patient_" in response.text
    assert "accession_" in response.text
    assert "provider_" in response.text
    assert "source_" in response.text
    assert "deidentified" in response.text
    assert "True" in response.text


def test_demo_evaluation_metrics_endpoint_returns_summary() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    response = client.get("/api/v1/metrics/evaluation", params={"threshold": 0.3, "top_k": 3})
    assert response.status_code == 200

    payload = response.json()
    assert payload["score_mode"] == "rules"
    assert payload["processed"] == 10
    assert payload["positives"] == 7
    assert payload["flagged"] == 5
    assert "precision" in payload
    assert "recall" in payload
    assert "precision_at_top_k" in payload
    assert len(payload["cases"]) == 10
    assert "base_score" in payload["cases"][0]
    assert "hybrid_score" in payload["cases"][0]
    assert "benchmark_bucket" in payload["cases"][0]
    assert "reviewer_focus" in payload["cases"][0]
    assert "expected_rationale_codes" in payload["cases"][0]


def test_demo_evaluation_supports_hybrid_score_mode() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    response = client.get("/api/v1/metrics/evaluation", params={"threshold": 0.3, "top_k": 5, "score_mode": "hybrid"})
    assert response.status_code == 200

    payload = response.json()
    assert payload["score_mode"] == "hybrid"
    assert payload["processed"] == 10
    assert payload["flagged"] == 7
    case_by_id = {case["case_id"]: case for case in payload["cases"]}
    assert case_by_id["C-003"]["benchmark_bucket"] == "secondary signs"
    assert "DOUBLE_DUCT_SIGN" in case_by_id["C-003"]["expected_rationale_codes"]
    assert case_by_id["C-005"]["benchmark_bucket"] == "follow-up only"
    assert case_by_id["C-005"]["hybrid_score"] > case_by_id["C-005"]["base_score"]
    assert case_by_id["C-008"]["benchmark_bucket"] == "follow-up only"
    assert "FOLLOWUP_RECOMMENDED" in case_by_id["C-008"]["expected_rationale_codes"]
    assert case_by_id["C-009"]["benchmark_bucket"] == "pancreatitis confounder"


def test_demo_evaluation_compare_endpoint_returns_deltas() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    response = client.get("/api/v1/metrics/evaluation/compare", params={"threshold": 0.3, "top_k": 5})
    assert response.status_code == 200

    payload = response.json()
    assert payload["rules"]["score_mode"] == "rules"
    assert payload["hybrid"]["score_mode"] == "hybrid"
    assert payload["flagged_delta"] == 2
    assert payload["recall_delta"] >= 0
    assert payload["newly_flagged_cases"] == ["C-005", "C-008"]
    assert payload["resolved_false_negatives"] == ["C-005", "C-008"]


def test_demo_evaluation_sweep_endpoint_returns_recommendations() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    response = client.get("/api/v1/metrics/evaluation/sweep", params={"top_k": 5, "thresholds": "0.2,0.3,0.4,0.5"})
    assert response.status_code == 200

    payload = response.json()
    assert payload["top_k"] == 5
    assert payload["thresholds"] == [0.2, 0.3, 0.4, 0.5]
    assert len(payload["points"]) == 4
    assert payload["rules_recommendation"]["score_mode"] == "rules"
    assert payload["hybrid_recommendation"]["score_mode"] == "hybrid"
    assert any(point["recall_delta"] >= 0 for point in payload["points"])


def test_review_feedback_jsonl_export_returns_labeled_rows() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_demo_case(
        client,
        case_id="C-FEEDBACK-EXPORT-1",
        report_id="R-FEEDBACK-EXPORT-1",
        report_text="Impression: Suspicious for pancreatic neoplasm. Recommend biopsy.",
        import_metadata={
            "patient_identifier": "PAT-FEEDBACK-1",
            "accession_number": "ACC-FEEDBACK-1",
            "source_system": "RADSYS",
            "source_format": "hl7-oru",
            "import_source_id": "MSG-FEEDBACK-1",
        },
    )
    response = client.post(
        "/api/v1/cases/C-FEEDBACK-EXPORT-1/feedback",
        json={
            "label": "true_positive",
            "disposition": "escalate",
            "error_bucket": "other",
            "notes": "Escalated to navigator.",
        },
        headers=_auth_headers("alex"),
    )
    assert response.status_code == 200

    response = client.get("/api/v1/exports/review-feedback.jsonl")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert '"case_id": "C-FEEDBACK-EXPORT-1"' in response.text
    assert '"label": "true_positive"' in response.text
    assert '"patient_identifier": "PAT-FEEDBACK-1"' in response.text
    assert '"import_source_id": "MSG-FEEDBACK-1"' in response.text
    assert '"hybrid_review_priority":' in response.text


def test_review_feedback_jsonl_export_supports_redacted_mode() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_demo_case(
        client,
        case_id="C-FEEDBACK-RESEARCH-1",
        report_id="R-FEEDBACK-RESEARCH-1",
        report_text=(
            "Patient Name: John Doe. MRN: 12345678. Impression: Suspicious for pancreatic neoplasm. "
            "Recommend biopsy."
        ),
        import_metadata={
            "patient_identifier": "PAT-FEEDBACK-RESEARCH-1",
            "encounter_identifier": "ENC-FEEDBACK-RESEARCH-1",
            "accession_number": "ACC-FEEDBACK-RESEARCH-1",
            "ordering_provider": "Dr. Jane Smith",
            "source_system": "RADSYS",
            "source_format": "hl7-oru",
            "import_source_id": "MSG-FEEDBACK-RESEARCH-1",
        },
    )
    feedback_response = client.post(
        "/api/v1/cases/C-FEEDBACK-RESEARCH-1/feedback",
        json={
            "label": "true_positive",
            "disposition": "escalate",
            "notes": "Patient John Doe called back at 780-555-1212.",
        },
        headers=_auth_headers("alex"),
    )
    assert feedback_response.status_code == 200

    response = client.get("/api/v1/exports/review-feedback.jsonl", params={"redact": "true"})
    assert response.status_code == 200
    assert '"deidentified": true' in response.text
    assert '"redaction_summary":' in response.text
    assert "John Doe" not in response.text
    assert "12345678" not in response.text
    assert "780-555-1212" not in response.text
    assert "PAT-FEEDBACK-RESEARCH-1" not in response.text
    assert "ENC-FEEDBACK-RESEARCH-1" not in response.text
    assert "ACC-FEEDBACK-RESEARCH-1" not in response.text
    assert "Dr. Jane Smith" not in response.text
    assert "MSG-FEEDBACK-RESEARCH-1" not in response.text
    assert '"patient_identifier": "patient_' in response.text
    assert '"encounter_identifier": "encounter_' in response.text
    assert '"accession_number": "accession_' in response.text
    assert '"ordering_provider": "provider_' in response.text
    assert '"import_source_id": "source_' in response.text
    assert '"reviewer": "user_' in response.text


def test_feedback_summary_endpoint_returns_label_coverage() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_demo_case(
        client,
        case_id="C-FEEDBACK-SUMMARY-1",
        report_id="R-FEEDBACK-SUMMARY-1",
        report_text="Impression: Suspicious for pancreatic neoplasm. Recommend biopsy.",
    )
    _triage_demo_case(
        client,
        case_id="C-FEEDBACK-SUMMARY-2",
        report_id="R-FEEDBACK-SUMMARY-2",
        report_text="Findings: Cystic lesion in the pancreatic tail. Impression: Recommend routine imaging follow-up.",
    )
    response = client.post(
        "/api/v1/cases/C-FEEDBACK-SUMMARY-1/feedback",
        json={
            "label": "true_positive",
            "disposition": "escalate",
            "error_bucket": "other",
        },
        headers=_auth_headers("alex"),
    )
    assert response.status_code == 200

    response = client.get("/api/v1/metrics/feedback")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_feedback"] == 1
    assert payload["labeled_cases"] == 1
    assert payload["unlabeled_cases"] == 1
    assert payload["unlabeled_active_learning_cases"] >= 1
    assert payload["label_distribution"]["true_positive"] == 1


def test_feedback_summary_and_exports_respect_site_scope() -> None:
    CASE_STORE.reset()
    client = TestClient(app)

    _triage_demo_case(
        client,
        case_id="C-SCOPED-EXPORT-1",
        report_id="R-SCOPED-EXPORT-1",
        report_text="Impression: Suspicious for pancreatic neoplasm. Recommend biopsy.",
    )
    _triage_demo_case(
        client,
        case_id="C-SCOPED-EXPORT-2",
        report_id="R-SCOPED-EXPORT-2",
        report_text="Findings: Cystic lesion in the pancreatic tail. Impression: Recommend routine imaging follow-up.",
        site="North Clinic",
    )

    client.post(
        "/api/v1/cases/C-SCOPED-EXPORT-1/feedback",
        json={"label": "true_positive", "disposition": "escalate"},
        headers=_scoped_headers("demo-reviewer", "reviewer", "Demo Hospital"),
    )

    demo_summary = client.get("/api/v1/metrics/feedback", headers=_scoped_headers("demo-analyst", "analyst", "Demo Hospital"))
    assert demo_summary.status_code == 200
    demo_payload = demo_summary.json()
    assert demo_payload["labeled_cases"] == 1
    assert demo_payload["unlabeled_cases"] == 0

    north_summary = client.get("/api/v1/metrics/feedback", headers=_scoped_headers("north-analyst", "analyst", "North Clinic"))
    assert north_summary.status_code == 200
    north_payload = north_summary.json()
    assert north_payload["labeled_cases"] == 0
    assert north_payload["unlabeled_cases"] == 1

    demo_export = client.get(
        "/api/v1/exports/review-feedback.jsonl",
        headers=_scoped_headers("demo-analyst", "analyst", "Demo Hospital"),
    )
    assert demo_export.status_code == 200
    assert '"case_id": "C-SCOPED-EXPORT-1"' in demo_export.text

    north_export = client.get(
        "/api/v1/exports/review-feedback.jsonl",
        headers=_scoped_headers("north-analyst", "analyst", "North Clinic"),
    )
    assert north_export.status_code == 200
    assert north_export.text.strip() == ""
