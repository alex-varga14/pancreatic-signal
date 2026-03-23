import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.benchmark_submission import BenchmarkSubmission
from app.schemas.evaluation import EvaluationLabel

ROOT = Path(__file__).resolve().parents[3]
SUBMISSION_TEMPLATE_PATH = ROOT / "docs" / "examples" / "benchmark-submission-template.json"
LABEL_TEMPLATE_PATH = ROOT / "docs" / "examples" / "benchmark-label-template.jsonl"


def test_benchmark_submission_template_is_valid() -> None:
    payload = json.loads(SUBMISSION_TEMPLATE_PATH.read_text())

    submission = BenchmarkSubmission.model_validate(payload)

    assert submission.submission_name == "external-pancreatic-benchmark-baseline"
    assert submission.metrics.processed == submission.report_count
    assert submission.metrics.flagged == (
        submission.metrics.true_positives + submission.metrics.false_positives
    )


def test_benchmark_submission_rejects_inconsistent_counts() -> None:
    payload = json.loads(SUBMISSION_TEMPLATE_PATH.read_text())
    payload["metrics"]["flagged"] = payload["metrics"]["flagged"] + 1

    with pytest.raises(ValidationError):
        BenchmarkSubmission.model_validate(payload)


def test_benchmark_label_template_lines_match_evaluation_schema() -> None:
    labels = [
        EvaluationLabel.model_validate_json(line)
        for line in LABEL_TEMPLATE_PATH.read_text().splitlines()
        if line.strip()
    ]

    assert len(labels) == 2
    assert labels[0].should_flag is True
    assert labels[1].should_flag is False
