import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.evaluation import compare_demo_evaluation, evaluate_demo_dataset, summary_to_json, sweep_demo_thresholds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run labeled evaluation on the demo pancreatic report dataset."
    )
    parser.add_argument("--threshold", type=float, default=0.3, help="Flagging threshold between 0 and 1.")
    parser.add_argument("--top-k", type=int, default=3, help="Top-k queue depth to analyze.")
    parser.add_argument(
        "--score-mode",
        choices=("rules", "hybrid"),
        default="rules",
        help="Select whether evaluation uses the baseline rule score or the explainable hybrid score.",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare rules and hybrid evaluation side by side at the selected threshold and top-k.",
    )
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Sweep multiple thresholds and recommend operating points for rules and hybrid scoring.",
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="",
        help="Optional comma-separated thresholds for --sweep, for example 0.2,0.3,0.4.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the evaluation summary as JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.sweep:
        thresholds = [float(item.strip()) for item in args.thresholds.split(",") if item.strip()] or None
        sweep = sweep_demo_thresholds(top_k=args.top_k, thresholds=thresholds)

        if args.json:
            import json

            print(json.dumps(sweep.model_dump(mode="json"), indent=2))
            return

        print(f"Swept thresholds for top-{sweep.top_k} queue depth")
        print(
            f"Recommended rules threshold {sweep.rules_recommendation.recommended_threshold:.2f} | "
            f"Recommended hybrid threshold {sweep.hybrid_recommendation.recommended_threshold:.2f}"
        )
        print(
            f"Rules rationale: {sweep.rules_recommendation.rationale}\n"
            f"Hybrid rationale: {sweep.hybrid_recommendation.rationale}"
        )
        print("Threshold points:")
        for point in sweep.points:
            print(
                f"  {point.threshold:.2f} | rules f1={point.rules_f1:.2f} recall={point.rules_recall:.2f} flagged={point.rules_flagged} | "
                f"hybrid f1={point.hybrid_f1:.2f} recall={point.hybrid_recall:.2f} flagged={point.hybrid_flagged}"
            )
        return

    if args.compare:
        comparison = compare_demo_evaluation(threshold=args.threshold, top_k=args.top_k)

        if args.json:
            import json

            print(json.dumps(comparison.model_dump(mode="json"), indent=2))
            return

        print(
            f"Compared rules vs hybrid at threshold {comparison.threshold:.2f} "
            f"with top-{comparison.top_k} queue depth"
        )
        print(
            f"Recall delta {comparison.recall_delta:+.2f} | "
            f"F1 delta {comparison.f1_delta:+.2f} | "
            f"Flagged delta {comparison.flagged_delta:+d}"
        )
        print(
            f"Newly flagged: {', '.join(comparison.newly_flagged_cases) or 'none'} | "
            f"Resolved false negatives: {', '.join(comparison.resolved_false_negatives) or 'none'}"
        )
        return

    summary = evaluate_demo_dataset(
        threshold=args.threshold,
        top_k=args.top_k,
        score_mode=args.score_mode,
    )

    if args.json:
        print(summary_to_json(summary))
        return

    print(
        f"Processed {summary.processed} reports at threshold {summary.threshold:.2f} "
        f"using {summary.score_mode} scoring"
    )
    print(
        f"Precision {summary.precision:.2f} | "
        f"Recall {summary.recall:.2f} | "
        f"F1 {summary.f1:.2f}"
    )
    print(
        f"Top-{summary.top_k} precision {summary.precision_at_top_k:.2f} | "
        f"Sensitivity {summary.sensitivity_at_top_k:.2f} | "
        f"Reviewer yield {summary.reviewer_yield_at_top_k:.2f}"
    )

    if summary.false_negative_buckets:
        print("False negative buckets:")
        for bucket, count in sorted(summary.false_negative_buckets.items()):
            print(f"  {bucket}: {count}")

    print("Ranked cases:")
    for case in summary.cases:
        label = (
            "TP"
            if case.flagged and case.expected_positive
            else "FP"
            if case.flagged
            else "MISS"
            if case.expected_positive
            else "TN"
        )
        print(
            f"  {case.case_id} | score={case.score:.2f} | baseline={case.base_score:.2f} | "
            f"hybrid={case.hybrid_score:.2f} | {case.urgency} | "
            f"{label} | {','.join(case.rationale_codes) or 'none'}"
        )


if __name__ == "__main__":
    main()
