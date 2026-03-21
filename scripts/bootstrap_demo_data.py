import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
reports_path = ROOT / "data" / "examples" / "reports.jsonl"
API_ROOT = ROOT / "apps" / "api"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.schemas.triage import ReportInput
from app.services.triage_engine import triage_report
from app.store.memory_store import CASE_STORE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load demo reports into the local persistence store.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear existing persisted cases before loading the demo dataset.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.reset:
        CASE_STORE.reset()

    count = 0
    flagged = 0
    with reports_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            payload = ReportInput(**json.loads(line))
            result = triage_report(payload)
            count += 1
            if result.score >= 0.30:
                flagged += 1

    print(
        f"Loaded {count} demo reports into {reports_path.name}; "
        f"{flagged} case(s) met the default flagged threshold."
    )


if __name__ == "__main__":
    main()
