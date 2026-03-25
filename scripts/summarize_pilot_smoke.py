from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize a Pancreatic Signal pilot smoke log into JSON and Markdown artifacts."
    )
    parser.add_argument("--log-path", required=True, help="Path to the pilot smoke log file.")
    parser.add_argument("--out-json", required=True, help="Path to write the structured JSON summary.")
    parser.add_argument("--out-markdown", required=True, help="Path to write the Markdown summary.")
    parser.add_argument("--workflow-name", default="Pilot Smoke", help="Workflow name.")
    parser.add_argument("--job-name", default="", help="Matrix job display name.")
    parser.add_argument("--job-scope", default="", help="Matrix job scope label.")
    parser.add_argument("--dispatch-scope", default="", help="Manual dispatch scope, if any.")
    parser.add_argument("--smoke-command", default="", help="Smoke command executed by the workflow.")
    parser.add_argument("--log-artifact-name", default="", help="Uploaded raw log artifact name.")
    parser.add_argument("--summary-artifact-name", default="", help="Uploaded structured summary artifact name.")
    parser.add_argument("--event-name", default="", help="GitHub event name for the workflow run.")
    parser.add_argument("--outcome", default="", help="Step outcome for the smoke command.")
    parser.add_argument("--exit-code", default="", help="Smoke command exit code.")
    parser.add_argument("--duration-seconds", default="", help="Smoke command duration in seconds.")
    parser.add_argument("--started-at", default="", help="UTC timestamp when the smoke command started.")
    parser.add_argument("--finished-at", default="", help="UTC timestamp when the smoke command finished.")
    parser.add_argument(
        "--summary-generated-at",
        default="",
        help="UTC timestamp when the structured summary was generated.",
    )
    parser.add_argument("--run-id", default="", help="GitHub Actions run ID.")
    parser.add_argument("--run-attempt", default="", help="GitHub Actions run attempt.")
    parser.add_argument("--run-url", default="", help="GitHub Actions run URL.")
    parser.add_argument("--repository", default="", help="GitHub repository name.")
    parser.add_argument("--ref", default="", help="Git ref for the workflow run.")
    parser.add_argument("--sha", default="", help="Git SHA for the workflow run.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    log_path = Path(args.log_path)
    log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""

    summary = build_summary(
        log_text=log_text,
        workflow_context={
            "name": args.workflow_name,
            "job_name": args.job_name,
            "job_scope": args.job_scope,
            "dispatch_scope": args.dispatch_scope or None,
            "smoke_command": args.smoke_command,
            "log_artifact_name": args.log_artifact_name,
            "summary_artifact_name": args.summary_artifact_name,
            "event_name": args.event_name,
            "outcome": args.outcome,
            "exit_code": args.exit_code,
            "duration_seconds": args.duration_seconds,
            "started_at": args.started_at,
            "finished_at": args.finished_at,
            "summary_generated_at": args.summary_generated_at,
            "run_id": args.run_id,
            "run_attempt": args.run_attempt,
            "run_url": args.run_url,
            "repository": args.repository,
            "ref": args.ref,
            "sha": args.sha,
        },
        log_path=log_path,
    )

    out_json = Path(args.out_json)
    out_markdown = Path(args.out_markdown)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_markdown.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    out_markdown.write_text(render_markdown(summary), encoding="utf-8")
    return 0


def build_summary(
    *,
    log_text: str,
    workflow_context: dict[str, Any],
    log_path: Path,
) -> dict[str, Any]:
    blocks = extract_named_json_blocks(log_text)
    summary_blocks, detail_blocks, other_blocks = partition_json_blocks(blocks)

    import_runs: list[dict[str, Any]] = []
    for label, detail in detail_blocks.items():
        run_id = detail.get("run_id")
        status = detail.get("status")
        if not isinstance(run_id, int) or not isinstance(status, str):
            continue

        paired_summary = summary_blocks.get(label, {})
        failure_counts = detail.get("failure_counts")
        imported_sites = detail.get("imported_sites")
        import_runs.append(
            {
                "label": label,
                "run_id": run_id,
                "status": status,
                "source_format": detail.get("source_format"),
                "processed": detail.get("processed"),
                "failed": detail.get("failed"),
                "failure_counts": failure_counts if isinstance(failure_counts, dict) else {},
                "imported_sites": imported_sites if isinstance(imported_sites, list) else [],
                "status_code": paired_summary.get("status_code"),
                "detail": paired_summary.get("detail"),
            }
        )

    import_runs.sort(key=lambda item: item["run_id"])

    visible_case_count = _last_int_match(log_text, r"Visible cases:\s+(\d+)")
    sample_case_ids = _last_csv_match(log_text, r"Sample case IDs:\s+(.+)")
    review_roundtrip_case_id = _last_string_match(
        log_text,
        r"Review round-trip verified for case ([^.\s]+)\.",
    )

    return {
        "workflow": workflow_context,
        "log_path": str(log_path),
        "log_present": bool(log_text),
        "checks": {
            "api_ready_status": _last_string_match(log_text, r"API ready:\s+(.+)"),
            "web_root_ok": "Web root responded with HTTP 200." in log_text,
            "imports_page_ok": "Import workspace responded with HTTP 200." in log_text,
        },
        "resolved_actor": other_blocks.get("Resolved actor"),
        "resolved_alternate_actor": other_blocks.get("Resolved alternate actor"),
        "visible_case_count": visible_case_count,
        "sample_case_ids": sample_case_ids,
        "review_roundtrip_case_id": review_roundtrip_case_id,
        "import_runs": import_runs,
        "milestones": [
            line.strip()
            for line in log_text.splitlines()
            if line.strip().startswith(("Imported ", "Verified ", "Review round-trip verified"))
        ],
    }


def extract_named_json_blocks(log_text: str) -> list[tuple[str, dict[str, Any]]]:
    blocks: list[tuple[str, dict[str, Any]]] = []
    lines = log_text.splitlines()
    index = 0

    while index < len(lines):
        label = lines[index].strip()
        if not label.endswith(":") or index + 1 >= len(lines):
            index += 1
            continue
        if not lines[index + 1].lstrip().startswith("{"):
            index += 1
            continue

        payload, next_index = _parse_json_block(lines, index + 1)
        if payload is None:
            index += 1
            continue

        blocks.append((label[:-1], payload))
        index = next_index

    return blocks


def partition_json_blocks(
    blocks: list[tuple[str, dict[str, Any]]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    summary_blocks: dict[str, dict[str, Any]] = {}
    detail_blocks: dict[str, dict[str, Any]] = {}
    other_blocks: dict[str, dict[str, Any]] = {}

    for label, payload in blocks:
        if label.endswith(" summary"):
            summary_blocks[label[: -len(" summary")]] = payload
        elif label.endswith(" detail"):
            detail_blocks[label[: -len(" detail")]] = payload
        else:
            other_blocks[label] = payload

    return summary_blocks, detail_blocks, other_blocks


def render_markdown(summary: dict[str, Any]) -> str:
    workflow = summary["workflow"]
    lines = ["# Pilot Smoke Summary", ""]

    lines.append("## Workflow")
    run_id = str(workflow.get("run_id") or "").strip()
    run_url = str(workflow.get("run_url") or "").strip()
    if run_id and run_url:
        lines.append(f"- Run: [#{run_id}]({run_url})")
    elif run_id:
        lines.append(f"- Run: `#{run_id}`")

    for label, key in (
        ("Outcome", "outcome"),
        ("Event", "event_name"),
        ("Job", "job_name"),
        ("Scope", "job_scope"),
        ("Dispatch scope", "dispatch_scope"),
        ("Smoke command", "smoke_command"),
        ("Exit code", "exit_code"),
        ("Duration seconds", "duration_seconds"),
        ("Started at", "started_at"),
        ("Finished at", "finished_at"),
        ("Summary generated at", "summary_generated_at"),
        ("Repository", "repository"),
        ("Ref", "ref"),
        ("SHA", "sha"),
        ("Run attempt", "run_attempt"),
        ("Raw log artifact", "log_artifact_name"),
        ("Structured summary artifact", "summary_artifact_name"),
    ):
        value = str(workflow.get(key) or "").strip()
        if value:
            lines.append(f"- {label}: `{value}`")

    actor = summary.get("resolved_actor")
    if isinstance(actor, dict):
        lines.append("")
        lines.append("## Actor")
        lines.append(f"- User: `{actor.get('user_id', '')}`")
        role = str(actor.get("role") or "").strip()
        if role:
            lines.append(f"- Role: `{role}`")
        site_scope = actor.get("site_scope")
        if isinstance(site_scope, list) and site_scope:
            lines.append(f"- Site scope: `{', '.join(str(item) for item in site_scope)}`")

    alternate_actor = summary.get("resolved_alternate_actor")
    if isinstance(alternate_actor, dict):
        lines.append("")
        lines.append("## Alternate Actor")
        lines.append(f"- User: `{alternate_actor.get('user_id', '')}`")
        role = str(alternate_actor.get("role") or "").strip()
        if role:
            lines.append(f"- Role: `{role}`")
        site_scope = alternate_actor.get("site_scope")
        if isinstance(site_scope, list) and site_scope:
            lines.append(f"- Site scope: `{', '.join(str(item) for item in site_scope)}`")

    checks = summary.get("checks", {})
    lines.append("")
    lines.append("## Checks")
    api_ready_status = str(checks.get("api_ready_status") or "").strip()
    if api_ready_status:
        lines.append(f"- API readiness: `{api_ready_status}`")
    lines.append(f"- Web root OK: `{checks.get('web_root_ok')}`")
    lines.append(f"- Imports page OK: `{checks.get('imports_page_ok')}`")

    visible_case_count = summary.get("visible_case_count")
    sample_case_ids = summary.get("sample_case_ids") or []
    review_roundtrip_case_id = summary.get("review_roundtrip_case_id")
    if visible_case_count is not None or sample_case_ids or review_roundtrip_case_id:
        lines.append("")
        lines.append("## Cases")
        if visible_case_count is not None:
            lines.append(f"- Visible cases: `{visible_case_count}`")
        if sample_case_ids:
            lines.append(f"- Sample case IDs: `{', '.join(str(item) for item in sample_case_ids)}`")
        if review_roundtrip_case_id:
            lines.append(f"- Review round-trip case: `{review_roundtrip_case_id}`")

    import_runs = summary.get("import_runs") or []
    if import_runs:
        lines.append("")
        lines.append("## Import Runs")
        for run in import_runs:
            failure_counts = run.get("failure_counts") or {}
            failure_suffix = ""
            if isinstance(failure_counts, dict) and failure_counts:
                failure_suffix = f", failure_counts={json.dumps(failure_counts, sort_keys=True)}"
            lines.append(
                "- "
                f"{run['label']}: run `#{run['run_id']}` status `{run.get('status')}` "
                f"format `{run.get('source_format')}` processed `{run.get('processed')}` "
                f"failed `{run.get('failed')}`{failure_suffix}"
            )

    milestones = summary.get("milestones") or []
    if milestones:
        lines.append("")
        lines.append("## Milestones")
        for milestone in milestones:
            lines.append(f"- {milestone}")

    lines.append("")
    return "\n".join(lines)


def _parse_json_block(lines: list[str], start_index: int) -> tuple[dict[str, Any] | None, int]:
    decoder = json.JSONDecoder()
    buffer: list[str] = []

    for index in range(start_index, len(lines)):
        buffer.append(lines[index])
        candidate = "\n".join(buffer).strip()
        if not candidate:
            continue
        try:
            payload, end_index = decoder.raw_decode(candidate)
        except json.JSONDecodeError:
            continue
        if candidate[end_index:].strip():
            continue
        if isinstance(payload, dict):
            return payload, index + 1

    return None, start_index + 1


def _last_int_match(text: str, pattern: str) -> int | None:
    matches = re.findall(pattern, text)
    if not matches:
        return None
    try:
        return int(matches[-1])
    except ValueError:
        return None


def _last_string_match(text: str, pattern: str) -> str | None:
    matches = re.findall(pattern, text)
    if not matches:
        return None
    value = matches[-1]
    if isinstance(value, tuple):
        value = value[0]
    stripped = str(value).strip()
    return stripped or None


def _last_csv_match(text: str, pattern: str) -> list[str]:
    value = _last_string_match(text, pattern)
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
