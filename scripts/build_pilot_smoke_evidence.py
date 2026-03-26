from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a release-friendly pilot smoke evidence bundle from downloaded "
            "pilot-smoke-summary.json artifacts."
        )
    )
    parser.add_argument(
        "--summary-json",
        action="append",
        default=[],
        help="Path to a pilot-smoke-summary.json artifact. Repeat as needed.",
    )
    parser.add_argument(
        "--summary-dir",
        action="append",
        default=[],
        help=(
            "Directory containing downloaded artifact folders. The script will recurse "
            "for pilot-smoke-summary.json files."
        ),
    )
    parser.add_argument("--out-json", required=True, help="Path to write the bundled JSON evidence.")
    parser.add_argument(
        "--out-markdown",
        required=True,
        help="Path to write the bundled Markdown evidence summary.",
    )
    parser.add_argument(
        "--hl7-decision",
        choices=("pending", "keep-manual", "promote-default"),
        default="pending",
        help="Recorded hosted HL7 decision for this evidence bundle.",
    )
    parser.add_argument(
        "--hl7-rationale",
        action="append",
        default=[],
        help="Optional rationale line for the hosted HL7 decision. Repeat as needed.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    summary_paths = discover_summary_paths(args.summary_json, args.summary_dir)
    summaries = [json.loads(path.read_text(encoding="utf-8")) for path in summary_paths]

    bundle = build_evidence_bundle(
        summaries=summaries,
        summary_paths=summary_paths,
        hl7_decision=args.hl7_decision,
        hl7_rationales=args.hl7_rationale,
    )

    out_json = Path(args.out_json)
    out_markdown = Path(args.out_markdown)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_markdown.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    out_markdown.write_text(render_markdown(bundle), encoding="utf-8")
    return 0


def discover_summary_paths(summary_jsons: list[str], summary_dirs: list[str]) -> list[Path]:
    discovered: list[Path] = []

    for raw_path in summary_jsons:
        path = Path(raw_path)
        if not path.is_file():
            raise SystemExit(f"Summary JSON path does not exist or is not a file: {raw_path}")
        discovered.append(path.resolve())

    for raw_dir in summary_dirs:
        path = Path(raw_dir)
        if not path.exists():
            raise SystemExit(f"Summary directory does not exist: {raw_dir}")
        if path.is_file():
            discovered.append(path.resolve())
            continue
        discovered.extend(sorted(candidate.resolve() for candidate in path.rglob("pilot-smoke-summary.json")))

    unique_paths: list[Path] = []
    seen: set[str] = set()
    for path in discovered:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique_paths.append(path)

    if not unique_paths:
        raise SystemExit(
            "No pilot-smoke-summary.json files were provided. Use --summary-json or --summary-dir."
        )

    return unique_paths


def build_evidence_bundle(
    *,
    summaries: list[dict[str, Any]],
    summary_paths: list[Path],
    hl7_decision: str,
    hl7_rationales: list[str],
) -> dict[str, Any]:
    normalized_jobs = [
        normalize_summary_job(summary=summary, source_path=path)
        for summary, path in zip(summaries, summary_paths, strict=True)
    ]

    runs = build_workflow_runs(normalized_jobs)

    primary_fhir_run = select_primary_run(runs=runs, payload_kind="fhir")
    primary_hl7_run = select_primary_run(runs=runs, payload_kind="hl7")

    hl7_mode = {
        "pending": "pending",
        "keep-manual": "manual_only",
        "promote-default": "default",
    }[hl7_decision]

    phase_status = {
        "hosted_fhir_confirmed": primary_fhir_run is not None,
        "primary_fhir_run_id": primary_fhir_run.get("run_id") if primary_fhir_run else None,
        "primary_fhir_run_url": primary_fhir_run.get("run_url") if primary_fhir_run else None,
        "hosted_hl7_trial_recorded": primary_hl7_run is not None,
        "primary_hl7_run_id": primary_hl7_run.get("run_id") if primary_hl7_run else None,
        "primary_hl7_run_url": primary_hl7_run.get("run_url") if primary_hl7_run else None,
        "hl7_hosting_mode": hl7_mode,
        "hl7_decision_complete": hl7_decision != "pending",
        "hl7_rationales": [item for item in hl7_rationales if item.strip()],
        "phase_complete": primary_fhir_run is not None and hl7_decision != "pending",
    }

    return {
        "summary_count": len(normalized_jobs),
        "workflow_runs": runs,
        "phase_status": phase_status,
        "copyable_snippets": build_copyable_snippets(
            primary_fhir_run=primary_fhir_run,
            primary_hl7_run=primary_hl7_run,
            hl7_mode=hl7_mode,
            hl7_rationales=phase_status["hl7_rationales"],
        ),
    }


def normalize_summary_job(*, summary: dict[str, Any], source_path: Path) -> dict[str, Any]:
    workflow = summary.get("workflow")
    workflow = workflow if isinstance(workflow, dict) else {}

    import_runs = summary.get("import_runs")
    import_runs = import_runs if isinstance(import_runs, list) else []
    normalized_import_runs = [item for item in import_runs if isinstance(item, dict)]

    job_name = _clean_string(workflow.get("job_name"))
    job_scope = _clean_string(workflow.get("job_scope"))
    dispatch_scope = _clean_string(workflow.get("dispatch_scope"))
    summary_artifact_name = _clean_string(workflow.get("summary_artifact_name"))
    log_artifact_name = _clean_string(workflow.get("log_artifact_name"))
    payload_kind = infer_payload_kind(
        dispatch_scope=dispatch_scope,
        job_scope=job_scope,
        job_name=job_name,
        import_runs=normalized_import_runs,
    )

    duration_seconds = _coerce_int(workflow.get("duration_seconds"))
    exit_code = _coerce_int(workflow.get("exit_code"))
    outcome = _clean_string(workflow.get("outcome"))

    return {
        "source_path": str(source_path),
        "run_id": _clean_string(workflow.get("run_id")),
        "run_url": _clean_string(workflow.get("run_url")),
        "run_attempt": _clean_string(workflow.get("run_attempt")),
        "event_name": _clean_string(workflow.get("event_name")),
        "repository": _clean_string(workflow.get("repository")),
        "ref": _clean_string(workflow.get("ref")),
        "sha": _clean_string(workflow.get("sha")),
        "dispatch_scope": dispatch_scope,
        "job_name": job_name,
        "job_scope": job_scope,
        "smoke_command": _clean_string(workflow.get("smoke_command")),
        "outcome": outcome,
        "exit_code": exit_code,
        "duration_seconds": duration_seconds,
        "started_at": _clean_string(workflow.get("started_at")),
        "finished_at": _clean_string(workflow.get("finished_at")),
        "summary_generated_at": _clean_string(workflow.get("summary_generated_at")),
        "log_artifact_name": log_artifact_name,
        "summary_artifact_name": summary_artifact_name,
        "auth_mode": infer_auth_mode(
            job_name=job_name,
            summary_artifact_name=summary_artifact_name,
            log_artifact_name=log_artifact_name,
        ),
        "payload_kind": payload_kind,
        "success": outcome == "success" and (exit_code is None or exit_code == 0) and all(
            _clean_string(item.get("status")) in {"", "completed"} for item in normalized_import_runs
        ),
        "visible_case_count": _coerce_int(summary.get("visible_case_count")),
        "sample_case_ids": [
            str(item)
            for item in (summary.get("sample_case_ids") or [])
            if str(item).strip()
        ],
        "review_roundtrip_case_id": _clean_string(summary.get("review_roundtrip_case_id")),
        "import_runs": normalized_import_runs,
    }


def infer_payload_kind(
    *,
    dispatch_scope: str,
    job_scope: str,
    job_name: str,
    import_runs: list[dict[str, Any]],
) -> str:
    scope_text = " ".join(part for part in (dispatch_scope, job_scope, job_name) if part).lower()
    source_formats = {
        _clean_string(item.get("source_format")).lower()
        for item in import_runs
        if _clean_string(item.get("source_format"))
    }

    if "fhir" in scope_text or "fhir-diagnostic-report" in source_formats:
        return "fhir"
    if "hl7" in scope_text or "hl7-oru" in source_formats:
        return "hl7"
    return "other"


def infer_auth_mode(*, job_name: str, summary_artifact_name: str, log_artifact_name: str) -> str:
    combined = " ".join(part for part in (job_name, summary_artifact_name, log_artifact_name) if part).lower()
    if "proxy" in combined:
        return "proxy"
    if "header" in combined:
        return "header"
    return "unknown"


def build_workflow_runs(normalized_jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, job in enumerate(normalized_jobs):
        key = job["run_id"] or job["run_url"] or f"local-{index}"
        grouped[key].append(job)

    workflow_runs: list[dict[str, Any]] = []
    for jobs in grouped.values():
        jobs.sort(
            key=lambda item: (
                item["dispatch_scope"],
                item["payload_kind"],
                item["auth_mode"],
                item["job_name"],
                item["source_path"],
            )
        )
        durations = [value for value in (job["duration_seconds"] for job in jobs) if value is not None]
        started_at = [value for value in (job["started_at"] for job in jobs) if value]
        finished_at = [value for value in (job["finished_at"] for job in jobs) if value]
        payload_kinds = sorted({job["payload_kind"] for job in jobs if job["payload_kind"] != "other"})
        auth_modes = sorted({job["auth_mode"] for job in jobs if job["auth_mode"]})
        run = {
            "run_id": first_non_empty(job["run_id"] for job in jobs),
            "run_url": first_non_empty(job["run_url"] for job in jobs),
            "run_attempt": first_non_empty(job["run_attempt"] for job in jobs),
            "event_name": first_non_empty(job["event_name"] for job in jobs),
            "repository": first_non_empty(job["repository"] for job in jobs),
            "ref": first_non_empty(job["ref"] for job in jobs),
            "sha": first_non_empty(job["sha"] for job in jobs),
            "dispatch_scope": first_non_empty(job["dispatch_scope"] for job in jobs),
            "payload_kinds": payload_kinds,
            "auth_modes": auth_modes,
            "job_count": len(jobs),
            "successful_job_count": sum(1 for job in jobs if job["success"]),
            "success": all(job["success"] for job in jobs),
            "started_at": min(started_at) if started_at else "",
            "finished_at": max(finished_at) if finished_at else "",
            "max_job_duration_seconds": max(durations) if durations else None,
            "total_job_duration_seconds": sum(durations) if durations else None,
            "jobs": jobs,
        }
        workflow_runs.append(run)

    workflow_runs.sort(key=workflow_run_sort_key)
    return workflow_runs


def select_primary_run(*, runs: list[dict[str, Any]], payload_kind: str) -> dict[str, Any] | None:
    candidates = [run for run in runs if run["success"] and payload_kind in run["payload_kinds"]]
    if not candidates:
        return None

    preferred = [
        run
        for run in candidates
        if set(run["auth_modes"]) >= {"header", "proxy"}
        and (
            run.get("dispatch_scope") == f"{payload_kind}-success-only"
            or run.get("dispatch_scope") == ""
        )
    ]
    if preferred:
        candidates = preferred

    return sorted(candidates, key=workflow_run_sort_key)[0]


def workflow_run_sort_key(run: dict[str, Any]) -> tuple[str, int]:
    run_id = _coerce_int(run.get("run_id"))
    return (
        _clean_string(run.get("started_at")) or _clean_string(run.get("finished_at")),
        run_id if run_id is not None else 0,
    )


def build_copyable_snippets(
    *,
    primary_fhir_run: dict[str, Any] | None,
    primary_hl7_run: dict[str, Any] | None,
    hl7_mode: str,
    hl7_rationales: list[str],
) -> dict[str, str]:
    snippets = {
        "fhir_handoff": "",
        "hl7_handoff": "",
    }

    if primary_fhir_run is not None:
        snippets["fhir_handoff"] = (
            "Hosted FHIR smoke confirmation: "
            f"{format_run_link(primary_fhir_run)} "
            f"completed across `{', '.join(primary_fhir_run['auth_modes'])}` "
            f"with summary artifacts `{', '.join(job['summary_artifact_name'] for job in primary_fhir_run['jobs'] if job['summary_artifact_name'])}`."
        )
    else:
        snippets["fhir_handoff"] = (
            "Hosted FHIR smoke confirmation is still pending; no successful downloaded "
            "summary bundle has been recorded yet."
        )

    decision_label = {
        "pending": "pending",
        "manual_only": "keep manual-only",
        "default": "promote into the default hosted matrix",
    }[hl7_mode]
    rationale_text = " ".join(hl7_rationales).strip()
    hl7_basis = ""
    if primary_hl7_run is not None:
        hl7_basis = f" based on {format_run_link(primary_hl7_run)}"
    elif hl7_mode != "pending":
        hl7_basis = " without a successful hosted HL7 summary bundle attached yet"

    snippets["hl7_handoff"] = f"Hosted HL7 decision: {decision_label}{hl7_basis}."
    if rationale_text:
        snippets["hl7_handoff"] += f" Rationale: {rationale_text}"

    return snippets


def render_markdown(bundle: dict[str, Any]) -> str:
    phase_status = bundle["phase_status"]
    workflow_runs = bundle["workflow_runs"]

    lines = ["# Pilot Smoke Evidence Bundle", ""]

    lines.append("## Phase Status")
    lines.append(f"- Hosted FHIR confirmed: `{phase_status['hosted_fhir_confirmed']}`")
    lines.append(f"- Hosted HL7 trial recorded: `{phase_status['hosted_hl7_trial_recorded']}`")
    lines.append(f"- HL7 hosting mode: `{phase_status['hl7_hosting_mode']}`")
    lines.append(f"- HL7 decision complete: `{phase_status['hl7_decision_complete']}`")
    lines.append(f"- Phase complete: `{phase_status['phase_complete']}`")

    if phase_status["hl7_rationales"]:
        lines.append("")
        lines.append("## HL7 Decision Rationale")
        for rationale in phase_status["hl7_rationales"]:
            lines.append(f"- {rationale}")

    lines.append("")
    lines.append("## Workflow Runs")
    for run in workflow_runs:
        lines.append(f"- {format_run_link(run)}")
        if run["dispatch_scope"]:
            lines.append(f"  Dispatch scope: `{run['dispatch_scope']}`")
        if run["ref"]:
            lines.append(f"  Ref: `{run['ref']}`")
        if run["started_at"]:
            lines.append(f"  Started at: `{run['started_at']}`")
        if run["finished_at"]:
            lines.append(f"  Finished at: `{run['finished_at']}`")
        lines.append(f"  Success: `{run['success']}`")
        if run["payload_kinds"]:
            lines.append(f"  Payloads: `{', '.join(run['payload_kinds'])}`")
        if run["auth_modes"]:
            lines.append(f"  Auth modes: `{', '.join(run['auth_modes'])}`")
        if run["max_job_duration_seconds"] is not None:
            lines.append(f"  Max job duration seconds: `{run['max_job_duration_seconds']}`")
        if run["total_job_duration_seconds"] is not None:
            lines.append(f"  Total job duration seconds: `{run['total_job_duration_seconds']}`")
        for job in run["jobs"]:
            lines.append(
                "  Job "
                f"`{job['job_name'] or job['source_path']}` "
                f"outcome `{job['outcome'] or 'unknown'}` "
                f"payload `{job['payload_kind']}` "
                f"auth `{job['auth_mode']}`"
            )
            if job["summary_artifact_name"]:
                lines.append(f"  Summary artifact: `{job['summary_artifact_name']}`")
            if job["visible_case_count"] is not None:
                lines.append(f"  Visible cases: `{job['visible_case_count']}`")
            if job["review_roundtrip_case_id"]:
                lines.append(f"  Review round-trip case: `{job['review_roundtrip_case_id']}`")

    lines.append("")
    lines.append("## Copyable Snippets")
    lines.append(f"- {bundle['copyable_snippets']['fhir_handoff']}")
    lines.append(f"- {bundle['copyable_snippets']['hl7_handoff']}")
    lines.append("")

    return "\n".join(lines)


def format_run_link(run: dict[str, Any]) -> str:
    run_id = _clean_string(run.get("run_id"))
    run_url = _clean_string(run.get("run_url"))
    if run_id and run_url:
        return f"[#{run_id}]({run_url})"
    if run_id:
        return f"`#{run_id}`"
    if run_url:
        return f"`{run_url}`"
    return "`local summary bundle`"


def first_non_empty(values: Any) -> str:
    for value in values:
        cleaned = _clean_string(value)
        if cleaned:
            return cleaned
    return ""


def _clean_string(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _coerce_int(value: Any) -> int | None:
    text = _clean_string(value)
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
