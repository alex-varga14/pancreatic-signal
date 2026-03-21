from pydantic import BaseModel, Field


class TrialAbstraction(BaseModel):
    modality: str
    suspected_pdac: bool
    pancreatic_mass: bool
    duct_cutoff: bool
    duct_dilation: bool
    double_duct_sign: bool
    focal_atrophy: bool
    followup_recommended: bool
    eus_recommended: bool
    biopsy_recommended: bool
    needs_tissue_confirmation: bool
    pancreatic_head_focus: bool
    pancreatic_tail_focus: bool
    secondary_signs_present: bool
    high_risk_pancreatic_signal: bool
    metastatic_language_present: bool
    localized_disease_suspected: bool


class TrialCriterionTrace(BaseModel):
    id: str
    label: str
    status: str
    rationale: str
    evidence: list[str] = Field(default_factory=list)


class TrialCandidate(BaseModel):
    trial_id: str
    title: str
    source: str
    summary: str
    match_score: float = Field(ge=0.0, le=1.0)
    match_status: str
    rationale: str
    criteria: list[TrialCriterionTrace]


class TrialMatchResponse(BaseModel):
    case_id: str
    abstraction: TrialAbstraction
    matches: list[TrialCandidate]
