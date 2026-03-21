from __future__ import annotations

import re

from app.schemas.case import CaseDetail
from app.schemas.feedback import FeedbackRecommendation
from app.schemas.hybrid import HybridAnalysis

_NEGATION_CONTEXT_RE = re.compile(
    r"\b(no|without|not)\b.{0,30}\b(pancreatic mass|pancreatic duct|mass|lesion|dilat\w+)\b",
    flags=re.IGNORECASE,
)


def recommend_case_feedback(case: CaseDetail, hybrid: HybridAnalysis) -> FeedbackRecommendation:
    latest_feedback = case.review_feedback[-1] if case.review_feedback else None
    if latest_feedback is not None:
        return FeedbackRecommendation(
            case_id=case.case_id,
            recommended_label=latest_feedback.label,
            recommended_disposition=latest_feedback.disposition,
            recommended_error_bucket=latest_feedback.error_bucket,
            confidence="anchored",
            rationale="This case already has reviewer feedback, so the latest label is used as the default anchor.",
            reasons=[
                f"Latest reviewer label is {latest_feedback.label}.",
                f"Latest reviewer disposition is {latest_feedback.disposition}.",
            ],
            suggested_notes=latest_feedback.notes,
            already_labeled=True,
            latest_feedback_label=latest_feedback.label,
            latest_feedback_disposition=latest_feedback.disposition,
        )

    text_l = case.report_text.lower()
    codes = set(case.rationale_codes)
    top_classes = {candidate.classification for candidate in hybrid.sentence_candidates}
    has_followup = "FOLLOWUP_RECOMMENDED" in codes or "actionable_followup" in top_classes
    has_explicit_suspicion = (
        "PDAC_EXPLICIT_SUSPICION" in codes
        or "explicit_suspicion" in top_classes
        or hybrid.review_priority == "expedite"
    )
    has_secondary_signs = bool(
        codes & {"DUCT_CUTOFF", "DOUBLE_DUCT_SIGN", "DUCT_DILATION", "FOCAL_ATROPHY"}
    )
    cystic_context = any(term in text_l for term in ("ipmn", "cystic lesion", "pancreatic cyst", "side-branch"))
    pancreatitis_context = any(term in text_l for term in ("pancreatitis", "inflammatory change"))
    negated_context = bool(_NEGATION_CONTEXT_RE.search(case.report_text))
    only_secondary_signs = bool(codes) and codes.issubset(
        {"DUCT_CUTOFF", "DOUBLE_DUCT_SIGN", "DUCT_DILATION", "FOCAL_ATROPHY", "FOLLOWUP_RECOMMENDED"}
    )
    hybrid_delta = round(hybrid.calibrated_score - case.score, 4)

    reasons: list[str] = []
    recommended_error_bucket = None
    suggested_notes = None

    if has_explicit_suspicion or case.urgency in {"high", "critical"}:
        reasons.append("Explicit suspicion language or high urgency supports a malignant signal label.")
        if has_secondary_signs:
            reasons.append("Secondary signs reinforce the obstructive pancreatic pattern.")
        if has_followup:
            reasons.append("Further diagnostic workup is already being recommended in the report.")
        if only_secondary_signs and "PDAC_EXPLICIT_SUSPICION" not in codes:
            recommended_error_bucket = "secondary_signs_only"
        return FeedbackRecommendation(
            case_id=case.case_id,
            recommended_label="true_positive",
            recommended_disposition="escalate",
            recommended_error_bucket=recommended_error_bucket,
            confidence="high" if "PDAC_EXPLICIT_SUSPICION" in codes or case.urgency == "critical" else "moderate",
            rationale="The current evidence pattern looks consistent with a high-priority pancreatic malignancy signal.",
            reasons=reasons,
            suggested_notes="Escalate for expedited specialist or navigator review.",
        )

    if cystic_context and has_followup and case.score < 0.3:
        reasons.append("Pancreatic cystic language with follow-up recommendation is still action-worthy.")
        if hybrid.active_learning_priority == "high":
            reasons.append("The hybrid layer uplifted this case above the rules-only baseline.")
        return FeedbackRecommendation(
            case_id=case.case_id,
            recommended_label="actionable_followup",
            recommended_disposition="routine_followup",
            recommended_error_bucket="incidental_cyst",
            confidence="moderate",
            rationale="This looks more like an actionable pancreatic follow-up finding than a malignant triage hit.",
            reasons=reasons,
            suggested_notes="Review incidental pancreatic cyst follow-up pathway and interval recommendation.",
        )

    if pancreatitis_context and hybrid.active_learning_priority in {"medium", "high"}:
        reasons.append("Pancreatitis wording can confound pancreatic malignancy rules.")
        if hybrid_delta >= 0.1:
            reasons.append("Hybrid uplift suggests wording variance or overlapping morphology worth manual review.")
        return FeedbackRecommendation(
            case_id=case.case_id,
            recommended_label="uncertain",
            recommended_disposition="needs_more_review",
            recommended_error_bucket="pancreatitis_confounder",
            confidence="moderate",
            rationale="Inflammatory pancreatic context makes this better suited for reviewer adjudication than immediate escalation.",
            reasons=reasons,
            suggested_notes="Pancreatitis confounder; confirm whether any discrete pancreatic lesion is truly present.",
        )

    if case.score == 0.0 and hybrid.calibrated_score >= 0.25:
        reasons.append("Rules-only scoring missed or down-weighted language that the hybrid layer surfaced.")
        if negated_context:
            recommended_error_bucket = "negation_failure"
            reasons.append("Nearby negation wording may be driving disagreement between deterministic and hybrid scoring.")
        elif cystic_context:
            recommended_error_bucket = "incidental_cyst"
            reasons.append("The disagreement is driven by incidental pancreatic cyst follow-up language.")
        elif only_secondary_signs or has_secondary_signs:
            recommended_error_bucket = "secondary_signs_only"
            reasons.append("Secondary signs without explicit mass language are driving the disagreement.")
        else:
            recommended_error_bucket = "wording_variance"
            reasons.append("This pattern looks like wording variance rather than a clean true-negative.")

        return FeedbackRecommendation(
            case_id=case.case_id,
            recommended_label="uncertain" if not cystic_context else "actionable_followup",
            recommended_disposition="needs_more_review" if not cystic_context else "routine_followup",
            recommended_error_bucket=recommended_error_bucket,
            confidence="moderate",
            rationale="This is a disagreement case that should be reviewed and labeled for calibration.",
            reasons=reasons,
            suggested_notes="Hybrid disagreement case; confirm whether this should remain reviewable in future calibration.",
        )

    if case.score == 0.0 and hybrid.calibrated_score < 0.15 and not case.evidence:
        reasons.append("No deterministic evidence spans were captured.")
        reasons.append("Hybrid scoring stayed low and did not surface an actionable sentence cluster.")
        return FeedbackRecommendation(
            case_id=case.case_id,
            recommended_label="benign",
            recommended_disposition="dismiss",
            confidence="moderate",
            rationale="This looks like a low-signal benign case rather than a candidate for escalation or follow-up.",
            reasons=reasons,
            suggested_notes="Low-signal benign report; no additional pancreatic action appears warranted.",
        )

    reasons.append("The case remains reviewer-meaningful but not clearly classifiable from the current signal mix alone.")
    if hybrid.active_learning_priority in {"medium", "high"}:
        reasons.append("It is still useful to label this case for future calibration.")
    return FeedbackRecommendation(
        case_id=case.case_id,
        recommended_label="uncertain",
        recommended_disposition="needs_more_review",
        recommended_error_bucket="wording_variance" if hybrid_delta >= 0.05 else None,
        confidence="low",
        rationale="The available evidence is mixed enough that a cautious reviewer label is the safest default.",
        reasons=reasons,
        suggested_notes=suggested_notes,
    )
