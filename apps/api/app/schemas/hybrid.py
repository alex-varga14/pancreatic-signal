from pydantic import BaseModel, Field


class SentenceSignal(BaseModel):
    code: str
    label: str
    weight: float
    rationale: str


class SentenceCandidate(BaseModel):
    text: str
    section: str
    sentence_index: int
    score: float = Field(ge=0.0, le=1.0)
    classification: str
    matched_codes: list[str]
    signals: list[SentenceSignal]


class HybridAnalysis(BaseModel):
    calibrated_score: float = Field(ge=0.0, le=1.0)
    confidence_label: str
    review_priority: str
    active_learning_priority: str
    summary: str
    factors: list[str]
    sentence_candidates: list[SentenceCandidate]
