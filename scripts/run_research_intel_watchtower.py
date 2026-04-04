import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.research_intel import run_research_watchtower


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one pancreatic research-intel watchtower automation tick."
    )
    parser.add_argument(
        "--actor-user-id",
        default="research-intel-watchtower",
        help="Actor id recorded on the watchtower run.",
    )
    parser.add_argument(
        "--source-ids",
        default="",
        help="Optional comma-separated source ids to include in this tick.",
    )
    parser.add_argument(
        "--include-disabled",
        action="store_true",
        help="Include disabled source definitions from the catalog.",
    )
    parser.add_argument(
        "--all-sources",
        action="store_true",
        help="Ignore due-only scheduling and run the requested source scope immediately.",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "seeded", "fixture", "live"],
        default="auto",
        help="Choose how source documents are collected before normalization.",
    )
    parser.add_argument(
        "--max-documents-per-source",
        type=int,
        default=None,
        help="Optional cap on collected documents per source.",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Generate any triggered digest as a draft instead of published.",
    )
    parser.add_argument(
        "--digest-policy",
        choices=["new_documents", "always", "never"],
        default="new_documents",
        help="Decide when the watchtower should generate a digest after ingest.",
    )
    parser.add_argument(
        "--no-artifacts",
        action="store_true",
        help="Skip writing JSON and Markdown artifacts for the watchtower and child runs.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the watchtower run detail as JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run = run_research_watchtower(
        actor_user_id=args.actor_user_id,
        source_ids=[item.strip() for item in args.source_ids.split(",") if item.strip()] or None,
        include_disabled=args.include_disabled,
        only_due=not args.all_sources,
        write_artifacts=not args.no_artifacts,
        mode=args.mode,
        max_documents_per_source=args.max_documents_per_source,
        publish_digest=not args.draft,
        digest_policy=args.digest_policy,
    )

    if args.json:
        print(json.dumps(run.model_dump(mode="json"), indent=2))
        return

    ingest_decision = run.metadata.get("ingest_decision") or {}
    digest_decision = run.metadata.get("digest_decision") or {}
    print(
        f"Research watchtower run {run.run_id} completed: "
        f"processed={run.processed} created={run.created} updated={run.updated} failed={run.failed}"
    )
    print(
        f"Ingest: triggered={ingest_decision.get('triggered', False)} "
        f"reason={ingest_decision.get('reason', 'unknown')}"
    )
    print(
        f"Digest: triggered={digest_decision.get('triggered', False)} "
        f"reason={digest_decision.get('reason', 'unknown')}"
    )
    if run.source_scope:
        print(f"Sources: {', '.join(run.source_scope)}")
    if run.artifact_paths:
        print("Artifacts:")
        for path in run.artifact_paths:
            print(f"  - {path}")


if __name__ == "__main__":
    main()
