"""Autoresearch loop orchestrator.

This script does **not** itself rewrite ``pancreatic_signal_rules.json``. It
calls an external coding agent CLI (Cursor, Claude Code, Codex, etc.) and asks
it to write a candidate ontology to a fresh run directory, then hands the
candidate to ``scripts/run_autoresearch_experiment.py``.

It also exposes ``--promote`` and ``--rollback`` modes for the Makefile
targets ``autoresearch-promote`` and ``autoresearch-rollback``. These actions
are intentionally human-gated: the loop never promotes a candidate by itself.

Usage:

    # Iterate the agent loop N times.
    python scripts/run_autoresearch_loop.py --iterations 3 \
        --agent-cmd "cursor agent --prompt-file autoresearch/program.md ..."

    # Promote a kept run into the live ontology.
    python scripts/run_autoresearch_loop.py --promote 2026-04-25T14-22-09Z

    # Restore the frozen baseline.
    python scripts/run_autoresearch_loop.py --rollback
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_PATH = ROOT / "data" / "ontologies" / "pancreatic_signal_rules.json"
BASELINE_ONTOLOGY_PATH = ROOT / "autoresearch" / "baseline" / "pancreatic_signal_rules.json"
RUNS_DIR = ROOT / "autoresearch" / "runs"
PROGRAM_MD = ROOT / "autoresearch" / "program.md"
EXPERIMENT_SCRIPT = ROOT / "scripts" / "run_autoresearch_experiment.py"
AUDIT_LOG = ROOT / "autoresearch" / "promotion_audit.jsonl"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_slug() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H-%M-%SZ")


def _ensure_baseline() -> None:
    if BASELINE_ONTOLOGY_PATH.exists():
        return
    BASELINE_ONTOLOGY_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ONTOLOGY_PATH, BASELINE_ONTOLOGY_PATH)
    print(f"[autoresearch] seeded baseline at {BASELINE_ONTOLOGY_PATH}")


def _read_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _append_audit(entry: dict[str, Any]) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def _resolve_run_dir(run_id: str) -> Path:
    candidate = (RUNS_DIR / run_id).resolve()
    if not candidate.exists() or not candidate.is_dir():
        raise SystemExit(f"error: run directory {run_id} not found under {RUNS_DIR}")
    if RUNS_DIR.resolve() not in candidate.parents:
        raise SystemExit(f"error: run directory {run_id} escapes {RUNS_DIR}")
    return candidate


def _invoke_agent(agent_cmd: str, run_dir: Path) -> int:
    """Invoke the configured coding agent CLI to produce a candidate.

    The agent receives three environment variables describing where to write
    its outputs:

    - ``AUTORESEARCH_OUT_ONTOLOGY``: path to ``proposal.json``
    - ``AUTORESEARCH_OUT_NOTES``: path to ``notes.md``
    - ``AUTORESEARCH_OUT_META``: path to ``proposal_meta.json`` (optional)
    - ``AUTORESEARCH_PROGRAM_MD``: path to the research org instructions
    - ``AUTORESEARCH_BASELINE``: path to the frozen baseline ontology
    - ``AUTORESEARCH_RUNS_DIR``: path to the parent runs directory

    Returns the agent CLI exit code.
    """

    env = os.environ.copy()
    env["AUTORESEARCH_OUT_ONTOLOGY"] = str(run_dir / "proposal.json")
    env["AUTORESEARCH_OUT_NOTES"] = str(run_dir / "notes.md")
    env["AUTORESEARCH_OUT_META"] = str(run_dir / "proposal_meta.json")
    env["AUTORESEARCH_PROGRAM_MD"] = str(PROGRAM_MD)
    env["AUTORESEARCH_BASELINE"] = str(BASELINE_ONTOLOGY_PATH)
    env["AUTORESEARCH_RUNS_DIR"] = str(RUNS_DIR)

    print(f"[autoresearch] invoking agent: {agent_cmd}")
    result = subprocess.run(shlex.split(agent_cmd), env=env, cwd=str(ROOT))
    return result.returncode


def _run_experiment(candidate_path: Path, run_dir: Path, *, skip_determinism: bool) -> int:
    cmd = [
        sys.executable,
        str(EXPERIMENT_SCRIPT),
        "--candidate",
        str(candidate_path),
        "--run-dir",
        str(run_dir),
        "--baseline",
        str(BASELINE_ONTOLOGY_PATH),
    ]
    if (run_dir / "proposal_meta.json").exists():
        cmd.extend(["--proposal-meta", str(run_dir / "proposal_meta.json")])
    if (run_dir / "notes.md").exists():
        cmd.extend(["--notes", str(run_dir / "notes.md")])
    if skip_determinism:
        cmd.append("--skip-determinism")
    print(f"[autoresearch] running experiment: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def _action_loop(args: argparse.Namespace) -> int:
    _ensure_baseline()

    if not args.agent_cmd:
        # No agent: run a single experiment against the current ontology
        # for human-driven manual edits (make autoresearch-once).
        run_dir = RUNS_DIR / _utc_now_slug()
        run_dir.mkdir(parents=True, exist_ok=True)
        candidate_copy = run_dir / "proposal.json"
        shutil.copyfile(ONTOLOGY_PATH, candidate_copy)
        if args.notes:
            (run_dir / "notes.md").write_text(args.notes + "\n")
        return _run_experiment(candidate_copy, run_dir, skip_determinism=False)

    overall_rc = 0
    for iteration in range(1, args.iterations + 1):
        run_dir = RUNS_DIR / _utc_now_slug()
        run_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n[autoresearch] === iteration {iteration}/{args.iterations} -> {run_dir.name} ===")

        agent_rc = _invoke_agent(args.agent_cmd, run_dir)
        if agent_rc != 0:
            decision = {
                "status": "agent_failed",
                "primary_metric": "f1_at_top_k_demo_rules",
                "primary_value": None,
                "baseline_value": None,
                "delta": None,
                "reasons": [f"agent_exit_code: {agent_rc}"],
                "run_dir": str(run_dir.relative_to(ROOT)),
            }
            _write_json(run_dir / "decision.json", decision)
            print(f"[autoresearch] agent exited with {agent_rc}; recorded as agent_failed")
            overall_rc = agent_rc
            continue

        candidate_path = run_dir / "proposal.json"
        if not candidate_path.exists():
            decision = {
                "status": "agent_failed",
                "primary_metric": "f1_at_top_k_demo_rules",
                "primary_value": None,
                "baseline_value": None,
                "delta": None,
                "reasons": ["agent_no_proposal: agent CLI exited 0 but did not write proposal.json"],
                "run_dir": str(run_dir.relative_to(ROOT)),
            }
            _write_json(run_dir / "decision.json", decision)
            print("[autoresearch] agent did not write proposal.json; skipping")
            overall_rc = 1
            continue

        rc = _run_experiment(candidate_path, run_dir, skip_determinism=False)
        if rc not in (0, 1):
            print(f"[autoresearch] experiment driver crashed with rc={rc}")
            overall_rc = rc

    return overall_rc


def _action_promote(run_id: str) -> int:
    _ensure_baseline()
    run_dir = _resolve_run_dir(run_id)
    decision_path = run_dir / "decision.json"
    candidate_path = run_dir / "proposal.json"
    if not decision_path.exists() or not candidate_path.exists():
        print(f"error: {run_id} is missing decision.json or proposal.json", file=sys.stderr)
        return 2
    decision = _read_json(decision_path)
    if decision.get("status") != "kept":
        print(
            f"error: refusing to promote {run_id} (status={decision.get('status')}); "
            "only kept runs can be promoted",
            file=sys.stderr,
        )
        return 2

    backup = ONTOLOGY_PATH.read_text()
    pre_promotion_path = run_dir / "pre_promotion_ontology.json"
    pre_promotion_path.write_text(backup)

    shutil.copyfile(candidate_path, ONTOLOGY_PATH)
    promotion_record = {
        "run_id": run_id,
        "promoted_at": _utc_now().isoformat(),
        "decision": decision,
        "ontology_target": str(ONTOLOGY_PATH.relative_to(ROOT)),
        "pre_promotion_snapshot": str(pre_promotion_path.relative_to(ROOT)),
    }
    _write_json(run_dir / "promotion.json", promotion_record)
    _append_audit({"action": "promote", **promotion_record})
    print(f"[autoresearch] promoted {run_id} into {ONTOLOGY_PATH.relative_to(ROOT)}")
    return 0


def _action_rollback() -> int:
    if not BASELINE_ONTOLOGY_PATH.exists():
        print("error: no frozen baseline at autoresearch/baseline/", file=sys.stderr)
        return 2
    backup = ONTOLOGY_PATH.read_text() if ONTOLOGY_PATH.exists() else ""
    shutil.copyfile(BASELINE_ONTOLOGY_PATH, ONTOLOGY_PATH)
    record = {
        "action": "rollback",
        "rolled_back_at": _utc_now().isoformat(),
        "previous_ontology_sha_first_64": backup[:64],
        "ontology_target": str(ONTOLOGY_PATH.relative_to(ROOT)),
    }
    _append_audit(record)
    print(f"[autoresearch] restored baseline ontology into {ONTOLOGY_PATH.relative_to(ROOT)}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Autoresearch loop orchestrator")
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of iterations to run when invoking an agent.",
    )
    parser.add_argument(
        "--agent-cmd",
        type=str,
        default=os.environ.get("AUTORESEARCH_AGENT_CMD", ""),
        help="Shell command to run for the coding agent. If empty, performs a "
        "single manual experiment against the current production ontology.",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Optional notes string to copy into the run directory when running "
        "the manual (no-agent) experiment.",
    )
    parser.add_argument(
        "--promote",
        type=str,
        default="",
        help="Promote the run with this id into the live ontology and exit.",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Restore the frozen baseline ontology and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.rollback:
        return _action_rollback()
    if args.promote:
        return _action_promote(args.promote)
    return _action_loop(args)


if __name__ == "__main__":
    raise SystemExit(main())
