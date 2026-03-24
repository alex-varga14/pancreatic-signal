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
SCRIPT_PATH = ROOT / "scripts" / "run_external_eval.py"


def test_external_evaluation_template_metrics_are_comparable() -> None:
    summary = evaluate_external_dataset(
        labels_path=LABEL_TEMPLATE_PATH,
        predictions_path=PREDICTION_TEMPLATE_PATH,
        threshold=0.2,
        top_k=2,
    )
    sweep = sweep_external_thresholds(
        labels_path=LABEL_TEMPLATE_PATH,
        predictions_path=PREDICTION_TEMPLATE_PATH,
        top_k=2,
        thresholds=[0.2, 0.4, 0.6],
    )

    assert summary.score_mode == "external"
    assert summary.processed == 2
    assert summary.positives == 1
    assert summary.flagged == 1
    assert summary.true_positives == 1
    assert summary.false_positives == 0
    assert summary.false_negatives == 0
    assert summary.precision == 1.0
    assert summary.recall == 1.0
    assert summary.f1 == 1.0
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
            "2",
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

    assert snapshot["evaluation"]["score_mode"] == "external"
    assert snapshot["submission"]["submission_name"] == submission.submission_name
    assert submission.metrics.precision == 1.0
    assert "External Benchmark Snapshot" in markdown_path.read_text()
