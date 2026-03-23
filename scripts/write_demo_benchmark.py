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

    comparison = compare_demo_evaluation(threshold=args.threshold, top_k=args.top_k)
    sweep = sweep_demo_thresholds(top_k=args.top_k, thresholds=thresholds)

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "dataset": {
            "reports_path": str(DEMO_REPORTS_PATH.relative_to(ROOT)),
            "labels_path": str(DEMO_LABELS_PATH.relative_to(ROOT)),
        },
        "comparison": comparison.model_dump(mode="json"),
        "sweep": sweep.model_dump(mode="json"),
    }

    out_dir = args.out_dir if args.out_dir.is_absolute() else (ROOT / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{args.basename}.json"
    markdown_path = out_dir / f"{args.basename}.md"

    json_path.write_text(json.dumps(snapshot, indent=2) + "\n")
    markdown_path.write_text(render_markdown(snapshot))

    print(f"Wrote {json_path.relative_to(ROOT)}")
    print(f"Wrote {markdown_path.relative_to(ROOT)}")


def render_markdown(snapshot: dict[str, object]) -> str:
    comparison = snapshot["comparison"]
    sweep = snapshot["sweep"]
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
        "## Threshold Sweep",
        "",
        "| Threshold | Rules F1 | Hybrid F1 | Rules Recall | Hybrid Recall | Rules Flagged | Hybrid Flagged |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

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


if __name__ == "__main__":
    main()
