from typing import Literal

from pydantic import BaseModel, Field

DemoScoreMode = Literal["rules", "hybrid"]
ScoreMode = Literal["rules", "hybrid", "external"]


class EvaluationLabel(BaseModel):
    report_id: str
    case_id: str
    suspicious_pancreatic_malignancy: bool
    high_risk_pancreatic_abnormality: bool
    action_worthy_followup: bool
    should_escalate: bool
    notes: str | None = None
    report_excerpt: str | None = None
    cohort: str | None = None
    benchmark_bucket: str | None = None
    reviewer_focus: str | None = None
    expected_rationale_codes: list[str] = Field(default_factory=list)

    @property
    def should_flag(self) -> bool:
        return any(
            [
                self.suspicious_pancreatic_malignancy,
                self.high_risk_pancreatic_abnormality,
                self.action_worthy_followup,
                self.should_escalate,
            ]
        )


class EvaluationCaseResult(BaseModel):
    report_id: str
    case_id: str
    score: float = Field(ge=0.0, le=1.0)
    base_score: float = Field(ge=0.0, le=1.0)
    hybrid_score: float = Field(ge=0.0, le=1.0)
    urgency: str
    flagged: bool
    expected_positive: bool
    expected_escalation: bool
    rationale_codes: list[str]
    label_notes: str | None = None
    report_excerpt: str | None = None
    cohort: str | None = None
    benchmark_bucket: str | None = None
    reviewer_focus: str | None = None
    expected_rationale_codes: list[str] = Field(default_factory=list)
    false_negative_bucket: str | None = Field(default=None, exclude=True)


class EvaluationSummary(BaseModel):
    score_mode: ScoreMode = "rules"
    threshold: float = Field(ge=0.0, le=1.0)
    top_k: int = Field(ge=1)
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
    false_negative_buckets: dict[str, int]
    cases: list[EvaluationCaseResult]


class EvaluationComparison(BaseModel):
    threshold: float = Field(ge=0.0, le=1.0)
    top_k: int = Field(ge=1)
    rules: EvaluationSummary
    hybrid: EvaluationSummary
    flagged_delta: int
    precision_delta: float
    recall_delta: float
    f1_delta: float
    precision_at_top_k_delta: float
    sensitivity_at_top_k_delta: float
    newly_flagged_cases: list[str]
    resolved_false_negatives: list[str]


class ThresholdSweepPoint(BaseModel):
    threshold: float = Field(ge=0.0, le=1.0)
    rules_f1: float = Field(ge=0.0, le=1.0)
    hybrid_f1: float = Field(ge=0.0, le=1.0)
    rules_recall: float = Field(ge=0.0, le=1.0)
    hybrid_recall: float = Field(ge=0.0, le=1.0)
    rules_flagged: int = Field(ge=0)
    hybrid_flagged: int = Field(ge=0)
    f1_delta: float
    recall_delta: float
    flagged_delta: int


class ThresholdRecommendation(BaseModel):
    score_mode: ScoreMode
    recommended_threshold: float = Field(ge=0.0, le=1.0)
    rationale: str
    f1: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    flagged: int = Field(ge=0)


class ThresholdSweepSummary(BaseModel):
    top_k: int = Field(ge=1)
    thresholds: list[float]
    points: list[ThresholdSweepPoint]
    rules_recommendation: ThresholdRecommendation
    hybrid_recommendation: ThresholdRecommendation


class ExternalEvaluationPrediction(BaseModel):
    report_id: str
    case_id: str
    score: float = Field(ge=0.0, le=1.0)
    rationale_codes: list[str] = Field(default_factory=list)
    false_negative_bucket: str | None = None
    notes: str | None = None


class ExternalThresholdSweepPoint(BaseModel):
    threshold: float = Field(ge=0.0, le=1.0)
    f1: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    flagged: int = Field(ge=0)
    precision: float = Field(ge=0.0, le=1.0)
    precision_at_top_k: float = Field(ge=0.0, le=1.0)
    sensitivity_at_top_k: float = Field(ge=0.0, le=1.0)


class ExternalThresholdRecommendation(BaseModel):
    score_mode: Literal["external"] = "external"
    recommended_threshold: float = Field(ge=0.0, le=1.0)
    rationale: str
    f1: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    flagged: int = Field(ge=0)


class ExternalThresholdSweepSummary(BaseModel):
    score_mode: Literal["external"] = "external"
    top_k: int = Field(ge=1)
    thresholds: list[float]
    points: list[ExternalThresholdSweepPoint]
    recommendation: ExternalThresholdRecommendation
