import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

try:
    from app.schemas.benchmark_submission import BenchmarkSubmission
except ModuleNotFoundError as exc:  # pragma: no cover - import guard for unprepared environments
    raise SystemExit(
        "Missing API dependencies. Activate apps/api/.venv or run "
        "`make validate-benchmark-submission SUBMISSION=...`."
    ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an external benchmark submission against the Pancreatic Signal public benchmark schema."
    )
    parser.add_argument("submission", type=Path, help="Path to a benchmark submission JSON file.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    submission_path = args.submission if args.submission.is_absolute() else (ROOT / args.submission).resolve()
    payload = json.loads(submission_path.read_text())
    submission = BenchmarkSubmission.model_validate(payload)

    print(f"Validated submission: {submission.submission_name}")
    print(f"Project: {submission.project_name}")
    print(f"Dataset: {submission.dataset_name} ({submission.report_count} reports)")
    print(
        f"Mode: {submission.score_mode} | threshold {submission.threshold:.2f} | top-k {submission.top_k}"
    )
    print(
        f"Precision {submission.metrics.precision:.4f} | "
        f"Recall {submission.metrics.recall:.4f} | "
        f"F1 {submission.metrics.f1:.4f}"
    )
    print(
        f"Top-k precision {submission.metrics.precision_at_top_k:.4f} | "
        f"Sensitivity {submission.metrics.sensitivity_at_top_k:.4f}"
    )


if __name__ == "__main__":
    main()
