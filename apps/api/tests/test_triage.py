from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.triage import ReportInput
from app.services.triage_engine import triage_report
from app.store.memory_store import CASE_STORE


def test_triage_batch_flags_suspicious_reports() -> None:
    CASE_STORE.reset()
    client = TestClient(app)
    response = client.post(
        "/api/v1/triage/batch",
        json={
            "reports": [
                {
                    "report_id": "R-TEST-1",
                    "case_id": "C-TEST-1",
                    "report_datetime": "2026-03-19T10:00:00Z",
                    "modality": "CT",
                    "report_text": "There is abrupt cutoff of the pancreatic duct with an ill-defined pancreatic head lesion suspicious for pancreatic neoplasm."
                },
                {
                    "report_id": "R-TEST-2",
                    "case_id": "C-TEST-2",
                    "report_datetime": "2026-03-19T10:00:00Z",
                    "modality": "CT",
                    "report_text": "Pancreas is unremarkable with no pancreatic mass."
                }
            ]
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["processed"] == 2
    assert payload["flagged"] >= 1


def test_triage_report_extracts_section_aware_evidence() -> None:
    CASE_STORE.reset()
    result = triage_report(
        ReportInput(
            report_id="R-SECTION-1",
            case_id="C-SECTION-1",
            report_datetime=datetime(2026, 3, 19, 10, 0, tzinfo=timezone.utc),
            modality="CT",
            report_text=(
                "Findings: There is abrupt cutoff of the pancreatic duct with an "
                "ill-defined pancreatic head lesion. Impression: Findings are "
                "suspicious for pancreatic neoplasm. Recommend endoscopic ultrasound."
            ),
        )
    )

    assert result.score == 1.0
    assert result.urgency == "critical"
    assert "DUCT_CUTOFF" in result.rationale_codes
    assert "PANCREATIC_MASS" in result.rationale_codes
    assert "PDAC_EXPLICIT_SUSPICION" in result.rationale_codes
    assert "FOLLOWUP_RECOMMENDED" in result.rationale_codes
    assert {item.section for item in result.evidence} == {"findings", "impression"}
    assert all(item.sentence_index is not None for item in result.evidence)
    assert any(item.text == "abrupt cutoff of the pancreatic duct" for item in result.evidence)
    assert any(item.text == "suspicious for pancreatic neoplasm" for item in result.evidence)
    assert result.hybrid_analysis is not None
    assert result.hybrid_analysis.calibrated_score >= result.score
    assert result.hybrid_analysis.review_priority == "expedite"
    assert len(result.hybrid_analysis.sentence_candidates) >= 1


def test_triage_report_suppresses_negated_benign_mentions() -> None:
    CASE_STORE.reset()
    result = triage_report(
        ReportInput(
            report_id="R-NEG-1",
            case_id="C-NEG-1",
            report_datetime=datetime(2026, 3, 19, 10, 0, tzinfo=timezone.utc),
            modality="CT",
            report_text=(
                "Findings: Pancreas is unremarkable. No discrete pancreatic mass is "
                "identified. No pancreatic duct dilation. Impression: No acute abnormality."
            ),
        )
    )

    assert result.score == 0.0
    assert result.urgency == "low"
    assert result.rationale_codes == []
    assert result.evidence == []
    assert result.hybrid_analysis is not None
    assert result.hybrid_analysis.calibrated_score < 0.25
    assert result.hybrid_analysis.review_priority == "defer"


def test_triage_report_surfaces_actionable_followup_without_rule_match() -> None:
    CASE_STORE.reset()
    result = triage_report(
        ReportInput(
            report_id="R-HYBRID-1",
            case_id="C-HYBRID-1",
            report_datetime=datetime(2026, 3, 19, 10, 0, tzinfo=timezone.utc),
            modality="CT",
            report_text=(
                "Findings: Cystic lesion in the pancreatic tail measuring 1.2 cm without "
                "suspicious enhancement. Impression: Likely side-branch IPMN; recommend routine "
                "imaging follow-up."
            ),
        )
    )

    assert result.score == 0.0
    assert result.hybrid_analysis is not None
    assert result.hybrid_analysis.calibrated_score >= 0.3
    assert result.hybrid_analysis.review_priority == "review"
    assert any(
        candidate.classification == "actionable_followup"
        for candidate in result.hybrid_analysis.sentence_candidates
    )
