from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AutoresearchRunSummary(BaseModel):
    """Compact summary suitable for the run list and leaderboard views."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    created_at: str | None = None
    status: str
    primary_metric: str = "f1_at_top_k_demo_rules"
    primary_value: float | None = None
    baseline_value: float | None = None
    delta: float | None = None
    notes_summary: str | None = None
    has_proposal: bool = False
    promoted_at: str | None = None


class AutoresearchRunDetail(BaseModel):
    """Full detail surface for a single run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    created_at: str | None = None
    status: str
    decision: dict[str, Any]
    eval: dict[str, Any] | None = None
    diff: dict[str, Any] | None = None
    proposal: dict[str, Any] | None = None
    proposal_meta: dict[str, Any] | None = None
    notes_markdown: str | None = None
    promotion: dict[str, Any] | None = None


class AutoresearchLeaderboard(BaseModel):
    """Top-N kept runs ranked by the primary metric."""

    model_config = ConfigDict(extra="forbid")

    primary_metric: str = "f1_at_top_k_demo_rules"
    runs: list[AutoresearchRunSummary] = Field(default_factory=list)


class AutoresearchPromotionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    promoted_at: str
    ontology_target: str
    pre_promotion_snapshot: str
    decision: dict[str, Any]
