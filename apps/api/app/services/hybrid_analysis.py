from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from app.schemas.hybrid import HybridAnalysis, SentenceCandidate, SentenceSignal
from app.schemas.triage import EvidenceSpan
from app.services.ontology import load_ontology
from app.services.text_utils import sentence_spans, split_sections

_GENERIC_PRE_NEGATION_RE = re.compile(
    r"\b(no|without|absent|absence of|free of|negative for|not)\b",
    flags=re.IGNORECASE,
)
_GENERIC_POST_NEGATION_RE = re.compile(
    r"\b(not seen|not identified|not visualized|not appreciated|is absent|are absent|absent)\b",
    flags=re.IGNORECASE,
)
_PANCREATIC_CONTEXT_RE = re.compile(
    r"\b(pancrea\w+|uncinate|ampulla|pancreatic duct|pdac|ipmn)\b",
    flags=re.IGNORECASE,
)
_MALIGNANCY_RE = re.compile(
    r"\b(mass|lesion|neoplasm|adenocarcinoma|carcinoma|malignan\w+|tumou?r)\b",
    flags=re.IGNORECASE,
)
_SECONDARY_SIGN_RE = re.compile(
    r"\b(cutoff|cut-off|double duct|dilat\w+|atrophy|upstream)\b",
    flags=re.IGNORECASE,
)
_FOLLOWUP_RE = re.compile(
    r"\b(recommend|follow-?up|eus|biopsy|tissue sampling|sampling|fna|fnb|evaluation)\b",
    flags=re.IGNORECASE,
)
_TISSUE_CONFIRMATION_RE = re.compile(
    r"\b(eus|biopsy|tissue sampling|fna|fnb)\b",
    flags=re.IGNORECASE,
)
_BENIGN_RE = re.compile(
    r"\b(unremarkable|no acute abnormality|compatible with pancreatitis|acute pancreatitis)\b",
    flags=re.IGNORECASE,
)
_CYST_RE = re.compile(r"\b(cystic lesion|ipmn|cyst)\b", flags=re.IGNORECASE)
_PANCREATITIS_RE = re.compile(r"\bpancreatitis|inflammatory change\b", flags=re.IGNORECASE)
_SUSPICION_RE = re.compile(
    r"\b(suspicious for|cannot exclude|cannot be excluded|concerning for|worrisome for)\b",
    flags=re.IGNORECASE,
)
_PANCREATIC_NEGATED_RE = re.compile(
    r"\b(no|without|absent|not)\b.{0,25}\b(pancreatic mass|pancreatic duct|mass|lesion|dilat\w+)\b",
    flags=re.IGNORECASE,
)


def analyze_hybrid_report(
    *,
    report_text: str,
    score: float,
    urgency: str,
    rationale_codes: Sequence[str],
    evidence: Sequence[EvidenceSpan | Mapping[str, Any]],
) -> HybridAnalysis:
    ontology = load_ontology()
    evidence_by_sentence = _group_evidence_by_sentence(evidence)
    family_by_code = {
        family["code"]: family
        for family in ontology.get("families", [])
        if "code" in family
    }
    uncertainty_phrases = [item.lower() for item in ontology.get("uncertainty", [])]
    negations = [item.lower() for item in ontology.get("negations", [])]

    candidates: list[SentenceCandidate] = []
    report_sentences = 0
    supportive_candidates = 0

    for section in split_sections(report_text):
        for sentence in sentence_spans(section.text):
            grouped = evidence_by_sentence.get(report_sentences, [])
            candidate = _score_sentence(
                text=sentence.text,
                section=section.name,
                sentence_index=report_sentences,
                evidence=grouped,
                family_by_code=family_by_code,
                uncertainty_phrases=uncertainty_phrases,
                negations=negations,
            )
            if candidate is not None:
                candidates.append(candidate)
                if candidate.score >= 0.25:
                    supportive_candidates += 1
            report_sentences += 1

    candidates.sort(key=lambda item: (-item.score, item.sentence_index, item.section, item.text))
    top_candidates = candidates[:5]
    top_score = top_candidates[0].score if top_candidates else 0.0
    unique_codes = sorted({code for candidate in top_candidates for code in candidate.matched_codes})

    calibrated_score = score
    if top_score:
        calibrated_score = max(calibrated_score, top_score)
        calibrated_score += min(0.10, 0.03 * max(0, supportive_candidates - 1))
        calibrated_score += min(0.08, 0.02 * len(unique_codes))
        if any(candidate.classification == "actionable_followup" for candidate in top_candidates):
            calibrated_score += 0.04

    if score == 0.0 and any(candidate.classification == "actionable_followup" for candidate in top_candidates):
        calibrated_score = max(calibrated_score, 0.32)

    if any(candidate.classification == "explicit_suspicion" for candidate in top_candidates):
        calibrated_score = max(calibrated_score, 0.72)
    if any(candidate.classification == "secondary_sign_cluster" for candidate in top_candidates):
        calibrated_score = max(calibrated_score, 0.48)

    calibrated_score = round(min(max(calibrated_score, 0.0), 1.0), 4)

    confidence_label = _confidence_label(calibrated_score)
    review_priority = _review_priority(calibrated_score=calibrated_score, urgency=urgency, candidates=top_candidates)
    active_learning_priority = _active_learning_priority(
        score=score,
        calibrated_score=calibrated_score,
        rationale_codes=rationale_codes,
        candidates=top_candidates,
    )
    factors = _build_factors(
        score=score,
        calibrated_score=calibrated_score,
        rationale_codes=rationale_codes,
        candidates=top_candidates,
    )
    summary = _build_summary(
        calibrated_score=calibrated_score,
        confidence_label=confidence_label,
        review_priority=review_priority,
        candidates=top_candidates,
        rationale_codes=rationale_codes,
    )

    return HybridAnalysis(
        calibrated_score=calibrated_score,
        confidence_label=confidence_label,
        review_priority=review_priority,
        active_learning_priority=active_learning_priority,
        summary=summary,
        factors=factors,
        sentence_candidates=top_candidates,
    )


def _group_evidence_by_sentence(
    evidence: Sequence[EvidenceSpan | Mapping[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = {}

    for item in evidence:
        sentence_index = _evidence_value(item, "sentence_index")
        if sentence_index is None:
            continue
        grouped.setdefault(int(sentence_index), []).append(
            {
                "code": _evidence_value(item, "code") or "",
                "text": _evidence_value(item, "text") or "",
                "section": _evidence_value(item, "section") or "unknown",
            }
        )

    return grouped


def _score_sentence(
    *,
    text: str,
    section: str,
    sentence_index: int,
    evidence: Sequence[dict[str, Any]],
    family_by_code: Mapping[str, dict[str, Any]],
    uncertainty_phrases: Sequence[str],
    negations: Sequence[str],
) -> SentenceCandidate | None:
    signals: list[SentenceSignal] = []
    matched_codes: list[str] = []
    sentence_l = text.lower()

    for item in evidence:
        code = str(item.get("code") or "")
        family = family_by_code.get(code)
        if family is None or code in matched_codes:
            continue

        matched_codes.append(code)
        signals.append(
            SentenceSignal(
                code=code,
                label=str(family.get("label") or code),
                weight=round(min(0.45, float(family.get("weight", 0.0)) * 0.85 + 0.08), 3),
                rationale="Matched deterministic triage rationale in this sentence.",
            )
        )

    if _PANCREATIC_CONTEXT_RE.search(text):
        signals.append(
            SentenceSignal(
                code="PANCREATIC_CONTEXT",
                label="Pancreatic context",
                weight=0.08,
                rationale="Sentence refers to pancreatic anatomy or disease context.",
            )
        )

    if _MALIGNANCY_RE.search(text):
        signals.append(
            SentenceSignal(
                code="MALIGNANCY_LANGUAGE",
                label="Mass or malignancy language",
                weight=0.14,
                rationale="Sentence contains lesion, mass, or malignancy terminology.",
            )
        )

    if _SECONDARY_SIGN_RE.search(text):
        signals.append(
            SentenceSignal(
                code="SECONDARY_SIGN_LANGUAGE",
                label="Secondary sign language",
                weight=0.12,
                rationale="Sentence includes ductal or atrophy wording associated with pancreatic obstruction.",
            )
        )

    if _FOLLOWUP_RE.search(text):
        signals.append(
            SentenceSignal(
                code="FOLLOWUP_LANGUAGE",
                label="Actionable follow-up language",
                weight=0.10,
                rationale="Sentence recommends further evaluation, tissue sampling, or interval follow-up.",
            )
        )

    if _TISSUE_CONFIRMATION_RE.search(text):
        signals.append(
            SentenceSignal(
                code="TISSUE_CONFIRMATION",
                label="Tissue confirmation cue",
                weight=0.06,
                rationale="Sentence specifically suggests biopsy, EUS, or tissue sampling.",
            )
        )

    if _CYST_RE.search(text) and _PANCREATIC_CONTEXT_RE.search(text):
        signals.append(
            SentenceSignal(
                code="PANCREATIC_CYSTIC_SIGNAL",
                label="Pancreatic cystic lesion",
                weight=0.15,
                rationale="Sentence mentions pancreatic cystic pathology that may still warrant review.",
            )
        )

    if (any(phrase in sentence_l for phrase in uncertainty_phrases) or _SUSPICION_RE.search(text)) and (
        _PANCREATIC_CONTEXT_RE.search(text) or _MALIGNANCY_RE.search(text)
    ):
        signals.append(
            SentenceSignal(
                code="UNCERTAINTY_SIGNAL",
                label="Uncertainty around pancreatic finding",
                weight=0.08,
                rationale="Sentence expresses uncertainty around a pancreatic or malignant finding.",
            )
        )

    if _BENIGN_RE.search(text):
        signals.append(
            SentenceSignal(
                code="BENIGN_CONTEXT",
                label="Benign context",
                weight=-0.20,
                rationale="Sentence contains benign or normalizing language that lowers suspicion.",
            )
        )

    if _PANCREATITIS_RE.search(text) and not matched_codes:
        signals.append(
            SentenceSignal(
                code="PANCREATITIS_CONFOUNDER",
                label="Pancreatitis confounder",
                weight=-0.12,
                rationale="Inflammatory pancreatitis wording can mimic pancreatic findings without implying malignancy.",
            )
        )

    if _sentence_has_negated_pancreatic_finding(text, negations):
        signals.append(
            SentenceSignal(
                code="NEGATED_FINDING",
                label="Negated pancreatic finding",
                weight=-0.22,
                rationale="Nearby negation suppresses pancreatic mass or duct abnormality language.",
            )
        )

    score = sum(signal.weight for signal in signals)
    if len(matched_codes) >= 2:
        score += 0.05
    if _PANCREATIC_CONTEXT_RE.search(text) and _FOLLOWUP_RE.search(text):
        score += 0.04
    if _MALIGNANCY_RE.search(text) and _SUSPICION_RE.search(text):
        score += 0.08

    score = round(min(max(score, 0.0), 1.0), 4)
    if score < 0.12 and not matched_codes:
        return None

    return SentenceCandidate(
        text=text,
        section=section,
        sentence_index=sentence_index,
        score=score,
        classification=_classify_sentence(score=score, matched_codes=matched_codes, text=text),
        matched_codes=matched_codes,
        signals=signals,
    )


def _classify_sentence(*, score: float, matched_codes: Sequence[str], text: str) -> str:
    if "PDAC_EXPLICIT_SUSPICION" in matched_codes or (_SUSPICION_RE.search(text) and _MALIGNANCY_RE.search(text)):
        return "explicit_suspicion"
    if "FOLLOWUP_RECOMMENDED" in matched_codes or (_FOLLOWUP_RE.search(text) and _PANCREATIC_CONTEXT_RE.search(text)):
        return "actionable_followup"
    if {"DOUBLE_DUCT_SIGN", "DUCT_CUTOFF", "DUCT_DILATION", "FOCAL_ATROPHY"} & set(matched_codes):
        return "secondary_sign_cluster"
    if _CYST_RE.search(text) and _FOLLOWUP_RE.search(text):
        return "actionable_followup"
    if score >= 0.25:
        return "supporting_signal"
    return "low_signal"


def _sentence_has_negated_pancreatic_finding(text: str, negations: Sequence[str]) -> bool:
    sentence_l = text.lower()
    if any(phrase in sentence_l for phrase in negations):
        return True
    if _PANCREATIC_NEGATED_RE.search(text):
        return True

    for term in ("pancreatic mass", "pancreatic duct", "mass", "lesion", "dilation", "dilatation"):
        match_start = sentence_l.find(term)
        if match_start == -1:
            continue
        match_end = match_start + len(term)
        prefix_window = sentence_l[max(0, match_start - 60) : match_start]
        suffix_window = sentence_l[match_end : match_end + 40]
        if _GENERIC_PRE_NEGATION_RE.search(prefix_window):
            return True
        if _GENERIC_POST_NEGATION_RE.search(suffix_window):
            return True

    return False


def _confidence_label(calibrated_score: float) -> str:
    if calibrated_score >= 0.75:
        return "high"
    if calibrated_score >= 0.45:
        return "moderate"
    if calibrated_score >= 0.25:
        return "borderline"
    return "low"


def _review_priority(
    *,
    calibrated_score: float,
    urgency: str,
    candidates: Sequence[SentenceCandidate],
) -> str:
    if urgency == "critical" or calibrated_score >= 0.75:
        return "expedite"
    if calibrated_score >= 0.25 or any(
        candidate.classification == "actionable_followup" for candidate in candidates
    ):
        return "review"
    return "defer"


def _active_learning_priority(
    *,
    score: float,
    calibrated_score: float,
    rationale_codes: Sequence[str],
    candidates: Sequence[SentenceCandidate],
) -> str:
    if score == 0.0 and calibrated_score >= 0.25:
        return "high"
    if abs(calibrated_score - score) >= 0.15:
        return "high"
    if not rationale_codes and any(candidate.score >= 0.2 for candidate in candidates):
        return "high"
    if any(candidate.classification == "actionable_followup" for candidate in candidates):
        return "medium"
    if candidates:
        return "medium"
    return "low"


def _build_factors(
    *,
    score: float,
    calibrated_score: float,
    rationale_codes: Sequence[str],
    candidates: Sequence[SentenceCandidate],
) -> list[str]:
    factors: list[str] = []

    if rationale_codes:
        factors.append(f"Rule engine matched {', '.join(rationale_codes[:3])}.")
    if candidates:
        top = candidates[0]
        factors.append(
            f"Top sentence scored {top.score:.2f} in the {top.section} section as {top.classification}."
        )
    if score == 0.0 and calibrated_score >= 0.25:
        factors.append("Hybrid ranking surfaced a reviewable sentence despite no direct rule match.")
    if any(candidate.classification == "actionable_followup" for candidate in candidates):
        factors.append("Follow-up language increased reviewer value even when malignancy wording was limited.")
    if any(
        signal.code in {"UNCERTAINTY_SIGNAL", "PANCREATITIS_CONFOUNDER"}
        for candidate in candidates
        for signal in candidate.signals
    ):
        factors.append("Uncertainty or confounding language marks this case as useful for error analysis.")

    return factors[:4]


def _build_summary(
    *,
    calibrated_score: float,
    confidence_label: str,
    review_priority: str,
    candidates: Sequence[SentenceCandidate],
    rationale_codes: Sequence[str],
) -> str:
    if not candidates:
        return (
            f"Hybrid review found little additional support beyond the rule score "
            f"({calibrated_score:.2f}, {confidence_label} confidence, {review_priority} priority)."
        )

    top = candidates[0]
    rationale = ", ".join(rationale_codes[:3]) if rationale_codes else "no direct rule family"
    return (
        f"Hybrid ranking prioritizes sentence {top.sentence_index + 1} in {top.section} as "
        f"{top.classification}; calibrated score {calibrated_score:.2f} with {confidence_label} "
        f"confidence and {review_priority} priority, anchored by {rationale}."
    )


def _evidence_value(item: EvidenceSpan | Mapping[str, Any], key: str) -> Any:
    if isinstance(item, Mapping):
        return item.get(key)
    return getattr(item, key, None)
