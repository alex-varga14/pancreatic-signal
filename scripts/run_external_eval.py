import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
DEFAULT_OUT_DIR = ROOT / "artifacts" / "benchmarks"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

try:
    from app.schemas.benchmark_submission import BenchmarkSubmission
    from app.services.evaluation import evaluate_external_dataset, sweep_external_thresholds
except ModuleNotFoundError as exc:  # pragma: no cover - import guard for unprepared environments
    raise SystemExit(
        "Missing API dependencies. Activate apps/api/.venv or run "
        "`make benchmark-external LABELS=... PREDICTIONS=...`."
    ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run comparable external evaluation and write a publishable results bundle."
    )
    parser.add_argument("--labels", type=Path, required=True, help="JSONL label file matching the public schema.")
    parser.add_argument(
        "--predictions",
        type=Path,
        required=True,
        help="JSONL external prediction file with report_id, case_id, and score.",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default="",
        help="Human-readable dataset name. Defaults to the labels filename stem.",
    )
    parser.add_argument("--dataset-split", type=str, default="test", help="Dataset split label.")
    parser.add_argument("--project-name", type=str, default="Pancreatic Signal", help="Project name.")
    parser.add_argument(
        "--submission-name",
        type=str,
        default="",
        help="Submission name. Defaults to a slug derived from the dataset name.",
    )
    parser.add_argument("--repository-url", type=str, default=None, help="Optional repository URL.")
    parser.add_argument("--commit-sha", type=str, default=None, help="Optional commit SHA.")
    parser.add_argument(
        "--label-schema-version",
        type=str,
        default="pancreatic-signal-eval-v1",
        help="Label schema version string for the generated submission draft.",
    )
    parser.add_argument("--threshold", type=float, default=0.2, help="Flagging threshold between 0 and 1.")
    parser.add_argument("--top-k", type=int, default=25, help="Top-k queue depth to analyze.")
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
        help="Directory that will receive the JSON, Markdown, and submission artifacts.",
    )
    parser.add_argument(
        "--basename",
        type=str,
        default="external-benchmark",
        help="Base filename for the written artifacts.",
    )
    parser.add_argument(
        "--deidentified",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether the evaluated dataset is de-identified.",
    )
    parser.add_argument(
        "--strength",
        action="append",
        default=[],
        help="Repeatable notable strength string for the generated submission draft.",
    )
    parser.add_argument(
        "--limitation",
        action="append",
        default=[],
        help="Repeatable known limitation string for the generated submission draft.",
    )
    parser.add_argument("--notes", type=str, default=None, help="Optional submission note.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    labels_path = _resolve_input_path(args.labels)
    predictions_path = _resolve_input_path(args.predictions)
    out_dir = args.out_dir if args.out_dir.is_absolute() else (ROOT / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset_name = args.dataset_name or labels_path.stem.replace("_", "-")
    submission_name = args.submission_name or f"external-{_slugify(dataset_name)}"
    thresholds = [float(item.strip()) for item in args.thresholds.split(",") if item.strip()] or None

    summary = evaluate_external_dataset(
        labels_path=labels_path,
        predictions_path=predictions_path,
        threshold=args.threshold,
        top_k=args.top_k,
    )
    sweep = sweep_external_thresholds(
        labels_path=labels_path,
        predictions_path=predictions_path,
        top_k=args.top_k,
        thresholds=thresholds,
    )

    json_path = out_dir / f"{args.basename}.json"
    markdown_path = out_dir / f"{args.basename}.md"
    submission_path = out_dir / f"{args.basename}-submission.json"
    artifact_paths = [_display_path(json_path), _display_path(markdown_path)]

    submission = BenchmarkSubmission.model_validate(
        {
            "submission_version": "1.0",
            "submission_name": submission_name,
            "project_name": args.project_name,
            "repository_url": args.repository_url,
            "commit_sha": args.commit_sha,
            "dataset_name": dataset_name,
            "dataset_split": args.dataset_split,
            "report_count": summary.processed,
            "deidentified": args.deidentified,
            "label_schema_version": args.label_schema_version,
            "score_mode": "external",
            "threshold": summary.threshold,
            "top_k": summary.top_k,
            "evaluation_command": _render_command(
                labels_path=labels_path,
                predictions_path=predictions_path,
                threshold=args.threshold,
                top_k=args.top_k,
                out_dir=out_dir,
                basename=args.basename,
                dataset_name=args.dataset_name,
                dataset_split=args.dataset_split,
                project_name=args.project_name,
                repository_url=args.repository_url,
                commit_sha=args.commit_sha,
                strengths=args.strength,
                limitations=args.limitation,
                notes=args.notes,
                deidentified=args.deidentified,
            ),
            "artifact_paths": artifact_paths,
            "metrics": {
                "processed": summary.processed,
                "positives": summary.positives,
                "flagged": summary.flagged,
                "true_positives": summary.true_positives,
                "false_positives": summary.false_positives,
                "true_negatives": summary.true_negatives,
                "false_negatives": summary.false_negatives,
                "precision": summary.precision,
                "recall": summary.recall,
                "f1": summary.f1,
                "precision_at_top_k": summary.precision_at_top_k,
                "sensitivity_at_top_k": summary.sensitivity_at_top_k,
                "reviewer_yield_at_top_k": summary.reviewer_yield_at_top_k,
                "false_negative_buckets": summary.false_negative_buckets,
            },
            "notable_strengths": args.strength or ["Replace with a dataset-specific strength before public submission."],
            "known_limitations": args.limitation
            or ["Replace with a dataset-specific limitation before public submission."],
            "notes": args.notes
            or (
                "Generated draft from scripts/run_external_eval.py. Replace placeholder strengths and "
                "limitations before public submission if you did not pass them explicitly."
            ),
        }
    )

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "dataset": {
            "dataset_name": dataset_name,
            "dataset_split": args.dataset_split,
            "deidentified": args.deidentified,
            "label_schema_version": args.label_schema_version,
            "labels_path": _display_path(labels_path),
            "predictions_path": _display_path(predictions_path),
        },
        "dataset_summary": build_dataset_summary(summary),
        "queue_preview": build_queue_preview(summary),
        "evaluation": summary.model_dump(mode="json"),
        "sweep": sweep.model_dump(mode="json"),
        "casebook": build_casebook(summary),
        "submission": submission.model_dump(mode="json"),
    }

    json_path.write_text(json.dumps(snapshot, indent=2) + "\n")
    markdown_path.write_text(render_markdown(snapshot, submission_path))
    submission_path.write_text(json.dumps(submission.model_dump(mode="json"), indent=2) + "\n")

    print(f"Wrote {_display_path(json_path)}")
    print(f"Wrote {_display_path(markdown_path)}")
    print(f"Wrote {_display_path(submission_path)}")
    print(
        f"External evaluation: precision {summary.precision:.4f} | recall {summary.recall:.4f} | "
        f"F1 {summary.f1:.4f} | flagged {summary.flagged}"
    )


def render_markdown(snapshot: dict[str, object], submission_path: Path) -> str:
    dataset = snapshot["dataset"]
    dataset_summary = snapshot["dataset_summary"]
    queue_preview = snapshot["queue_preview"]
    summary = snapshot["evaluation"]
    sweep = snapshot["sweep"]
    casebook = snapshot["casebook"]
    submission = snapshot["submission"]
    top_flagged = [case["case_id"] for case in summary["cases"] if case["flagged"]][: min(summary["top_k"], 5)]
    missed = [case["case_id"] for case in summary["cases"] if case["expected_positive"] and not case["flagged"]]

    lines = [
        "# External Benchmark Snapshot",
        "",
        f"- Generated at: {snapshot['generated_at']}",
        f"- Dataset: {dataset['dataset_name']} ({dataset['dataset_split']})",
        f"- De-identified: {dataset['deidentified']}",
        f"- Labels: `{dataset['labels_path']}`",
        f"- Predictions: `{dataset['predictions_path']}`",
        f"- Threshold: {summary['threshold']:.2f}",
        f"- Top-k: {summary['top_k']}",
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
            "## Summary",
            "",
            "| Mode | Precision | Recall | F1 | Flagged | Top-k Precision | Top-k Sensitivity |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            (
                f"| External | {summary['precision']:.4f} | {summary['recall']:.4f} | {summary['f1']:.4f} | "
                f"{summary['flagged']} | {summary['precision_at_top_k']:.4f} | {summary['sensitivity_at_top_k']:.4f} |"
            ),
            "",
            f"- Positives: {summary['positives']} of {summary['processed']}",
            f"- Reviewer yield at top-{summary['top_k']}: {summary['reviewer_yield_at_top_k']:.4f}",
            f"- Top flagged case IDs: {', '.join(top_flagged) if top_flagged else 'none'}",
            f"- Missed positive case IDs: {', '.join(missed) if missed else 'none'}",
            f"- False negative buckets: {format_false_negative_buckets(summary['false_negative_buckets'])}",
            "",
            "## Top-k Queue Preview",
            "",
            f"- External top-{queue_preview['top_k']}: {format_queue(queue_preview['external'])}",
            "",
            "## Threshold Sweep",
            "",
            "| Threshold | Precision | Recall | F1 | Flagged | Top-k Precision | Top-k Sensitivity |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for point in sweep["points"]:
        lines.append(
            "| "
            f"{point['threshold']:.2f} | "
            f"{point['precision']:.4f} | "
            f"{point['recall']:.4f} | "
            f"{point['f1']:.4f} | "
            f"{point['flagged']} | "
            f"{point['precision_at_top_k']:.4f} | "
            f"{point['sensitivity_at_top_k']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Recommended Operating Point",
            "",
            (
                f"- External: threshold {sweep['recommendation']['recommended_threshold']:.2f}, "
                f"F1 {sweep['recommendation']['f1']:.4f}, "
                f"recall {sweep['recommendation']['recall']:.4f}, "
                f"flagged {sweep['recommendation']['flagged']}"
            ),
            f"- Rationale: {sweep['recommendation']['rationale']}",
            "",
            "## Submission Draft",
            "",
            f"- Submission name: `{submission['submission_name']}`",
            f"- Project: {submission['project_name']}",
            f"- Submission JSON: `{_display_path(submission_path)}`",
            f"- Artifact paths: {', '.join(submission['artifact_paths']) or 'none'}",
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
                *([f"- Report excerpt: {entry['report_excerpt']}"] if entry.get("report_excerpt") else []),
                f"- Reviewer focus: {entry['reviewer_focus'] or 'No reviewer cue recorded.'}",
                f"- Label note: {entry['label_notes'] or 'No label note recorded.'}",
                (
                    f"- Expected positive: `{entry['expected_positive']}` | "
                    f"Expected escalation: `{entry['expected_escalation']}`"
                ),
                f"- Expected rationale cues: {format_code_list(entry['expected_rationale_codes'])}",
                (
                    f"- External: {entry['external']['outcome']} at {entry['external']['score']:.4f} "
                    f"with rationale cues {format_code_list(entry['external']['rationale_codes'])}"
                ),
                f"- Reviewed false-negative bucket: {entry['external']['false_negative_bucket'] or 'none recorded'}",
                "",
            ]
        )
    return "\n".join(lines)


def format_false_negative_buckets(buckets: dict[str, int]) -> str:
    if not buckets:
        return "none recorded"
    return ", ".join(f"{bucket}={count}" for bucket, count in sorted(buckets.items()))


def build_dataset_summary(summary) -> dict[str, object]:
    bucket_counts: dict[str, dict[str, int | str]] = {}

    for case in summary.cases:
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
        "report_count": len(summary.cases),
        "positive_count": sum(1 for case in summary.cases if case.expected_positive),
        "escalation_count": sum(1 for case in summary.cases if case.expected_escalation),
        "bucket_counts": sorted(bucket_counts.values(), key=lambda item: str(item["bucket"])),
    }


def build_queue_preview(summary) -> dict[str, object]:
    return {
        "top_k": summary.top_k,
        "external": [build_queue_entry(case) for case in summary.cases[: summary.top_k]],
    }


def build_queue_entry(case) -> dict[str, object]:
    return {
        "case_id": case.case_id,
        "report_id": case.report_id,
        "benchmark_bucket": case.benchmark_bucket,
        "score": round(case.score, 4),
        "outcome": classify_outcome(case),
    }


def build_casebook(summary) -> list[dict[str, object]]:
    casebook: list[dict[str, object]] = []
    for case in sorted(summary.cases, key=lambda item: item.case_id):
        casebook.append(
            {
                "case_id": case.case_id,
                "report_id": case.report_id,
                "report_excerpt": case.report_excerpt,
                "benchmark_bucket": case.benchmark_bucket,
                "reviewer_focus": case.reviewer_focus,
                "label_notes": case.label_notes,
                "expected_positive": case.expected_positive,
                "expected_escalation": case.expected_escalation,
                "expected_rationale_codes": case.expected_rationale_codes,
                "external": summarize_case_mode(case),
            }
        )
    return casebook


def summarize_case_mode(case) -> dict[str, object]:
    return {
        "score": round(case.score, 4),
        "flagged": case.flagged,
        "outcome": classify_outcome(case),
        "rationale_codes": case.rationale_codes,
        "false_negative_bucket": case.false_negative_bucket,
    }


def classify_outcome(case) -> str:
    if case.flagged and case.expected_positive:
        return "true_positive"
    if case.flagged and not case.expected_positive:
        return "false_positive"
    if not case.flagged and case.expected_positive:
        return "missed_positive"
    return "true_negative"


def format_queue(entries: list[dict[str, object]]) -> str:
    if not entries:
        return "none"
    return " -> ".join(
        (
            f"{entry['case_id']} ({entry['benchmark_bucket'] or 'unbucketed'}, "
            f"{entry['outcome']}, {entry['score']:.4f})"
        )
        for entry in entries
    )


def format_code_list(codes: list[str]) -> str:
    return ", ".join(codes) if codes else "none"


def _resolve_input_path(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _render_command(
    *,
    labels_path: Path,
    predictions_path: Path,
    threshold: float,
    top_k: int,
    out_dir: Path,
    basename: str,
    dataset_name: str,
    dataset_split: str,
    project_name: str,
    repository_url: str | None,
    commit_sha: str | None,
    strengths: list[str],
    limitations: list[str],
    notes: str | None,
    deidentified: bool,
) -> str:
    parts = [
        "python scripts/run_external_eval.py",
        f"--labels {_shell_quote(_display_path(labels_path))}",
        f"--predictions {_shell_quote(_display_path(predictions_path))}",
        f"--threshold {threshold:.2f}",
        f"--top-k {top_k}",
        f"--out-dir {_shell_quote(_display_path(out_dir))}",
        f"--basename {_shell_quote(basename)}",
    ]
    if dataset_name:
        parts.append(f"--dataset-name {_shell_quote(dataset_name)}")
    if dataset_split:
        parts.append(f"--dataset-split {_shell_quote(dataset_split)}")
    if project_name:
        parts.append(f"--project-name {_shell_quote(project_name)}")
    if repository_url:
        parts.append(f"--repository-url {_shell_quote(repository_url)}")
    if commit_sha:
        parts.append(f"--commit-sha {_shell_quote(commit_sha)}")
    if not deidentified:
        parts.append("--no-deidentified")
    for strength in strengths:
        parts.append(f"--strength {_shell_quote(strength)}")
    for limitation in limitations:
        parts.append(f"--limitation {_shell_quote(limitation)}")
    if notes:
        parts.append(f"--notes {_shell_quote(notes)}")
    return " ".join(parts)


def _shell_quote(value: str) -> str:
    if not value or any(char.isspace() or char in {'"', "'"} for char in value):
        return json.dumps(value)
    return value


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return normalized.strip("-") or "external-benchmark"


if __name__ == "__main__":
    main()
