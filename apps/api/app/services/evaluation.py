from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from app.core.paths import resolve_data_path
from app.schemas.evaluation import (
    DemoScoreMode,
    EvaluationCaseResult,
    EvaluationComparison,
    EvaluationLabel,
    EvaluationSummary,
    ExternalEvaluationPrediction,
    ExternalThresholdRecommendation,
    ExternalThresholdSweepPoint,
    ExternalThresholdSweepSummary,
    ScoreMode,
    ThresholdRecommendation,
    ThresholdSweepPoint,
    ThresholdSweepSummary,
)
from app.schemas.triage import ReportInput
from app.services.triage_engine import triage_report

DEMO_REPORTS_PATH = resolve_data_path("examples", "reports.jsonl")
DEMO_LABELS_PATH = resolve_data_path("examples", "report_labels.jsonl")
DEFAULT_SWEEP_THRESHOLDS = (0.2, 0.3, 0.4, 0.5, 0.6)


def load_demo_labels() -> dict[str, EvaluationLabel]:
    return load_evaluation_labels(DEMO_LABELS_PATH)


def load_evaluation_labels(path: Path) -> dict[str, EvaluationLabel]:
    labels: dict[str, EvaluationLabel] = {}
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            label = EvaluationLabel.model_validate_json(line)
            labels[_case_key(label.report_id, label.case_id)] = label
    return labels


def load_demo_reports() -> list[ReportInput]:
    reports: list[ReportInput] = []
    with DEMO_REPORTS_PATH.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            reports.append(ReportInput.model_validate_json(line))
    return reports


def evaluate_demo_dataset(
    threshold: float = 0.3,
    top_k: int = 3,
    score_mode: DemoScoreMode = "rules",
) -> EvaluationSummary:
    normalized_top_k = max(1, top_k)
    labels = load_demo_labels()
    reports = load_demo_reports()
    cases: list[EvaluationCaseResult] = []

    for payload in reports:
        label = labels[_case_key(payload.report_id, payload.case_id)]
        result = triage_report(payload, persist=False)
        hybrid_score = result.hybrid_analysis.calibrated_score if result.hybrid_analysis else result.score
        selected_score = result.score if score_mode == "rules" else hybrid_score
        cases.append(
            EvaluationCaseResult(
                report_id=result.report_id,
                case_id=result.case_id,
                score=selected_score,
                base_score=result.score,
                hybrid_score=hybrid_score,
                urgency=result.urgency,
                flagged=selected_score >= threshold,
                expected_positive=label.should_flag,
                expected_escalation=label.should_escalate,
                rationale_codes=result.rationale_codes,
                label_notes=label.notes,
                benchmark_bucket=label.benchmark_bucket,
                reviewer_focus=label.reviewer_focus,
                expected_rationale_codes=label.expected_rationale_codes,
            )
        )

    return summarize_cases(
        cases,
        threshold=threshold,
        top_k=normalized_top_k,
        score_mode=score_mode,
    )


def load_external_predictions(path: Path) -> dict[str, ExternalEvaluationPrediction]:
    predictions: dict[str, ExternalEvaluationPrediction] = {}
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            prediction = ExternalEvaluationPrediction.model_validate_json(line)
            case_key = _case_key(prediction.report_id, prediction.case_id)
            if case_key in predictions:
                raise ValueError(
                    f"Duplicate external prediction for report_id={prediction.report_id} case_id={prediction.case_id}."
                )
            predictions[case_key] = prediction
    return predictions


def evaluate_external_dataset(
    *,
    labels_path: Path,
    predictions_path: Path,
    threshold: float = 0.2,
    top_k: int = 25,
) -> EvaluationSummary:
    labels = load_evaluation_labels(labels_path)
    predictions = load_external_predictions(predictions_path)
    cases = build_external_case_results(labels=labels, predictions=predictions, threshold=threshold)
    return summarize_cases(
        cases,
        threshold=threshold,
        top_k=max(1, top_k),
        score_mode="external",
    )


def build_external_case_results(
    *,
    labels: dict[str, EvaluationLabel],
    predictions: dict[str, ExternalEvaluationPrediction],
    threshold: float,
) -> list[EvaluationCaseResult]:
    _validate_external_alignment(labels=labels, predictions=predictions)

    cases: list[EvaluationCaseResult] = []
    for case_key in sorted(labels):
        label = labels[case_key]
        prediction = predictions[case_key]
        flagged = prediction.score >= threshold
        cases.append(
            EvaluationCaseResult(
                report_id=label.report_id,
                case_id=label.case_id,
                score=prediction.score,
                base_score=prediction.score,
                hybrid_score=prediction.score,
                urgency="external",
                flagged=flagged,
                expected_positive=label.should_flag,
                expected_escalation=label.should_escalate,
                rationale_codes=prediction.rationale_codes,
                label_notes=label.notes,
                benchmark_bucket=label.benchmark_bucket,
                reviewer_focus=label.reviewer_focus,
                expected_rationale_codes=label.expected_rationale_codes,
                false_negative_bucket=prediction.false_negative_bucket if label.should_flag and not flagged else None,
            )
        )
    return cases


def summarize_cases(
    cases: list[EvaluationCaseResult],
    *,
    threshold: float,
    top_k: int,
    score_mode: ScoreMode = "rules",
) -> EvaluationSummary:
    normalized_top_k = max(1, top_k)
    processed = len(cases)
    positives = sum(1 for case in cases if case.expected_positive)
    flagged = sum(1 for case in cases if case.flagged)
    true_positives = sum(1 for case in cases if case.flagged and case.expected_positive)
    false_positives = sum(1 for case in cases if case.flagged and not case.expected_positive)
    true_negatives = sum(1 for case in cases if not case.flagged and not case.expected_positive)
    false_negatives = sum(1 for case in cases if not case.flagged and case.expected_positive)

    precision = _safe_divide(true_positives, true_positives + false_positives)
    recall = _safe_divide(true_positives, true_positives + false_negatives)
    f1 = _safe_divide(2 * precision * recall, precision + recall) if precision or recall else 0.0

    ranked = sorted(cases, key=lambda case: (-case.score, case.case_id))
    top_ranked = ranked[: min(normalized_top_k, len(ranked))]
    top_true_positives = sum(1 for case in top_ranked if case.expected_positive)
    precision_at_top_k = _safe_divide(top_true_positives, len(top_ranked))
    sensitivity_at_top_k = _safe_divide(top_true_positives, positives)

    false_negative_buckets: dict[str, int] = {}
    for case in cases:
        if case.flagged or not case.expected_positive:
            continue
        if case.false_negative_bucket:
            bucket = case.false_negative_bucket
        elif score_mode == "external":
            continue
        else:
            bucket = case.rationale_codes[0] if case.rationale_codes else "NO_MATCHED_RATIONALE"
        false_negative_buckets[bucket] = false_negative_buckets.get(bucket, 0) + 1

    return EvaluationSummary(
        score_mode=score_mode,
        threshold=threshold,
        top_k=normalized_top_k,
        processed=processed,
        positives=positives,
        flagged=flagged,
        true_positives=true_positives,
        false_positives=false_positives,
        true_negatives=true_negatives,
        false_negatives=false_negatives,
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        precision_at_top_k=round(precision_at_top_k, 4),
        sensitivity_at_top_k=round(sensitivity_at_top_k, 4),
        reviewer_yield_at_top_k=round(precision_at_top_k, 4),
        false_negative_buckets=false_negative_buckets,
        cases=ranked,
    )


def summary_to_json(summary: EvaluationSummary) -> str:
    return json.dumps(summary.model_dump(mode="json"), indent=2)


def compare_demo_evaluation(threshold: float = 0.3, top_k: int = 3) -> EvaluationComparison:
    rules = evaluate_demo_dataset(threshold=threshold, top_k=top_k, score_mode="rules")
    hybrid = evaluate_demo_dataset(threshold=threshold, top_k=top_k, score_mode="hybrid")

    rules_by_case_id = {case.case_id: case for case in rules.cases}
    hybrid_by_case_id = {case.case_id: case for case in hybrid.cases}

    newly_flagged_cases = sorted(
        case_id
        for case_id, hybrid_case in hybrid_by_case_id.items()
        if hybrid_case.flagged and not rules_by_case_id[case_id].flagged
    )
    resolved_false_negatives = sorted(
        case_id
        for case_id, hybrid_case in hybrid_by_case_id.items()
        if hybrid_case.flagged and hybrid_case.expected_positive and not rules_by_case_id[case_id].flagged
    )

    return EvaluationComparison(
        threshold=threshold,
        top_k=max(1, top_k),
        rules=rules,
        hybrid=hybrid,
        flagged_delta=hybrid.flagged - rules.flagged,
        precision_delta=round(hybrid.precision - rules.precision, 4),
        recall_delta=round(hybrid.recall - rules.recall, 4),
        f1_delta=round(hybrid.f1 - rules.f1, 4),
        precision_at_top_k_delta=round(hybrid.precision_at_top_k - rules.precision_at_top_k, 4),
        sensitivity_at_top_k_delta=round(hybrid.sensitivity_at_top_k - rules.sensitivity_at_top_k, 4),
        newly_flagged_cases=newly_flagged_cases,
        resolved_false_negatives=resolved_false_negatives,
    )


def sweep_demo_thresholds(
    *,
    top_k: int = 3,
    thresholds: Sequence[float] | None = None,
) -> ThresholdSweepSummary:
    normalized_top_k = max(1, top_k)
    normalized_thresholds = _normalize_thresholds(thresholds)
    comparisons = [
        compare_demo_evaluation(threshold=threshold, top_k=normalized_top_k)
        for threshold in normalized_thresholds
    ]

    points = [
        ThresholdSweepPoint(
            threshold=comparison.threshold,
            rules_f1=comparison.rules.f1,
            hybrid_f1=comparison.hybrid.f1,
            rules_recall=comparison.rules.recall,
            hybrid_recall=comparison.hybrid.recall,
            rules_flagged=comparison.rules.flagged,
            hybrid_flagged=comparison.hybrid.flagged,
            f1_delta=comparison.f1_delta,
            recall_delta=comparison.recall_delta,
            flagged_delta=comparison.flagged_delta,
        )
        for comparison in comparisons
    ]

    rules_summaries = [comparison.rules for comparison in comparisons]
    hybrid_summaries = [comparison.hybrid for comparison in comparisons]

    return ThresholdSweepSummary(
        top_k=normalized_top_k,
        thresholds=normalized_thresholds,
        points=points,
        rules_recommendation=_pick_threshold_recommendation(rules_summaries, score_mode="rules"),
        hybrid_recommendation=_pick_threshold_recommendation(hybrid_summaries, score_mode="hybrid"),
    )


def sweep_external_thresholds(
    *,
    labels_path: Path,
    predictions_path: Path,
    top_k: int = 25,
    thresholds: Sequence[float] | None = None,
) -> ExternalThresholdSweepSummary:
    normalized_top_k = max(1, top_k)
    normalized_thresholds = _normalize_thresholds(thresholds)
    labels = load_evaluation_labels(labels_path)
    predictions = load_external_predictions(predictions_path)

    summaries = [
        summarize_cases(
            build_external_case_results(labels=labels, predictions=predictions, threshold=threshold),
            threshold=threshold,
            top_k=normalized_top_k,
            score_mode="external",
        )
        for threshold in normalized_thresholds
    ]

    points = [
        ExternalThresholdSweepPoint(
            threshold=summary.threshold,
            f1=summary.f1,
            recall=summary.recall,
            flagged=summary.flagged,
            precision=summary.precision,
            precision_at_top_k=summary.precision_at_top_k,
            sensitivity_at_top_k=summary.sensitivity_at_top_k,
        )
        for summary in summaries
    ]

    return ExternalThresholdSweepSummary(
        top_k=normalized_top_k,
        thresholds=normalized_thresholds,
        points=points,
        recommendation=_pick_external_threshold_recommendation(summaries),
    )


def _safe_divide(numerator: int | float, denominator: int | float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def _normalize_thresholds(thresholds: Sequence[float] | None) -> list[float]:
    if not thresholds:
        return list(DEFAULT_SWEEP_THRESHOLDS)

    normalized = sorted({round(float(value), 2) for value in thresholds if 0.0 <= float(value) <= 1.0})
    return normalized or list(DEFAULT_SWEEP_THRESHOLDS)


def _pick_threshold_recommendation(
    summaries: Sequence[EvaluationSummary],
    *,
    score_mode: ScoreMode,
) -> ThresholdRecommendation:
    best = max(
        summaries,
        key=lambda summary: (
            summary.f1,
            summary.recall,
            -summary.flagged,
            -summary.threshold,
        ),
    )

    rationale = (
        f"Selected threshold {best.threshold:.2f} because it maximizes F1 "
        f"({best.f1:.2f}) while preserving recall {best.recall:.2f} "
        f"with {best.flagged} flagged case(s)."
    )
    return ThresholdRecommendation(
        score_mode=score_mode,
        recommended_threshold=best.threshold,
        rationale=rationale,
        f1=best.f1,
        recall=best.recall,
        flagged=best.flagged,
    )


def _pick_external_threshold_recommendation(
    summaries: Sequence[EvaluationSummary],
) -> ExternalThresholdRecommendation:
    best = max(
        summaries,
        key=lambda summary: (
            summary.f1,
            summary.recall,
            -summary.flagged,
            -summary.threshold,
        ),
    )
    rationale = (
        f"Selected threshold {best.threshold:.2f} because it maximizes F1 "
        f"({best.f1:.2f}) while preserving recall {best.recall:.2f} "
        f"with {best.flagged} flagged case(s)."
    )
    return ExternalThresholdRecommendation(
        recommended_threshold=best.threshold,
        rationale=rationale,
        f1=best.f1,
        recall=best.recall,
        flagged=best.flagged,
    )


def _validate_external_alignment(
    *,
    labels: dict[str, EvaluationLabel],
    predictions: dict[str, ExternalEvaluationPrediction],
) -> None:
    missing = sorted(case_key for case_key in labels if case_key not in predictions)
    extra = sorted(case_key for case_key in predictions if case_key not in labels)
    if missing or extra:
        details: list[str] = []
        if missing:
            details.append(f"missing predictions for {', '.join(missing[:5])}")
        if extra:
            details.append(f"extra predictions for {', '.join(extra[:5])}")
        raise ValueError("Prediction set must match labels exactly: " + "; ".join(details))


def _case_key(report_id: str, case_id: str) -> str:
    return f"{report_id}::{case_id}"
