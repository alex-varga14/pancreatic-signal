from datetime import datetime
from typing import Literal

from pydantic import BaseModel

FeedbackLabel = Literal[
    "true_positive",
    "false_positive",
    "actionable_followup",
    "benign",
    "uncertain",
]

FeedbackDisposition = Literal[
    "escalate",
    "dismiss",
    "routine_followup",
    "monitor",
    "needs_more_review",
]

FeedbackErrorBucket = Literal[
    "wording_variance",
    "negation_failure",
    "incidental_cyst",
    "pancreatitis_confounder",
    "secondary_signs_only",
    "other",
]

RecommendationConfidence = Literal["anchored", "high", "moderate", "low"]


class ReviewerFeedbackInput(BaseModel):
    reviewer: str | None = None
    label: FeedbackLabel
    disposition: FeedbackDisposition
    error_bucket: FeedbackErrorBucket | None = None
    notes: str | None = None


class ReviewerFeedbackRecord(BaseModel):
    reviewer: str
    label: FeedbackLabel
    disposition: FeedbackDisposition
    error_bucket: FeedbackErrorBucket | None = None
    notes: str | None = None
    created_at: datetime


class ReviewerFeedbackResult(BaseModel):
    ok: bool
    case_id: str
    reviewer: str
    label: FeedbackLabel
    disposition: FeedbackDisposition


class FeedbackSummary(BaseModel):
    total_feedback: int
    labeled_cases: int
    unlabeled_cases: int
    unlabeled_active_learning_cases: int
    label_distribution: dict[str, int]
    disposition_distribution: dict[str, int]
    error_bucket_distribution: dict[str, int]


class FeedbackRecommendation(BaseModel):
    case_id: str
    recommended_label: FeedbackLabel
    recommended_disposition: FeedbackDisposition
    recommended_error_bucket: FeedbackErrorBucket | None = None
    confidence: RecommendationConfidence
    rationale: str
    reasons: list[str]
    suggested_notes: str | None = None
    already_labeled: bool = False
    latest_feedback_label: FeedbackLabel | None = None
    latest_feedback_disposition: FeedbackDisposition | None = None
