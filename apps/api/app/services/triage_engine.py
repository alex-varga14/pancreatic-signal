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
# Clauses joined by these connectors are treated as a fresh negation scope so
# that "no mass; pancreatic head lesion is present" does not negate the lesion.
_CLAUSE_BOUNDARY_RE = re.compile(r"[;,]|\bbut\b|\bhowever\b|\byet\b", flags=re.IGNORECASE)

# Default scoring profile used when an ontology omits the optional "scoring" block.
# See data/ontologies/pancreatic_signal_rules.json for the runtime profile and
# docs/AUTORESEARCH.md for the ontology-tuning surface used by autoresearch.
_DEFAULT_SCORING: dict[str, object] = {
    "method": "additive",
    "max_score": 1.0,
    "round_digits": 4,
}


def _match_is_negated(sentence: str, match_start: int, match_end: int, negations: list[str]) -> bool:
    """Return True when the match falls inside a negation scope within the same clause.

    The scope is the clause-bounded prefix and short suffix relative to the match.
    Clause boundaries (commas, semicolons, and contrastive connectors like "but")
    reset the scope so a negation cannot leak across them. Sentence boundaries
    are already enforced by the caller, which only passes the current sentence.
    """
    sentence_l = sentence.lower()
    clause_start = _clause_scope_start(sentence_l, match_start)
    prefix_window = sentence_l[clause_start:match_start]
    inclusive_window = sentence_l[clause_start:match_end]
    suffix_window = sentence_l[match_end : _clause_scope_end(sentence_l, match_end)]

    if any(phrase in inclusive_window for phrase in negations):
        return True
    if _GENERIC_PRE_NEGATION_RE.search(prefix_window):
        return True
    if _GENERIC_POST_NEGATION_RE.search(suffix_window):
        return True
    return False


def _clause_scope_start(sentence_l: str, match_start: int) -> int:
    last_boundary_end = 0
    for boundary in _CLAUSE_BOUNDARY_RE.finditer(sentence_l, 0, match_start):
        last_boundary_end = boundary.end()
    return last_boundary_end


def _clause_scope_end(sentence_l: str, match_end: int) -> int:
    boundary = _CLAUSE_BOUNDARY_RE.search(sentence_l, match_end)
    return boundary.start() if boundary else len(sentence_l)


def _resolve_scoring_profile(ontology: dict) -> dict:
    profile = dict(_DEFAULT_SCORING)
    profile.update(ontology.get("scoring") or {})
    return profile


def _apply_scoring_profile(family_scores: list[float], profile: dict) -> float:
    method = str(profile.get("method", "additive")).lower()
    max_score = float(profile.get("max_score", 1.0))
    round_digits = int(profile.get("round_digits", 4))

    if method == "max":
        raw = max(family_scores) if family_scores else 0.0
    elif method == "weighted_sum":
        weight = float(profile.get("global_weight", 1.0))
        raw = sum(score * weight for score in family_scores)
    else:
        raw = sum(family_scores)

    return min(round(raw, round_digits), max_score)


def triage_report(payload: ReportInput, *, persist: bool = True) -> TriageResult:
    """Deterministic rules-only triage engine.

    Negation: clause-bounded windows inside the matched sentence (no leakage
    across sentences or clause boundaries). Configurable via ontology negations.

    Scoring: driven by the optional ``scoring`` block on the ontology so the
    autoresearch loop can tune calibration without code changes. Defaults to
    additive scoring with a max of 1.0.

    Persistence: structured ``FindingRecord`` rows are persisted by the case
    store keyed off the evidence list returned here.
    """
    ontology = load_ontology()
    normalized = normalize_text(payload.report_text)
    sections = split_sections(normalized)
    evidence: list[EvidenceSpan] = []
    rationale_codes: list[str] = []
    family_scores: list[float] = []
    seen_evidence_keys: set[tuple[str, int, int]] = set()

    negations = [item.lower() for item in ontology.get("negations", [])]
    scoring_profile = _resolve_scoring_profile(ontology)

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
            family_scores.append(family_weight)

    evidence.sort(key=lambda item: (item.start, item.end, item.code))

    score = _apply_scoring_profile(family_scores, scoring_profile)

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
