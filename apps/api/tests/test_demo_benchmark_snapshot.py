import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts" / "write_demo_benchmark.py"


def test_write_demo_benchmark_writes_casebook_snapshot(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--out-dir",
            str(tmp_path),
            "--basename",
            "demo-benchmark-casebook",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )

    json_path = tmp_path / "demo-benchmark-casebook.json"
    markdown_path = tmp_path / "demo-benchmark-casebook.md"

    assert "Wrote" in result.stdout
    assert json_path.exists()
    assert markdown_path.exists()

    snapshot = json.loads(json_path.read_text())
    casebook_by_id = {entry["case_id"]: entry for entry in snapshot["casebook"]}
    bucket_by_name = {
        bucket["bucket"]: bucket
        for bucket in snapshot["dataset_summary"]["bucket_counts"]
    }

    assert snapshot["dataset_summary"]["report_count"] == 10
    assert snapshot["dataset_summary"]["positive_count"] == 7
    assert snapshot["dataset_summary"]["escalation_count"] == 5
    assert snapshot["queue_preview"]["top_k"] == snapshot["comparison"]["top_k"]
    assert bucket_by_name["follow-up only"]["case_count"] == 2
    assert casebook_by_id["C-005"]["benchmark_bucket"] == "follow-up only"
    assert "FOLLOWUP_RECOMMENDED" in casebook_by_id["C-005"]["expected_rationale_codes"]
    assert casebook_by_id["C-005"]["rules"]["outcome"] == "missed_positive"
    assert casebook_by_id["C-005"]["hybrid"]["outcome"] == "true_positive"
    assert casebook_by_id["C-008"]["rules"]["outcome"] == "missed_positive"
    assert casebook_by_id["C-008"]["hybrid"]["outcome"] == "true_positive"
    assert casebook_by_id["C-009"]["hybrid"]["outcome"] == "true_negative"
    assert casebook_by_id["C-003"]["reviewer_focus"].startswith("Treat double duct sign")

    markdown = markdown_path.read_text()
    assert "## Dataset Coverage" in markdown
    assert "## Top-k Queue Preview" in markdown
    assert "## Reviewer Casebook" in markdown
    assert "### C-005 — follow-up only" in markdown
    assert "### C-008 — follow-up only" in markdown
