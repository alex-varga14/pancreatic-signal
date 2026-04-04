import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.research_intel import list_research_opportunities, run_research_opportunity_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a safe experiment for a benchmark or rule research-intel opportunity."
    )
    parser.add_argument(
        "--actor-user-id",
        default="research-intel-cli",
        help="Actor id recorded on the experiment run.",
    )
    parser.add_argument(
        "--opportunity-id",
        default="",
        help="Specific opportunity id to evaluate. Defaults to the highest-confidence supported opportunity.",
    )
    parser.add_argument(
        "--no-artifacts",
        action="store_true",
        help="Skip writing JSON and Markdown artifacts.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the run detail as JSON.")
    return parser.parse_args()


def _pick_supported_opportunity() -> str:
    opportunities = list_research_opportunities()
    supported = [
        item
        for item in opportunities
        if item.opportunity_type in {"benchmark_gap", "rule_gap"}
    ]
    supported.sort(key=lambda item: (-item.confidence_score, item.opportunity_id))
    if not supported:
        raise SystemExit("No benchmark or rule opportunity is available for experimentation.")
    return supported[0].opportunity_id


def main() -> None:
    args = parse_args()
    opportunity_id = args.opportunity_id.strip() or _pick_supported_opportunity()
    run = run_research_opportunity_experiment(
        opportunity_id=opportunity_id,
        actor_user_id=args.actor_user_id,
        write_artifacts=not args.no_artifacts,
    )
    if run is None:
        raise SystemExit(f"Opportunity {opportunity_id} was not found.")

    if args.json:
        print(json.dumps(run.model_dump(mode="json"), indent=2))
        return

    print(
        f"Research experiment run {run.run_id} completed: "
        f"processed={run.processed} created={run.created} updated={run.updated} failed={run.failed}"
    )
    print(f"Opportunity: {opportunity_id}")
    if run.artifact_paths:
        print("Artifacts:")
        for path in run.artifact_paths:
            print(f"  - {path}")


if __name__ == "__main__":
    main()
