"""Single-experiment driver for the autoresearch loop.

Given a candidate ontology JSON path, this script:

1. Validates the candidate against ``OntologyConfig``.
2. Computes a structured diff vs. the frozen baseline ontology.
3. Temporarily swaps the candidate into ``data/ontologies/pancreatic_signal_rules.json``.
4. Runs the demo benchmark in both rules and hybrid modes.
5. Re-runs the demo benchmark a second time and asserts determinism.
6. Reads the published external sample snapshot for visibility.
7. Restores the production ontology.
8. Applies guardrails and writes ``eval.json`` and ``decision.json`` into the
   target run directory.

The driver never mutates ``autoresearch/baseline/`` and never writes to the
case database. It is safe to run repeatedly; failures restore the original
ontology before exiting.

Usage:
    python scripts/run_autoresearch_experiment.py \
        --candidate path/to/candidate.json \
        --run-dir autoresearch/runs/2026-04-25T14-22-09Z

If ``--run-dir`` is omitted a fresh timestamped directory is created under
``autoresearch/runs/``.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
ONTOLOGY_PATH = ROOT / "data" / "ontologies" / "pancreatic_signal_rules.json"
BASELINE_ONTOLOGY_PATH = ROOT / "autoresearch" / "baseline" / "pancreatic_signal_rules.json"
RUNS_DIR = ROOT / "autoresearch" / "runs"
EXTERNAL_SAMPLE_SNAPSHOT = ROOT / "docs" / "examples" / "retrospective-benchmark-sample-current.json"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


def _utc_now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _read_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _diff_ontologies(baseline: dict, candidate: dict) -> dict[str, Any]:
    """Compute a reviewer-readable diff of ``candidate`` vs. ``baseline``."""

    baseline_families = {family["code"]: family for family in baseline.get("families", [])}
    candidate_families = {family["code"]: family for family in candidate.get("families", [])}

    added_codes = sorted(set(candidate_families) - set(baseline_families))
    removed_codes = sorted(set(baseline_families) - set(candidate_families))
    common_codes = sorted(set(baseline_families) & set(candidate_families))

    family_changes: list[dict[str, Any]] = []
    for code in common_codes:
        before = baseline_families[code]
        after = candidate_families[code]
        diff_entry: dict[str, Any] = {"code": code}
        if before.get("weight") != after.get("weight"):
            diff_entry["weight"] = {"before": before.get("weight"), "after": after.get("weight")}
        if set(before.get("patterns", [])) != set(after.get("patterns", [])):
            diff_entry["patterns_added"] = sorted(
                set(after.get("patterns", [])) - set(before.get("patterns", []))
            )
            diff_entry["patterns_removed"] = sorted(
                set(before.get("patterns", [])) - set(after.get("patterns", []))
            )
        if before.get("label") != after.get("label"):
            diff_entry["label"] = {"before": before.get("label"), "after": after.get("label")}
        if len(diff_entry) > 1:
            family_changes.append(diff_entry)

    return {
        "added_family_codes": added_codes,
        "removed_family_codes": removed_codes,
        "family_changes": family_changes,
        "negations_added": sorted(set(candidate.get("negations", [])) - set(baseline.get("negations", []))),
        "negations_removed": sorted(set(baseline.get("negations", [])) - set(candidate.get("negations", []))),
        "uncertainty_added": sorted(
            set(candidate.get("uncertainty", [])) - set(baseline.get("uncertainty", []))
        ),
        "uncertainty_removed": sorted(
            set(baseline.get("uncertainty", [])) - set(candidate.get("uncertainty", []))
        ),
        "thresholds_before": baseline.get("thresholds"),
        "thresholds_after": candidate.get("thresholds"),
        "scoring_before": baseline.get("scoring"),
        "scoring_after": candidate.get("scoring"),
        "version_before": baseline.get("version"),
        "version_after": candidate.get("version"),
    }


def _load_external_snapshot() -> dict[str, Any] | None:
    if not EXTERNAL_SAMPLE_SNAPSHOT.exists():
        return None
    snapshot = _read_json(EXTERNAL_SAMPLE_SNAPSHOT)
    summary = snapshot.get("summary") or {}
    return {
        "snapshot_path": str(EXTERNAL_SAMPLE_SNAPSHOT.relative_to(ROOT)),
        "threshold": snapshot.get("threshold"),
        "top_k": snapshot.get("top_k"),
        "precision": summary.get("precision"),
        "recall": summary.get("recall"),
        "f1": summary.get("f1"),
        "precision_at_top_k": summary.get("precision_at_top_k"),
        "sensitivity_at_top_k": summary.get("sensitivity_at_top_k"),
        "note": (
            "Static published predictions; recorded for visibility. v2.0 autoresearch does not "
            "regenerate external predictions."
        ),
    }


def _evaluate_demo_for_ontology(ontology_payload: dict) -> dict[str, Any]:
    """Swap the production ontology for the candidate, run demo eval, restore."""

    from app.services import ontology as ontology_module
    from app.services.evaluation import evaluate_demo_dataset

    backup = ONTOLOGY_PATH.read_text()
    try:
        with ONTOLOGY_PATH.open("w") as handle:
            json.dump(ontology_payload, handle, indent=2)
            handle.write("\n")
        ontology_module.load_ontology.cache_clear()

        rules_summary = evaluate_demo_dataset(threshold=0.3, top_k=3, score_mode="rules")
        hybrid_summary = evaluate_demo_dataset(threshold=0.3, top_k=3, score_mode="hybrid")
    finally:
        ONTOLOGY_PATH.write_text(backup)
        ontology_module.load_ontology.cache_clear()

    return {
        "rules": rules_summary.model_dump(mode="json"),
        "hybrid": hybrid_summary.model_dump(mode="json"),
    }


def _summary_signature(summary: dict[str, Any]) -> tuple:
    """Reduce a demo summary to a hashable tuple for determinism comparison."""

    return (
        summary["threshold"],
        summary["top_k"],
        summary["precision"],
        summary["recall"],
        summary["f1"],
        summary["precision_at_top_k"],
        summary["sensitivity_at_top_k"],
        tuple(
            (case["case_id"], round(case["score"], 6), case["flagged"], case["expected_positive"])
            for case in summary.get("cases", [])
        ),
    )


def _evaluate_with_determinism(
    ontology_payload: dict,
    *,
    skip_determinism: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns ``(eval_payload, determinism_block)``.

    ``determinism_block`` records whether a second eval pass produced the same
    rules-mode signature.
    """

    primary = _evaluate_demo_for_ontology(ontology_payload)
    if skip_determinism:
        return primary, {"checked": False, "ok": None}

    secondary = _evaluate_demo_for_ontology(ontology_payload)
    primary_sig = _summary_signature(primary["rules"])
    secondary_sig = _summary_signature(secondary["rules"])
    return primary, {
        "checked": True,
        "ok": primary_sig == secondary_sig,
        "first_pass_signature_size": len(primary_sig[-1]),
        "second_pass_signature_size": len(secondary_sig[-1]),
    }


def _enforce_guardrails(
    *,
    candidate: dict,
    baseline: dict,
    eval_payload: dict[str, Any],
    baseline_eval: dict[str, Any],
    determinism: dict[str, Any],
    proposal_meta: dict[str, Any] | None,
) -> dict[str, Any]:
    """Apply the program.md guardrails. Returns the decision block."""

    reasons: list[str] = []
    behavior_change = bool((proposal_meta or {}).get("behavior_change"))
    declared_removed = set((proposal_meta or {}).get("removed_family_codes", []) or [])

    baseline_codes = {family["code"] for family in baseline.get("families", [])}
    candidate_codes = {family["code"] for family in candidate.get("families", [])}
    silently_removed = baseline_codes - candidate_codes - declared_removed
    if silently_removed and not behavior_change:
        reasons.append(
            "silent_rationale_code_deletion: "
            + ",".join(sorted(silently_removed))
            + " (set proposal.behavior_change=true and list removed_family_codes to authorize)"
        )

    thresholds = candidate.get("thresholds") or {}
    if not (
        thresholds.get("medium", 0.0)
        <= thresholds.get("high", 0.0)
        <= thresholds.get("critical", 0.0)
    ):
        reasons.append("threshold_ordering: medium <= high <= critical violated")

    over_limit_families = [
        family["code"]
        for family in candidate.get("families", [])
        if len(family.get("patterns", [])) > 200
    ]
    if over_limit_families:
        reasons.append("regex_blowup: families with >200 patterns: " + ",".join(over_limit_families))

    if determinism.get("checked") and not determinism.get("ok"):
        reasons.append("nondeterministic_eval: rules-mode summary differed across runs")

    rules_recall = eval_payload["rules"].get("sensitivity_at_top_k", 0.0)
    baseline_rules_recall = baseline_eval["rules"].get("sensitivity_at_top_k", 0.0)
    if rules_recall + 0.02 < baseline_rules_recall:
        reasons.append(
            f"demo_recall_floor: candidate sensitivity_at_top_k={rules_recall:.4f} "
            f"is more than 0.02 below baseline {baseline_rules_recall:.4f}"
        )

    candidate_f1 = eval_payload["rules"].get("f1", 0.0)
    baseline_f1 = baseline_eval["rules"].get("f1", 0.0)
    primary_metric_delta = round(candidate_f1 - baseline_f1, 6)

    decision: dict[str, Any]
    if reasons:
        decision = {
            "status": "discarded_guardrail",
            "primary_metric": "f1_at_top_k_demo_rules",
            "primary_value": candidate_f1,
            "baseline_value": baseline_f1,
            "delta": primary_metric_delta,
            "reasons": reasons,
        }
    elif candidate_f1 > baseline_f1 + 1e-9:
        decision = {
            "status": "kept",
            "primary_metric": "f1_at_top_k_demo_rules",
            "primary_value": candidate_f1,
            "baseline_value": baseline_f1,
            "delta": primary_metric_delta,
            "reasons": [],
        }
    else:
        decision = {
            "status": "discarded_no_improvement",
            "primary_metric": "f1_at_top_k_demo_rules",
            "primary_value": candidate_f1,
            "baseline_value": baseline_f1,
            "delta": primary_metric_delta,
            "reasons": ["primary_metric: candidate did not strictly beat baseline F1"],
        }

    decision["determinism"] = determinism
    return decision


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single autoresearch experiment")
    parser.add_argument(
        "--candidate",
        type=Path,
        required=True,
        help="Path to the candidate ontology JSON to evaluate.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=BASELINE_ONTOLOGY_PATH,
        help="Path to the frozen baseline ontology JSON.",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Directory to write run artifacts into. Defaults to a fresh autoresearch/runs/<ts>/.",
    )
    parser.add_argument(
        "--proposal-meta",
        type=Path,
        default=None,
        help="Optional path to proposal_meta.json supplied by the agent.",
    )
    parser.add_argument(
        "--notes",
        type=Path,
        default=None,
        help="Optional path to notes.md to copy into the run directory.",
    )
    parser.add_argument(
        "--skip-determinism",
        action="store_true",
        help="Skip the duplicate eval determinism check (useful for fast iteration).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    candidate_path = args.candidate.resolve()
    baseline_path = args.baseline.resolve()
    if not candidate_path.exists():
        print(f"error: candidate ontology not found at {candidate_path}", file=sys.stderr)
        return 2
    if not baseline_path.exists():
        print(f"error: baseline ontology not found at {baseline_path}", file=sys.stderr)
        return 2

    run_dir = args.run_dir or (RUNS_DIR / _utc_now_slug())
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    from app.services.ontology import validate_ontology_payload

    candidate_payload = _read_json(candidate_path)
    baseline_payload = _read_json(baseline_path)

    try:
        validate_ontology_payload(candidate_payload)
    except Exception as exc:  # pydantic ValidationError or json error
        decision = {
            "status": "discarded_guardrail",
            "primary_metric": "f1_at_top_k_demo_rules",
            "primary_value": None,
            "baseline_value": None,
            "delta": None,
            "reasons": [f"schema_validation: {exc.__class__.__name__}: {exc}"],
        }
        _write_json(run_dir / "decision.json", decision)
        _write_json(run_dir / "proposal.json", candidate_payload)
        print(f"[autoresearch] candidate rejected by schema: {decision['reasons'][0]}", file=sys.stderr)
        return 1

    proposal_meta: dict[str, Any] | None = None
    if args.proposal_meta and args.proposal_meta.exists():
        proposal_meta = _read_json(args.proposal_meta)

    diff = _diff_ontologies(baseline_payload, candidate_payload)
    _write_json(run_dir / "diff.json", diff)
    _write_json(run_dir / "proposal.json", candidate_payload)
    if proposal_meta is not None:
        _write_json(run_dir / "proposal_meta.json", proposal_meta)

    if args.notes and args.notes.exists():
        shutil.copyfile(args.notes, run_dir / "notes.md")

    try:
        baseline_eval = _evaluate_demo_for_ontology(baseline_payload)
        candidate_eval, determinism = _evaluate_with_determinism(
            candidate_payload, skip_determinism=args.skip_determinism
        )
    except Exception as exc:  # pragma: no cover - defensive
        traceback.print_exc()
        decision = {
            "status": "discarded_guardrail",
            "primary_metric": "f1_at_top_k_demo_rules",
            "primary_value": None,
            "baseline_value": None,
            "delta": None,
            "reasons": [f"eval_crashed: {exc.__class__.__name__}: {exc}"],
        }
        _write_json(run_dir / "decision.json", decision)
        return 1

    external_snapshot = _load_external_snapshot()

    eval_payload: dict[str, Any] = {
        "primary_metric": "f1_at_top_k_demo_rules",
        "operating_point": {"threshold": 0.3, "top_k": 3},
        "candidate": candidate_eval,
        "baseline": baseline_eval,
        "external_sample": external_snapshot,
    }
    _write_json(run_dir / "eval.json", eval_payload)

    decision = _enforce_guardrails(
        candidate=candidate_payload,
        baseline=baseline_payload,
        eval_payload=candidate_eval,
        baseline_eval=baseline_eval,
        determinism=determinism,
        proposal_meta=proposal_meta,
    )
    decision["run_dir"] = str(run_dir.relative_to(ROOT))
    decision["candidate_path"] = str(candidate_path.relative_to(ROOT)) if ROOT in candidate_path.parents else str(candidate_path)
    decision["baseline_path"] = str(baseline_path.relative_to(ROOT)) if ROOT in baseline_path.parents else str(baseline_path)
    _write_json(run_dir / "decision.json", decision)

    primary_value = decision.get("primary_value")
    baseline_value = decision.get("baseline_value")
    delta_value = decision.get("delta")
    print(
        f"[autoresearch] {decision['status']} | f1 "
        f"candidate={primary_value if primary_value is None else f'{primary_value:.4f}'} "
        f"baseline={baseline_value if baseline_value is None else f'{baseline_value:.4f}'} "
        f"delta={delta_value if delta_value is None else f'{delta_value:+.4f}'}"
    )
    if decision.get("reasons"):
        for reason in decision["reasons"]:
            print(f"[autoresearch]   reason: {reason}")

    return 0 if decision["status"] != "discarded_guardrail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
