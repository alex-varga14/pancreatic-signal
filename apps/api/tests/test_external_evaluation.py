import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.schemas.benchmark_submission import BenchmarkSubmission
from app.services.evaluation import evaluate_external_dataset, sweep_external_thresholds

ROOT = Path(__file__).resolve().parents[3]
LABEL_TEMPLATE_PATH = ROOT / "docs" / "examples" / "benchmark-label-template.jsonl"
PREDICTION_TEMPLATE_PATH = ROOT / "docs" / "examples" / "benchmark-prediction-template.jsonl"
RETRO_LABELS_PATH = ROOT / "docs" / "examples" / "retrospective-benchmark-sample-labels.jsonl"
RETRO_PREDICTIONS_PATH = ROOT / "docs" / "examples" / "retrospective-benchmark-sample-predictions.jsonl"
SCRIPT_PATH = ROOT / "scripts" / "run_external_eval.py"


def test_external_evaluation_template_metrics_are_comparable() -> None:
    summary = evaluate_external_dataset(
        labels_path=LABEL_TEMPLATE_PATH,
        predictions_path=PREDICTION_TEMPLATE_PATH,
        threshold=0.2,
        top_k=3,
    )
    sweep = sweep_external_thresholds(
        labels_path=LABEL_TEMPLATE_PATH,
        predictions_path=PREDICTION_TEMPLATE_PATH,
        top_k=3,
        thresholds=[0.2, 0.4, 0.6],
    )

    assert summary.score_mode == "external"
    assert summary.processed == 5
    assert summary.positives == 3
    assert summary.flagged == 2
    assert summary.true_positives == 2
    assert summary.false_positives == 0
    assert summary.false_negatives == 1
    assert summary.precision == 1.0
    assert summary.recall == 0.6667
    assert summary.f1 == 0.8
    case_by_id = {case.case_id: case for case in summary.cases}
    assert case_by_id["C-TEMPLATE-002"].benchmark_bucket == "secondary signs"
    assert case_by_id["C-TEMPLATE-002"].cohort == "template workup"
    assert case_by_id["C-TEMPLATE-003"].reviewer_focus.startswith("Keep pancreatic follow-up")
    assert case_by_id["C-TEMPLATE-003"].false_negative_bucket == "recommendation_language_missed"
    assert case_by_id["C-TEMPLATE-003"].expected_rationale_codes == ["FOLLOWUP_RECOMMENDED"]
    assert sweep.recommendation.recommended_threshold == 0.2
    assert len(sweep.points) == 3


def test_external_evaluation_requires_prediction_alignment(tmp_path: Path) -> None:
    incomplete_predictions = tmp_path / "predictions.jsonl"
    incomplete_predictions.write_text(
        '{"report_id":"R-TEMPLATE-001","case_id":"C-TEMPLATE-001","score":0.91}\n'
    )

    with pytest.raises(ValueError, match="Prediction set must match labels exactly"):
        evaluate_external_dataset(
            labels_path=LABEL_TEMPLATE_PATH,
            predictions_path=incomplete_predictions,
            threshold=0.2,
            top_k=2,
        )


def test_retrospective_external_sample_carries_casebook_context() -> None:
    summary = evaluate_external_dataset(
        labels_path=RETRO_LABELS_PATH,
        predictions_path=RETRO_PREDICTIONS_PATH,
        threshold=0.3,
        top_k=5,
    )

    assert summary.processed == 12
    assert summary.positives == 8
    assert summary.flagged == 8
    assert summary.true_positives == 7
    assert summary.false_positives == 1
    assert summary.false_negatives == 1
    assert summary.precision == 0.875
    assert summary.recall == 0.875
    assert summary.f1 == 0.875

    case_by_id = {case.case_id: case for case in summary.cases}
    assert case_by_id["C-RETRO-003"].report_excerpt.startswith("Pancreas protocol MRI")
    assert case_by_id["C-RETRO-006"].benchmark_bucket == "explicit malignancy"
    assert case_by_id["C-RETRO-009"].cohort == "tertiary MRI workup"
    assert case_by_id["C-RETRO-012"].cohort == "referral pancreas review"
    assert case_by_id["C-RETRO-007"].false_negative_bucket == "recommendation_language_missed"


def test_run_external_eval_writes_valid_bundle(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--labels",
            str(LABEL_TEMPLATE_PATH),
            "--predictions",
            str(PREDICTION_TEMPLATE_PATH),
            "--threshold",
            "0.2",
            "--top-k",
            "3",
            "--out-dir",
            str(tmp_path),
            "--basename",
            "template-external",
            "--dataset-name",
            "template-dataset",
            "--project-name",
            "Example Project",
            "--strength",
            "Strong positive ranking in the small template set.",
            "--limitation",
            "Template-sized dataset is illustrative only.",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )

    json_path = tmp_path / "template-external.json"
    markdown_path = tmp_path / "template-external.md"
    submission_path = tmp_path / "template-external-submission.json"

    assert "Wrote" in result.stdout
    assert json_path.exists()
    assert markdown_path.exists()
    assert submission_path.exists()

    snapshot = json.loads(json_path.read_text())
    submission = BenchmarkSubmission.model_validate(json.loads(submission_path.read_text()))
    casebook_by_id = {entry["case_id"]: entry for entry in snapshot["casebook"]}

    assert snapshot["evaluation"]["score_mode"] == "external"
    assert snapshot["dataset_summary"]["report_count"] == 5
    assert snapshot["dataset_summary"]["positive_count"] == 3
    assert snapshot["queue_preview"]["top_k"] == 3
    assert any(bucket["bucket"] == "follow-up only" for bucket in snapshot["dataset_summary"]["bucket_counts"])
    assert casebook_by_id["C-TEMPLATE-003"]["benchmark_bucket"] == "follow-up only"
    assert casebook_by_id["C-TEMPLATE-003"]["external"]["outcome"] == "missed_positive"
    assert casebook_by_id["C-TEMPLATE-003"]["external"]["false_negative_bucket"] == "recommendation_language_missed"
    assert snapshot["submission"]["submission_name"] == submission.submission_name
    assert submission.metrics.precision == 1.0
    markdown = markdown_path.read_text()
    assert "External Benchmark Snapshot" in markdown
    assert "## Dataset Coverage" in markdown
    assert "## Top-k Queue Preview" in markdown
    assert "## Reviewer Casebook" in markdown
    assert "### C-TEMPLATE-003 — follow-up only" in markdown


def test_run_external_eval_sample_bundle_includes_report_excerpts(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--labels",
            str(RETRO_LABELS_PATH),
            "--predictions",
            str(RETRO_PREDICTIONS_PATH),
            "--threshold",
            "0.3",
            "--top-k",
            "5",
            "--out-dir",
            str(tmp_path),
            "--basename",
            "retrospective-sample",
            "--dataset-name",
            "deidentified-retrospective-multicohort-sample",
            "--dataset-split",
            "validation",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )

    json_path = tmp_path / "retrospective-sample.json"
    markdown_path = tmp_path / "retrospective-sample.md"

    assert "Wrote" in result.stdout
    snapshot = json.loads(json_path.read_text())
    casebook_by_id = {entry["case_id"]: entry for entry in snapshot["casebook"]}
    cohort_by_name = {entry["cohort"]: entry for entry in snapshot["dataset_summary"]["cohort_counts"]}

    assert snapshot["dataset_summary"]["report_count"] == 12
    assert snapshot["queue_preview"]["top_k"] == 5
    assert len(snapshot["dataset_summary"]["cohort_counts"]) == 3
    assert cohort_by_name["tertiary MRI workup"]["missed_positive_count"] == 1
    assert casebook_by_id["C-RETRO-001"]["report_excerpt"].startswith("CT abdomen with contrast")
    assert casebook_by_id["C-RETRO-001"]["cohort"] == "community CT intake"
    assert casebook_by_id["C-RETRO-007"]["external"]["outcome"] == "missed_positive"
    assert casebook_by_id["C-RETRO-010"]["external"]["outcome"] == "false_positive"

    markdown = markdown_path.read_text()
    assert "## Cohort Coverage" in markdown
    assert "### C-RETRO-007 — follow-up only" in markdown
    assert "- Cohort: tertiary MRI workup" in markdown
    assert "- Report excerpt: MRI abdomen:" in markdown
