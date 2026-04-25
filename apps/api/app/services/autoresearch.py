"""Read-only access layer over ``autoresearch/runs/``.

This service is what the FastAPI routes (``apps/api/app/api/routes/autoresearch.py``)
sit on top of. It never writes to the run log; it only reads structured
artifacts produced by ``scripts/run_autoresearch_experiment.py``. Promotion
mutates ``data/ontologies/pancreatic_signal_rules.json`` and writes a
``promotion.json`` provenance record into the run directory.

The module deliberately avoids depending on the orchestrator script so it can
be unit-tested in isolation: it only needs the run directory layout described
in ``autoresearch/runs/README.md``.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.paths import resolve_data_root
from app.schemas.autoresearch import (
    AutoresearchLeaderboard,
    AutoresearchPromotionResult,
    AutoresearchRunDetail,
    AutoresearchRunSummary,
)
from app.services import ontology as ontology_module


def _project_root() -> Path:
    """Return the repository root.

    ``resolve_data_root()`` returns the ``data/`` directory; the autoresearch
    runtime layout lives one level up at ``<repo>/autoresearch/``.
    """

    return resolve_data_root().parent


def _runs_dir() -> Path:
    return _project_root() / "autoresearch" / "runs"


def _baseline_path() -> Path:
    return _project_root() / "autoresearch" / "baseline" / "pancreatic_signal_rules.json"


def _ontology_path() -> Path:
    return ontology_module.ONTOLOGY_PATH


def _audit_log_path() -> Path:
    return _project_root() / "autoresearch" / "promotion_audit.jsonl"


def _read_json_if_exists(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        with path.open() as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return None


def _read_text_if_exists(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text()
    except OSError:
        return None


def _summarize_notes(notes_text: str | None) -> str | None:
    if not notes_text:
        return None
    for raw_line in notes_text.splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            return line[:240]
    return None


def _summary_from_run_dir(run_dir: Path) -> AutoresearchRunSummary | None:
    decision = _read_json_if_exists(run_dir / "decision.json")
    if not decision:
        return None
    promotion = _read_json_if_exists(run_dir / "promotion.json")
    notes_summary = _summarize_notes(_read_text_if_exists(run_dir / "notes.md"))

    try:
        created_at_dt = datetime.fromtimestamp(
            (run_dir / "decision.json").stat().st_mtime, tz=timezone.utc
        )
        created_at = created_at_dt.isoformat()
    except OSError:
        created_at = None

    return AutoresearchRunSummary(
        run_id=run_dir.name,
        created_at=created_at,
        status=str(decision.get("status", "unknown")),
        primary_metric=str(decision.get("primary_metric", "f1_at_top_k_demo_rules")),
        primary_value=decision.get("primary_value"),
        baseline_value=decision.get("baseline_value"),
        delta=decision.get("delta"),
        notes_summary=notes_summary,
        has_proposal=(run_dir / "proposal.json").exists(),
        promoted_at=(promotion or {}).get("promoted_at"),
    )


def list_runs(*, limit: int = 50, offset: int = 0) -> list[AutoresearchRunSummary]:
    runs_root = _runs_dir()
    if not runs_root.exists():
        return []

    candidates: list[AutoresearchRunSummary] = []
    for child in runs_root.iterdir():
        if not child.is_dir():
            continue
        summary = _summary_from_run_dir(child)
        if summary:
            candidates.append(summary)

    candidates.sort(key=lambda item: item.created_at or item.run_id, reverse=True)
    sliced = candidates[offset : offset + limit] if limit > 0 else candidates[offset:]
    return sliced


def get_run_detail(run_id: str) -> AutoresearchRunDetail | None:
    run_dir = _runs_dir() / run_id
    runs_root = _runs_dir().resolve()
    try:
        run_dir_resolved = run_dir.resolve()
    except OSError:
        return None
    if runs_root not in run_dir_resolved.parents or not run_dir_resolved.is_dir():
        return None

    decision = _read_json_if_exists(run_dir / "decision.json")
    if not decision:
        return None

    summary = _summary_from_run_dir(run_dir)
    return AutoresearchRunDetail(
        run_id=run_id,
        created_at=summary.created_at if summary else None,
        status=str(decision.get("status", "unknown")),
        decision=decision,
        eval=_read_json_if_exists(run_dir / "eval.json"),
        diff=_read_json_if_exists(run_dir / "diff.json"),
        proposal=_read_json_if_exists(run_dir / "proposal.json"),
        proposal_meta=_read_json_if_exists(run_dir / "proposal_meta.json"),
        notes_markdown=_read_text_if_exists(run_dir / "notes.md"),
        promotion=_read_json_if_exists(run_dir / "promotion.json"),
    )


def leaderboard(*, top_n: int = 10) -> AutoresearchLeaderboard:
    summaries = [
        run for run in list_runs(limit=10_000, offset=0) if run.status == "kept"
    ]

    def _sort_key(item: AutoresearchRunSummary) -> tuple:
        primary = -(item.primary_value if item.primary_value is not None else float("-inf"))
        delta = -(item.delta if item.delta is not None else float("-inf"))
        return (primary, delta, item.run_id)

    summaries.sort(key=_sort_key)
    return AutoresearchLeaderboard(runs=summaries[: max(1, top_n)])


def promote_run(run_id: str, *, actor_user_id: str) -> AutoresearchPromotionResult:
    run_dir = _runs_dir() / run_id
    if not run_dir.is_dir():
        raise ValueError(f"Run '{run_id}' not found")

    decision = _read_json_if_exists(run_dir / "decision.json")
    proposal_path = run_dir / "proposal.json"
    if not decision or not proposal_path.exists():
        raise ValueError(f"Run '{run_id}' is missing decision.json or proposal.json")
    if decision.get("status") != "kept":
        raise ValueError(
            f"Refusing to promote run '{run_id}' (status={decision.get('status')}); "
            "only kept runs are promotable."
        )

    candidate_payload = _read_json_if_exists(proposal_path)
    if candidate_payload is None:
        raise ValueError(f"Run '{run_id}' proposal.json could not be parsed")

    ontology_module.validate_ontology_payload(candidate_payload)

    ontology_path = _ontology_path()
    pre_snapshot_path = run_dir / "pre_promotion_ontology.json"
    pre_snapshot_path.write_text(ontology_path.read_text())

    shutil.copyfile(proposal_path, ontology_path)
    ontology_module.load_ontology.cache_clear()

    promoted_at = datetime.now(timezone.utc).isoformat()
    promotion_record = {
        "run_id": run_id,
        "promoted_at": promoted_at,
        "decision": decision,
        "ontology_target": str(ontology_path.relative_to(_project_root())),
        "pre_promotion_snapshot": str(pre_snapshot_path.relative_to(_project_root())),
        "actor_user_id": actor_user_id,
    }
    promotion_path = run_dir / "promotion.json"
    with promotion_path.open("w") as handle:
        json.dump(promotion_record, handle, indent=2, sort_keys=True)
        handle.write("\n")

    audit_path = _audit_log_path()
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a") as handle:
        handle.write(json.dumps({"action": "promote_via_api", **promotion_record}, sort_keys=True) + "\n")

    return AutoresearchPromotionResult(
        run_id=run_id,
        promoted_at=promoted_at,
        ontology_target=promotion_record["ontology_target"],
        pre_promotion_snapshot=promotion_record["pre_promotion_snapshot"],
        decision=decision,
    )
