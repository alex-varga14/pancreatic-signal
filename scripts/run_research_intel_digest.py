import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.research_intel import run_research_digest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a pancreatic research-intel digest from the current document store."
    )
    parser.add_argument(
        "--actor-user-id",
        default="research-intel-cli",
        help="Actor id recorded on the digest run.",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Generate the digest as a draft instead of published.",
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
    run = run_research_digest(
        actor_user_id=args.actor_user_id,
        publish=not args.draft,
        write_artifacts=not args.no_artifacts,
    )

    if args.json:
        print(json.dumps(run.model_dump(mode="json"), indent=2))
        return

    print(
        f"Research digest run {run.run_id} completed: "
        f"processed={run.processed} created={run.created} updated={run.updated} failed={run.failed}"
    )
    if run.artifact_paths:
        print("Artifacts:")
        for path in run.artifact_paths:
            print(f"  - {path}")


if __name__ == "__main__":
    main()
