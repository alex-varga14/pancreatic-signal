import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.research_intel import list_research_schedule


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show the pancreatic research-intel watchtower schedule snapshot."
    )
    parser.add_argument("--json", action="store_true", help="Emit the schedule snapshot as JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot = list_research_schedule()

    if args.json:
        print(json.dumps(snapshot.model_dump(mode="json"), indent=2))
        return

    print(
        f"Research schedule snapshot: due={snapshot.due_count} scheduled={snapshot.scheduled_count} "
        f"live-ready={snapshot.live_ready_count} total={snapshot.total_sources}"
    )
    for source in snapshot.sources:
        print(
            f"- {source.source_id}: {source.schedule_state} • "
            f"{source.schedule_summary or 'manual'} • "
            f"next {source.next_run_at.isoformat() if source.next_run_at else 'now'}"
        )


if __name__ == "__main__":
    main()
