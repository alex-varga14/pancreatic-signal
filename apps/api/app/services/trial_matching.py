from __future__ import annotations

import json
import re
from functools import lru_cache

from sqlalchemy import select

from app.core.paths import resolve_data_path
from app.db.session import SessionLocal
from app.models import ReportRecord
from app.schemas.case import CaseDetail
from app.schemas.trial import TrialAbstraction, TrialCandidate, TrialCriterionTrace, TrialMatchResponse
from app.store.memory_store import CASE_STORE

TRIAL_RULES_PATH = resolve_data_path("trials", "pdac_trial_rules.json")

_METASTATIC_RE = re.compile(
    r"\b(metastatic|metastasis|metastases|liver metast|hepatic metast|peritoneal carcinomatosis)\b",
    flags=re.IGNORECASE,
)


@lru_cache(maxsize=1)
def load_trial_catalog() -> dict:
    with TRIAL_RULES_PATH.open() as handle:
        return json.load(handle)


def match_case_to_trials(case_id: str) -> TrialMatchResponse | None:
    case = CASE_STORE.get_case(case_id)
    if case is None:
        return None

    modality = _load_case_modality(case.report_id)
    abstraction, evidence_map = _build_abstraction(case, modality=modality)

    matches: list[TrialCandidate] = []
    for rule in load_trial_catalog().get("trials", []):
        candidate = _evaluate_trial_rule(rule, abstraction, evidence_map)
        if candidate is not None:
            matches.append(candidate)

    matches.sort(key=lambda item: (-item.match_score, item.trial_id))
    return TrialMatchResponse(case_id=case_id, abstraction=abstraction, matches=matches)


def _load_case_modality(report_id: str) -> str:
    with SessionLocal() as session:
        report = session.execute(
            select(ReportRecord).where(ReportRecord.report_id == report_id)
        ).scalar_one_or_none()
        return report.modality if report is not None else "unknown"


def _build_abstraction(case: CaseDetail, *, modality: str) -> tuple[TrialAbstraction, dict[str, list[str]]]:
    report_text_l = case.report_text.lower()
    rationale_codes = set(case.rationale_codes)
    evidence_by_code: dict[str, list[str]] = {}
    for item in case.evidence:
        evidence_by_code.setdefault(item["code"], []).append(item["text"])

    evidence_map: dict[str, list[str]] = {}

    suspected_pdac = (
        "PDAC_EXPLICIT_SUSPICION" in rationale_codes
        or "pancreatic neoplasm" in report_text_l
        or "pancreatic malignancy" in report_text_l
        or "pancreatic carcinoma" in report_text_l
        or "pancreatic adenocarcinoma" in report_text_l
    )
    if suspected_pdac:
        evidence_map["suspected_pdac"] = _pick_evidence(
            evidence_by_code,
            ["PDAC_EXPLICIT_SUSPICION"],
            fallback_phrases=["pancreatic neoplasm", "pancreatic malignancy", "pancreatic carcinoma"],
            report_text=case.report_text,
        )

    pancreatic_mass = "PANCREATIC_MASS" in rationale_codes or "pancreatic mass" in report_text_l
    if pancreatic_mass:
        evidence_map["pancreatic_mass"] = _pick_evidence(
            evidence_by_code,
            ["PANCREATIC_MASS"],
            fallback_phrases=["pancreatic mass", "pancreatic lesion"],
            report_text=case.report_text,
        )

    duct_cutoff = "DUCT_CUTOFF" in rationale_codes
    if duct_cutoff:
        evidence_map["duct_cutoff"] = _pick_evidence(
            evidence_by_code,
            ["DUCT_CUTOFF"],
            fallback_phrases=["abrupt cutoff of the pancreatic duct", "abrupt duct cutoff"],
            report_text=case.report_text,
        )

    duct_dilation = "DUCT_DILATION" in rationale_codes
    if duct_dilation:
        evidence_map["duct_dilation"] = _pick_evidence(
            evidence_by_code,
            ["DUCT_DILATION"],
            fallback_phrases=["pancreatic duct dilation", "dilated pancreatic duct"],
            report_text=case.report_text,
        )

    double_duct_sign = "DOUBLE_DUCT_SIGN" in rationale_codes or "double duct sign" in report_text_l
    if double_duct_sign:
        evidence_map["double_duct_sign"] = _pick_evidence(
            evidence_by_code,
            ["DOUBLE_DUCT_SIGN"],
            fallback_phrases=["double duct sign"],
            report_text=case.report_text,
        )

    focal_atrophy = "FOCAL_ATROPHY" in rationale_codes
    if focal_atrophy:
        evidence_map["focal_atrophy"] = _pick_evidence(
            evidence_by_code,
            ["FOCAL_ATROPHY"],
            fallback_phrases=["focal pancreatic atrophy", "distal pancreatic atrophy"],
            report_text=case.report_text,
        )

    followup_recommended = "FOLLOWUP_RECOMMENDED" in rationale_codes
    if followup_recommended:
        evidence_map["followup_recommended"] = _pick_evidence(
            evidence_by_code,
            ["FOLLOWUP_RECOMMENDED"],
            fallback_phrases=["recommend", "consider eus", "biopsy"],
            report_text=case.report_text,
        )

    eus_recommended = any(
        phrase in report_text_l
        for phrase in ["endoscopic ultrasound", "consider eus", "recommend eus"]
    )
    if eus_recommended:
        evidence_map["eus_recommended"] = _find_phrases(
            case.report_text,
            ["endoscopic ultrasound", "consider EUS", "recommend EUS"],
        )

    biopsy_recommended = "biopsy" in report_text_l or "tissue sampling" in report_text_l
    if biopsy_recommended:
        evidence_map["biopsy_recommended"] = _find_phrases(case.report_text, ["biopsy", "tissue sampling"])

    pancreatic_head_focus = "pancreatic head" in report_text_l
    if pancreatic_head_focus:
        evidence_map["pancreatic_head_focus"] = _find_phrases(case.report_text, ["pancreatic head"])

    pancreatic_tail_focus = "pancreatic tail" in report_text_l
    if pancreatic_tail_focus:
        evidence_map["pancreatic_tail_focus"] = _find_phrases(case.report_text, ["pancreatic tail"])

    metastatic_language_present = bool(_METASTATIC_RE.search(case.report_text))
    if metastatic_language_present:
        evidence_map["metastatic_language_present"] = _find_regex_matches(case.report_text, _METASTATIC_RE)

    secondary_signs_present = any([duct_cutoff, duct_dilation, double_duct_sign, focal_atrophy])
    if secondary_signs_present:
        evidence_map["secondary_signs_present"] = _combine_evidence(
            evidence_map,
            ["duct_cutoff", "duct_dilation", "double_duct_sign", "focal_atrophy"],
        )

    high_risk_pancreatic_signal = any([suspected_pdac, pancreatic_mass, secondary_signs_present])
    if high_risk_pancreatic_signal:
        evidence_map["high_risk_pancreatic_signal"] = _combine_evidence(
            evidence_map,
            ["suspected_pdac", "pancreatic_mass", "secondary_signs_present"],
        )

    needs_tissue_confirmation = any([eus_recommended, biopsy_recommended, followup_recommended])
    if needs_tissue_confirmation:
        evidence_map["needs_tissue_confirmation"] = _combine_evidence(
            evidence_map,
            ["eus_recommended", "biopsy_recommended", "followup_recommended"],
        )

    localized_disease_suspected = high_risk_pancreatic_signal and not metastatic_language_present
    if localized_disease_suspected:
        evidence_map["localized_disease_suspected"] = _combine_evidence(
            evidence_map,
            ["high_risk_pancreatic_signal"],
        ) or ["No metastatic disease language detected in the report text."]

    abstraction = TrialAbstraction(
        modality=modality,
        suspected_pdac=suspected_pdac,
        pancreatic_mass=pancreatic_mass,
        duct_cutoff=duct_cutoff,
        duct_dilation=duct_dilation,
        double_duct_sign=double_duct_sign,
        focal_atrophy=focal_atrophy,
        followup_recommended=followup_recommended,
        eus_recommended=eus_recommended,
        biopsy_recommended=biopsy_recommended,
        needs_tissue_confirmation=needs_tissue_confirmation,
        pancreatic_head_focus=pancreatic_head_focus,
        pancreatic_tail_focus=pancreatic_tail_focus,
        secondary_signs_present=secondary_signs_present,
        high_risk_pancreatic_signal=high_risk_pancreatic_signal,
        metastatic_language_present=metastatic_language_present,
        localized_disease_suspected=localized_disease_suspected,
    )
    return abstraction, evidence_map


def _evaluate_trial_rule(
    rule: dict,
    abstraction: TrialAbstraction,
    evidence_map: dict[str, list[str]],
) -> TrialCandidate | None:
    traces: list[TrialCriterionTrace] = []
    required_met = True
    any_group_met = True
    blocked = False
    satisfied_positive = 0
    positive_total = 0

    for criterion in rule.get("inclusion_all", []):
        trace = _evaluate_positive_criterion(criterion, abstraction, evidence_map, require_all=True)
        traces.append(trace)
        positive_total += 1
        if trace.status == "met":
            satisfied_positive += 1
        else:
            required_met = False

    for criterion in rule.get("inclusion_any", []):
        trace = _evaluate_positive_criterion(criterion, abstraction, evidence_map, require_all=False)
        traces.append(trace)
        positive_total += 1
        if trace.status == "met":
            satisfied_positive += 1
        else:
            any_group_met = False

    for criterion in rule.get("preferred", []):
        trace = _evaluate_positive_criterion(criterion, abstraction, evidence_map, require_all=False)
        traces.append(trace)
        positive_total += 1
        if trace.status == "met":
            satisfied_positive += 1

    for criterion in rule.get("exclude_any", []):
        trace = _evaluate_exclusion_criterion(criterion, abstraction, evidence_map)
        traces.append(trace)
        if trace.status == "blocked":
            blocked = True

    if blocked or not required_met or not any_group_met:
        return None

    match_score = round(satisfied_positive / positive_total, 4) if positive_total else 0.0
    match_status = "strong" if match_score >= 0.8 else "potential"
    met_labels = [trace.label for trace in traces if trace.status == "met"]
    rationale = (
        f"Matched on {', '.join(met_labels[:3])}."
        if met_labels
        else "Met the baseline rule set for this trial."
    )

    return TrialCandidate(
        trial_id=rule["trial_id"],
        title=rule["title"],
        source=rule["source"],
        summary=rule["summary"],
        match_score=match_score,
        match_status=match_status,
        rationale=rationale,
        criteria=traces,
    )


def _evaluate_positive_criterion(
    criterion: dict,
    abstraction: TrialAbstraction,
    evidence_map: dict[str, list[str]],
    *,
    require_all: bool,
) -> TrialCriterionTrace:
    fields = criterion.get("fields", [])
    values = [getattr(abstraction, field) for field in fields]
    matched_fields = [field for field, value in zip(fields, values, strict=True) if value]
    met = all(values) if require_all else any(values)

    if met:
        evidence = _combine_evidence(evidence_map, matched_fields)
        rationale = (
            f"Matched via {', '.join(field.replace('_', ' ') for field in matched_fields)}."
            if matched_fields
            else "Criterion satisfied."
        )
        status = "met"
    else:
        evidence = []
        rationale = (
            f"Did not meet required field(s): {', '.join(field.replace('_', ' ') for field in fields)}."
        )
        status = "missing"

    return TrialCriterionTrace(
        id=criterion["id"],
        label=criterion["label"],
        status=status,
        rationale=rationale,
        evidence=evidence,
    )


def _evaluate_exclusion_criterion(
    criterion: dict,
    abstraction: TrialAbstraction,
    evidence_map: dict[str, list[str]],
) -> TrialCriterionTrace:
    fields = criterion.get("fields", [])
    matched_fields = [field for field in fields if getattr(abstraction, field)]
    blocked = bool(matched_fields)
    return TrialCriterionTrace(
        id=criterion["id"],
        label=criterion["label"],
        status="blocked" if blocked else "clear",
        rationale=(
            f"Exclusion triggered by {', '.join(field.replace('_', ' ') for field in matched_fields)}."
            if blocked
            else "No exclusion language detected."
        ),
        evidence=_combine_evidence(evidence_map, matched_fields),
    )


def _pick_evidence(
    evidence_by_code: dict[str, list[str]],
    codes: list[str],
    *,
    fallback_phrases: list[str],
    report_text: str,
) -> list[str]:
    values: list[str] = []
    for code in codes:
        values.extend(evidence_by_code.get(code, []))
    if values:
        return _dedupe(values)
    return _find_phrases(report_text, fallback_phrases)


def _find_phrases(report_text: str, phrases: list[str]) -> list[str]:
    report_text_l = report_text.lower()
    matches: list[str] = []
    for phrase in phrases:
        if phrase.lower() in report_text_l:
            matches.append(phrase)
    return _dedupe(matches)


def _find_regex_matches(report_text: str, pattern: re.Pattern[str]) -> list[str]:
    return _dedupe([match.group(0) for match in pattern.finditer(report_text)])


def _combine_evidence(evidence_map: dict[str, list[str]], fields: list[str]) -> list[str]:
    combined: list[str] = []
    for field in fields:
        combined.extend(evidence_map.get(field, []))
    return _dedupe(combined)


def _dedupe(values: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        ordered.append(cleaned)
    return ordered
