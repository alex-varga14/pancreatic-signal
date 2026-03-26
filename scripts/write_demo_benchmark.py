import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
DEFAULT_OUT_DIR = ROOT / "artifacts" / "benchmarks"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.evaluation import (
    DEMO_LABELS_PATH,
    DEMO_REPORTS_PATH,
    compare_demo_evaluation,
    sweep_demo_thresholds,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write a reproducible demo benchmark snapshot as JSON and Markdown."
    )
    parser.add_argument("--threshold", type=float, default=0.3, help="Comparison threshold between 0 and 1.")
    parser.add_argument("--top-k", type=int, default=3, help="Top-k queue depth to analyze.")
    parser.add_argument(
        "--thresholds",
        type=str,
        default="",
        help="Optional comma-separated thresholds for the sweep, for example 0.2,0.3,0.4.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Directory that will receive the JSON and Markdown benchmark artifacts.",
    )
    parser.add_argument(
        "--basename",
        type=str,
        default="demo-benchmark",
        help="Base filename for the written artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    thresholds = [float(item.strip()) for item in args.thresholds.split(",") if item.strip()] or None

    snapshot = build_snapshot(
        threshold=args.threshold,
        top_k=args.top_k,
        thresholds=thresholds,
    )

    out_dir = args.out_dir if args.out_dir.is_absolute() else (ROOT / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{args.basename}.json"
    markdown_path = out_dir / f"{args.basename}.md"

    json_path.write_text(json.dumps(snapshot, indent=2) + "\n")
    markdown_path.write_text(render_markdown(snapshot))

    print(f"Wrote {display_path(json_path)}")
    print(f"Wrote {display_path(markdown_path)}")


def build_snapshot(
    *,
    threshold: float,
    top_k: int,
    thresholds: list[float] | None,
) -> dict[str, object]:
    comparison = compare_demo_evaluation(threshold=threshold, top_k=top_k)
    sweep = sweep_demo_thresholds(top_k=top_k, thresholds=thresholds)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "dataset": {
            "reports_path": str(DEMO_REPORTS_PATH.relative_to(ROOT)),
            "labels_path": str(DEMO_LABELS_PATH.relative_to(ROOT)),
        },
        "dataset_summary": build_dataset_summary(comparison),
        "queue_preview": build_queue_preview(comparison),
        "comparison": comparison.model_dump(mode="json"),
        "sweep": sweep.model_dump(mode="json"),
        "casebook": build_casebook(comparison),
    }


def build_dataset_summary(comparison) -> dict[str, object]:
    cases = comparison.rules.cases
    bucket_counts: dict[str, dict[str, int | str]] = {}

    for case in cases:
        bucket = case.benchmark_bucket or "unbucketed"
        entry = bucket_counts.setdefault(
            bucket,
            {
                "bucket": bucket,
                "case_count": 0,
                "positive_count": 0,
                "escalation_count": 0,
            },
        )
        entry["case_count"] += 1
        if case.expected_positive:
            entry["positive_count"] += 1
        if case.expected_escalation:
            entry["escalation_count"] += 1

    return {
        "report_count": len(cases),
        "positive_count": sum(1 for case in cases if case.expected_positive),
        "escalation_count": sum(1 for case in cases if case.expected_escalation),
        "bucket_counts": sorted(bucket_counts.values(), key=lambda item: str(item["bucket"])),
    }


def build_queue_preview(comparison) -> dict[str, object]:
    top_k = comparison.top_k
    return {
        "top_k": top_k,
        "rules": [build_queue_entry(case) for case in comparison.rules.cases[:top_k]],
        "hybrid": [build_queue_entry(case) for case in comparison.hybrid.cases[:top_k]],
    }


def build_queue_entry(case) -> dict[str, object]:
    return {
        "case_id": case.case_id,
        "report_id": case.report_id,
        "benchmark_bucket": case.benchmark_bucket,
        "score": round(case.score, 4),
        "outcome": classify_outcome(case),
    }


def build_casebook(comparison) -> list[dict[str, object]]:
    rules_by_case_id = {case.case_id: case for case in comparison.rules.cases}
    hybrid_by_case_id = {case.case_id: case for case in comparison.hybrid.cases}

    casebook: list[dict[str, object]] = []
    for case_id in sorted(rules_by_case_id):
        rules_case = rules_by_case_id[case_id]
        hybrid_case = hybrid_by_case_id[case_id]
        casebook.append(
            {
                "case_id": case_id,
                "report_id": rules_case.report_id,
                "benchmark_bucket": rules_case.benchmark_bucket,
                "reviewer_focus": rules_case.reviewer_focus,
                "label_notes": rules_case.label_notes,
                "expected_positive": rules_case.expected_positive,
                "expected_escalation": rules_case.expected_escalation,
                "expected_rationale_codes": rules_case.expected_rationale_codes,
                "hybrid_lift": round(hybrid_case.score - rules_case.score, 4),
                "rules": summarize_case_mode(rules_case),
                "hybrid": summarize_case_mode(hybrid_case),
            }
        )
    return casebook


def summarize_case_mode(case) -> dict[str, object]:
    return {
        "score": round(case.score, 4),
        "flagged": case.flagged,
        "outcome": classify_outcome(case),
        "rationale_codes": case.rationale_codes,
    }


def classify_outcome(case) -> str:
    if case.flagged and case.expected_positive:
        return "true_positive"
    if case.flagged and not case.expected_positive:
        return "false_positive"
    if not case.flagged and case.expected_positive:
        return "missed_positive"
    return "true_negative"


def render_markdown(snapshot: dict[str, object]) -> str:
    comparison = snapshot["comparison"]
    sweep = snapshot["sweep"]
    dataset_summary = snapshot["dataset_summary"]
    queue_preview = snapshot["queue_preview"]
    casebook = snapshot["casebook"]
    rules = comparison["rules"]
    hybrid = comparison["hybrid"]

    lines = [
        "# Demo Benchmark Snapshot",
        "",
        f"- Generated at: {snapshot['generated_at']}",
        f"- Reports: `{snapshot['dataset']['reports_path']}`",
        f"- Labels: `{snapshot['dataset']['labels_path']}`",
        f"- Comparison threshold: {comparison['threshold']:.2f}",
        f"- Top-k: {comparison['top_k']}",
        "",
        "## Dataset Coverage",
        "",
        f"- Reports in casebook: {dataset_summary['report_count']}",
        f"- Positive labels: {dataset_summary['positive_count']}",
        f"- Escalation labels: {dataset_summary['escalation_count']}",
        f"- Benchmark buckets: {len(dataset_summary['bucket_counts'])}",
    ]

    for bucket in dataset_summary["bucket_counts"]:
        lines.append(
            f"- `{bucket['bucket']}`: {bucket['case_count']} case(s), "
            f"{bucket['positive_count']} positive, {bucket['escalation_count']} escalation-tagged"
        )

    lines.extend(
        [
        "",
        "## Comparison",
        "",
        "| Mode | Precision | Recall | F1 | Flagged | Top-k Precision | Top-k Sensitivity |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        format_comparison_row("Rules", rules),
        format_comparison_row("Hybrid", hybrid),
        "",
        (
            f"- Hybrid deltas at threshold {comparison['threshold']:.2f}: "
            f"precision {comparison['precision_delta']:+.4f}, "
            f"recall {comparison['recall_delta']:+.4f}, "
            f"F1 {comparison['f1_delta']:+.4f}, "
            f"flagged {comparison['flagged_delta']:+d}"
        ),
        f"- Newly flagged by hybrid: {format_case_ids(comparison['newly_flagged_cases'])}",
            f"- Resolved false negatives: {format_case_ids(comparison['resolved_false_negatives'])}",
            "",
            "## Top-k Queue Preview",
            "",
            f"- Rules top-{queue_preview['top_k']}: {format_queue(queue_preview['rules'])}",
            f"- Hybrid top-{queue_preview['top_k']}: {format_queue(queue_preview['hybrid'])}",
            "",
            "## Threshold Sweep",
            "",
            "| Threshold | Rules F1 | Hybrid F1 | Rules Recall | Hybrid Recall | Rules Flagged | Hybrid Flagged |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for point in sweep["points"]:
        lines.append(
            "| "
            f"{point['threshold']:.2f} | "
            f"{point['rules_f1']:.4f} | "
            f"{point['hybrid_f1']:.4f} | "
            f"{point['rules_recall']:.4f} | "
            f"{point['hybrid_recall']:.4f} | "
            f"{point['rules_flagged']} | "
            f"{point['hybrid_flagged']} |"
        )

    lines.extend(
        [
            "",
            "## Recommended Operating Points",
            "",
            (
                f"- Rules: threshold {sweep['rules_recommendation']['recommended_threshold']:.2f}, "
                f"F1 {sweep['rules_recommendation']['f1']:.4f}, "
                f"recall {sweep['rules_recommendation']['recall']:.4f}, "
                f"flagged {sweep['rules_recommendation']['flagged']}"
            ),
            f"- Rules rationale: {sweep['rules_recommendation']['rationale']}",
            (
                f"- Hybrid: threshold {sweep['hybrid_recommendation']['recommended_threshold']:.2f}, "
                f"F1 {sweep['hybrid_recommendation']['f1']:.4f}, "
                f"recall {sweep['hybrid_recommendation']['recall']:.4f}, "
                f"flagged {sweep['hybrid_recommendation']['flagged']}"
            ),
            f"- Hybrid rationale: {sweep['hybrid_recommendation']['rationale']}",
            "",
            "## Reviewer Casebook",
            "",
        ]
    )

    for entry in casebook:
        lines.extend(
            [
                f"### {entry['case_id']} — {entry['benchmark_bucket'] or 'unbucketed'}",
                "",
                f"- Report: `{entry['report_id']}`",
                f"- Reviewer focus: {entry['reviewer_focus'] or 'none'}",
                f"- Label note: {entry['label_notes'] or 'none'}",
                f"- Expected positive: `{entry['expected_positive']}` | Expected escalation: `{entry['expected_escalation']}`",
                f"- Expected rationale cues: {format_case_ids(entry['expected_rationale_codes'])}",
                f"- Rules: {format_mode_summary(entry['rules'])}",
                f"- Hybrid: {format_mode_summary(entry['hybrid'])}",
                f"- Hybrid lift: {entry['hybrid_lift']:+.4f}",
                "",
            ]
        )

    return "\n".join(lines)


def format_comparison_row(name: str, summary: dict[str, object]) -> str:
    return (
        f"| {name} | "
        f"{summary['precision']:.4f} | "
        f"{summary['recall']:.4f} | "
        f"{summary['f1']:.4f} | "
        f"{summary['flagged']} | "
        f"{summary['precision_at_top_k']:.4f} | "
        f"{summary['sensitivity_at_top_k']:.4f} |"
    )


def format_case_ids(case_ids: list[str]) -> str:
    return ", ".join(case_ids) if case_ids else "none"


def format_mode_summary(mode: dict[str, object]) -> str:
    return (
        f"{mode['outcome']} at {mode['score']:.4f} "
        f"with rationale cues {format_case_ids(mode['rationale_codes'])}"
    )


def format_queue(entries: list[dict[str, object]]) -> str:
    formatted = []
    for entry in entries:
        formatted.append(
            f"{entry['case_id']} ({entry['benchmark_bucket'] or 'unbucketed'}, {entry['outcome']}, {entry['score']:.4f})"
        )
    return " -> ".join(formatted) if formatted else "none"


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()
