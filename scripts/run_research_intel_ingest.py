import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.research_intel import run_research_ingest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the pancreatic research-intel discovery ingest workflow."
    )
    parser.add_argument(
        "--actor-user-id",
        default="research-intel-cli",
        help="Actor id recorded on the ingest run.",
    )
    parser.add_argument(
        "--source-ids",
        default="",
        help="Optional comma-separated source ids to ingest.",
    )
    parser.add_argument(
        "--include-disabled",
        action="store_true",
        help="Include disabled source definitions from the catalog.",
    )
    parser.add_argument(
        "--only-due",
        action="store_true",
        help="Run only sources that are currently due according to the watchtower schedule.",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "seeded", "fixture", "live"],
        default="auto",
        help="Choose how documents are collected before normalization.",
    )
    parser.add_argument(
        "--max-documents-per-source",
        type=int,
        default=None,
        help="Optional cap on collected documents per source.",
    )
    parser.add_argument(
        "--no-artifacts",
        action="store_true",
        help="Skip writing JSON and Markdown artifacts.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the run detail as JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run = run_research_ingest(
        actor_user_id=args.actor_user_id,
        source_ids=[item.strip() for item in args.source_ids.split(",") if item.strip()] or None,
        include_disabled=args.include_disabled,
        only_due=args.only_due,
        write_artifacts=not args.no_artifacts,
        mode=args.mode,
        max_documents_per_source=args.max_documents_per_source,
    )

    if args.json:
        print(json.dumps(run.model_dump(mode="json"), indent=2))
        return

    print(
        f"Research ingest run {run.run_id} completed: "
        f"processed={run.processed} created={run.created} updated={run.updated} failed={run.failed}"
    )
    if run.source_scope:
        print(f"Sources: {', '.join(run.source_scope)}")
    if run.metadata.get("skipped_source_ids"):
        skipped = run.metadata["skipped_source_ids"]
        if isinstance(skipped, list) and skipped:
            print(f"Skipped: {', '.join(str(item) for item in skipped)}")
    if run.artifact_paths:
        print("Artifacts:")
        for path in run.artifact_paths:
            print(f"  - {path}")


if __name__ == "__main__":
    main()
