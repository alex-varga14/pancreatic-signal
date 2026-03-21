from __future__ import annotations

import re

from app.schemas.triage import EvidenceSpan, ReportInput, TriageResult
from app.services.hybrid_analysis import analyze_hybrid_report
from app.services.ontology import load_ontology
from app.services.text_utils import normalize_text, sentence_spans, split_sections

_GENERIC_PRE_NEGATION_RE = re.compile(
    r"\b(no|without|absent|absence of|free of|negative for|not)\b",
    flags=re.IGNORECASE,
)
_GENERIC_POST_NEGATION_RE = re.compile(
    r"\b(not seen|not identified|not visualized|not appreciated|is absent|are absent|absent)\b",
    flags=re.IGNORECASE,
)


def _match_is_negated(sentence: str, match_start: int, match_end: int, negations: list[str]) -> bool:
    sentence_l = sentence.lower()
    prefix_window = sentence_l[max(0, match_start - 60) : match_start]
    inclusive_window = sentence_l[max(0, match_start - 60) : match_end]
    suffix_window = sentence_l[match_end : match_end + 40]

    if any(phrase in inclusive_window for phrase in negations):
        return True
    if _GENERIC_PRE_NEGATION_RE.search(prefix_window):
        return True
    if _GENERIC_POST_NEGATION_RE.search(suffix_window):
        return True
    return False


def triage_report(payload: ReportInput, *, persist: bool = True) -> TriageResult:
    """Deterministic rules-only triage engine.

    TODO for implementation agent:
    - improve negation window handling
    - persist structured findings, not just flattened evidence
    - replace simple additive score with calibrated scoring config
    """
    ontology = load_ontology()
    normalized = normalize_text(payload.report_text)
    sections = split_sections(normalized)
    evidence: list[EvidenceSpan] = []
    rationale_codes: list[str] = []
    score = 0.0
    seen_evidence_keys: set[tuple[str, int, int]] = set()

    negations = [item.lower() for item in ontology.get("negations", [])]

    for family in ontology.get("families", []):
        family_code = family["code"]
        family_weight = float(family["weight"])
        family_matched = False

        sentence_index = 0
        for section in sections:
            for sentence in sentence_spans(section.text):
                sentence_text = sentence.text
                for pattern in family.get("patterns", []):
                    matcher = re.compile(re.escape(pattern), flags=re.IGNORECASE)
                    for match in matcher.finditer(sentence_text):
                        if _match_is_negated(sentence_text, match.start(), match.end(), negations):
                            continue

                        start = section.start + sentence.start + match.start()
                        end = start + len(match.group(0))
                        evidence_key = (family_code, start, end)
                        if evidence_key in seen_evidence_keys:
                            continue

                        seen_evidence_keys.add(evidence_key)
                        family_matched = True
                        evidence.append(
                            EvidenceSpan(
                                text=normalized[start:end],
                                section=section.name,
                                start=start,
                                end=end,
                                code=family_code,
                                sentence_index=sentence_index,
                            )
                        )
                sentence_index += 1

        if family_matched:
            rationale_codes.append(family_code)
            score += family_weight

    evidence.sort(key=lambda item: (item.start, item.end, item.code))

    score = min(round(score, 4), 1.0)

    thresholds = ontology.get("thresholds", {})
    urgency = "low"
    if score >= float(thresholds.get("critical", 0.8)):
        urgency = "critical"
    elif score >= float(thresholds.get("high", 0.55)):
        urgency = "high"
    elif score >= float(thresholds.get("medium", 0.30)):
        urgency = "medium"

    result = TriageResult(
        report_id=payload.report_id,
        case_id=payload.case_id,
        score=score,
        urgency=urgency,
        rationale_codes=rationale_codes,
        evidence=evidence,
        hybrid_analysis=analyze_hybrid_report(
            report_text=payload.report_text,
            score=score,
            urgency=urgency,
            rationale_codes=rationale_codes,
            evidence=evidence,
        ),
    )

    if persist:
        from app.store.memory_store import CASE_STORE

        CASE_STORE.upsert_from_triage(payload, result)
    return result
