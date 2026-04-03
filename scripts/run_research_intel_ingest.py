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
        description="Run the seeded pancreatic research-intel ingest workflow."
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
        write_artifacts=not args.no_artifacts,
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
    if run.artifact_paths:
        print("Artifacts:")
        for path in run.artifact_paths:
            print(f"  - {path}")


if __name__ == "__main__":
    main()
