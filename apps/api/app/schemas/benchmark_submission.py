from typing import Literal

from pydantic import BaseModel, Field, model_validator

SubmissionScoreMode = Literal["rules", "hybrid", "external"]


def _safe_divide(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _round_metric(value: float) -> float:
    return round(float(value), 4)


class BenchmarkSubmissionMetrics(BaseModel):
    processed: int = Field(ge=0)
    positives: int = Field(ge=0)
    flagged: int = Field(ge=0)
    true_positives: int = Field(ge=0)
    false_positives: int = Field(ge=0)
    true_negatives: int = Field(ge=0)
    false_negatives: int = Field(ge=0)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1: float = Field(ge=0.0, le=1.0)
    precision_at_top_k: float = Field(ge=0.0, le=1.0)
    sensitivity_at_top_k: float = Field(ge=0.0, le=1.0)
    reviewer_yield_at_top_k: float = Field(ge=0.0, le=1.0)
    false_negative_buckets: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_consistency(self) -> "BenchmarkSubmissionMetrics":
        if self.processed != (
            self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        ):
            raise ValueError("processed must equal TP + FP + TN + FN.")

        if self.positives != self.true_positives + self.false_negatives:
            raise ValueError("positives must equal TP + FN.")

        if self.flagged != self.true_positives + self.false_positives:
            raise ValueError("flagged must equal TP + FP.")

        expected_precision = _round_metric(
            _safe_divide(self.true_positives, self.true_positives + self.false_positives)
        )
        expected_recall = _round_metric(
            _safe_divide(self.true_positives, self.true_positives + self.false_negatives)
        )
        expected_f1 = _round_metric(
            0.0
            if (expected_precision == 0.0 and expected_recall == 0.0)
            else (2 * expected_precision * expected_recall) / (expected_precision + expected_recall)
        )

        if _round_metric(self.precision) != expected_precision:
            raise ValueError(f"precision must match counts ({expected_precision:.4f}).")
        if _round_metric(self.recall) != expected_recall:
            raise ValueError(f"recall must match counts ({expected_recall:.4f}).")
        if _round_metric(self.f1) != expected_f1:
            raise ValueError(f"f1 must match counts ({expected_f1:.4f}).")
        if _round_metric(self.reviewer_yield_at_top_k) != _round_metric(self.precision_at_top_k):
            raise ValueError("reviewer_yield_at_top_k should match precision_at_top_k.")
        if sum(self.false_negative_buckets.values()) > self.false_negatives:
            raise ValueError("false_negative_buckets cannot sum to more than false_negatives.")

        return self


class BenchmarkSubmission(BaseModel):
    submission_version: Literal["1.0"] = "1.0"
    submission_name: str = Field(min_length=3)
    project_name: str = Field(min_length=2)
    repository_url: str | None = None
    commit_sha: str | None = None
    dataset_name: str = Field(min_length=3)
    dataset_split: str = Field(default="test", min_length=2)
    report_count: int = Field(ge=1)
    deidentified: bool = True
    label_schema_version: str = Field(default="pancreatic-signal-eval-v1", min_length=3)
    score_mode: SubmissionScoreMode = "external"
    threshold: float = Field(ge=0.0, le=1.0)
    top_k: int = Field(ge=1)
    evaluation_command: str = Field(min_length=3)
    artifact_paths: list[str] = Field(default_factory=list)
    metrics: BenchmarkSubmissionMetrics
    notable_strengths: list[str] = Field(min_length=1)
    known_limitations: list[str] = Field(min_length=1)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_dataset_consistency(self) -> "BenchmarkSubmission":
        if self.metrics.processed != self.report_count:
            raise ValueError("report_count must equal metrics.processed.")
        return self
