from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OntologyFamily(BaseModel):
    """A rationale family with patterns and a positive weight contribution."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    label: str = Field(min_length=1)
    weight: float = Field(ge=0.0, le=1.0)
    patterns: list[str] = Field(min_length=1)

    @field_validator("patterns")
    @classmethod
    def _patterns_non_empty(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("patterns must contain at least one non-empty string")
        return cleaned


class OntologyThresholds(BaseModel):
    """Score thresholds that bucket triage urgency."""

    model_config = ConfigDict(extra="forbid")

    medium: float = Field(ge=0.0, le=1.0)
    high: float = Field(ge=0.0, le=1.0)
    critical: float = Field(ge=0.0, le=1.0)


class OntologyScoringProfile(BaseModel):
    """Configurable scoring block consumed by the triage engine.

    The default profile is additive (sum of matched family weights) clamped to
    ``max_score``. Autoresearch loops can swap this block to retune calibration
    without code changes; downstream consumers should treat unknown methods as
    a validation error rather than silently falling back.
    """

    model_config = ConfigDict(extra="forbid")

    method: Literal["additive", "max", "weighted_sum"] = "additive"
    max_score: float = Field(default=1.0, gt=0.0, le=1.0)
    round_digits: int = Field(default=4, ge=0, le=8)
    global_weight: float = Field(default=1.0, ge=0.0, le=10.0)


class OntologyConfig(BaseModel):
    """Top-level rule ontology, the only artifact the autoresearcher mutates."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    families: list[OntologyFamily] = Field(min_length=1)
    negations: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)
    thresholds: OntologyThresholds
    scoring: OntologyScoringProfile = Field(default_factory=OntologyScoringProfile)

    @field_validator("families")
    @classmethod
    def _unique_codes(cls, value: list[OntologyFamily]) -> list[OntologyFamily]:
        codes = [family.code for family in value]
        if len(codes) != len(set(codes)):
            raise ValueError("ontology family codes must be unique")
        return value
