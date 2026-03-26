from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SUMMARY_SCRIPT = ROOT / "scripts" / "summarize_pilot_smoke.py"


def _load_summary_module():
    spec = importlib.util.spec_from_file_location("summarize_pilot_smoke", SUMMARY_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_summary_extracts_fhir_success_metadata() -> None:
    summarize = _load_summary_module()
    log_text = """
Waiting for API readiness at http://localhost:8000/api/v1/health/ready
API ready: ok
Waiting for web root at http://localhost:3000
Web root responded with HTTP 200.
Waiting for web import workspace at http://localhost:3000/imports
Import workspace responded with HTTP 200.

Resolved actor:
{
  "authenticated": true,
  "display_name": "Pilot Navigator",
  "role": "pdac-navigator",
  "site_scope": [
    "Demo Hospital"
  ],
  "user_id": "pilot-navigator"
}
FHIR import run summary:
{
  "case_ids": [
    "dr-fhir-smoke-20260325180000"
  ],
  "created": 1,
  "failed": 0,
  "flagged": 1,
  "processed": 1,
  "report_ids": [
    "dr-fhir-smoke-20260325180000"
  ],
  "run_id": 88,
  "source_format": "fhir-diagnostic-report",
  "updated": 0
}
FHIR import run detail:
{
  "failed": 0,
  "failure_counts": {},
  "imported_sites": [
    "Demo Hospital"
  ],
  "processed": 1,
  "run_id": 88,
  "source_format": "fhir-diagnostic-report",
  "status": "completed"
}

Imported 1 demo case(s) through /api/v1/imports/fhir/diagnostic-reports.
Verified persisted FHIR import run #88.

Visible cases: 1
Sample case IDs: dr-fhir-smoke-20260325180000

Review round-trip verified for case dr-fhir-smoke-20260325180000.
""".strip()

    summary = summarize.build_summary(
        log_text=log_text,
        workflow_context={
            "name": "Pilot Smoke",
            "job_name": "Proxy Demo FHIR Smoke",
            "job_scope": "fhir-success",
            "dispatch_scope": "fhir-success-only",
            "smoke_command": "make pilot-proxy-demo-fhir-smoke",
            "log_artifact_name": "pilot-smoke-proxy-demo-fhir-smoke",
            "summary_artifact_name": "pilot-smoke-summary-proxy-demo-fhir-smoke",
            "event_name": "workflow_dispatch",
            "outcome": "success",
            "exit_code": "0",
            "duration_seconds": "187",
            "started_at": "2026-03-25T19:10:00Z",
            "finished_at": "2026-03-25T19:13:07Z",
            "summary_generated_at": "2026-03-25T19:13:10Z",
            "run_id": "123456789",
            "run_attempt": "1",
            "run_url": "https://github.com/example/repo/actions/runs/123456789",
            "repository": "example/repo",
            "ref": "refs/heads/main",
            "sha": "abc123",
        },
        log_path=Path("pilot-smoke.log"),
    )

    assert summary["checks"] == {
        "api_ready_status": "ok",
        "web_root_ok": True,
        "imports_page_ok": True,
    }
    assert summary["resolved_actor"]["user_id"] == "pilot-navigator"
    assert summary["visible_case_count"] == 1
    assert summary["sample_case_ids"] == ["dr-fhir-smoke-20260325180000"]
    assert summary["review_roundtrip_case_id"] == "dr-fhir-smoke-20260325180000"
    assert summary["import_runs"] == [
        {
            "label": "FHIR import run",
            "run_id": 88,
            "status": "completed",
            "source_format": "fhir-diagnostic-report",
            "processed": 1,
            "failed": 0,
            "failure_counts": {},
            "imported_sites": ["Demo Hospital"],
            "status_code": None,
            "detail": None,
        }
    ]

    markdown = summarize.render_markdown(summary)
    assert "[#123456789](https://github.com/example/repo/actions/runs/123456789)" in markdown
    assert "`pilot-smoke-summary-proxy-demo-fhir-smoke`" in markdown
    assert "- Duration seconds: `187`" in markdown
    assert "- Started at: `2026-03-25T19:10:00Z`" in markdown
    assert "- Finished at: `2026-03-25T19:13:07Z`" in markdown
    assert "run `#88` status `completed` format `fhir-diagnostic-report`" in markdown


def test_build_summary_extracts_failure_details_and_alternate_actor() -> None:
    summarize = _load_summary_module()
    log_text = """
Waiting for API readiness at http://localhost:8000/api/v1/health/ready
API ready: ok

Resolved actor:
{
  "display_name": "Pilot Navigator",
  "role": "pdac-navigator",
  "site_scope": [
    "Demo Hospital"
  ],
  "user_id": "pilot-navigator"
}

Resolved alternate actor:
{
  "display_name": "Pilot Navigator Audit Alt",
  "role": "pdac-navigator",
  "site_scope": [
    "Demo Hospital"
  ],
  "user_id": "pilot-navigator-audit-alt"
}
FHIR unsupported payload run summary:
{
  "detail": "FHIR import payload must be a DiagnosticReport resource or Bundle.",
  "run_id": 90,
  "status_code": 400
}
FHIR unsupported payload run detail:
{
  "failed": 1,
  "failure_counts": {
    "unsupported_payload": 1
  },
  "imported_sites": [],
  "processed": 0,
  "run_id": 90,
  "source_format": "fhir-diagnostic-report",
  "status": "failed"
}
HL7 parse failure run summary:
{
  "detail": "HL7 ORU import did not contain any OBR report groups.",
  "run_id": 91,
  "status_code": 400
}
HL7 parse failure run detail:
{
  "failed": 1,
  "failure_counts": {
    "parse_error": 1
  },
  "imported_sites": [],
  "processed": 0,
  "run_id": 91,
  "source_format": "hl7-oru",
  "status": "failed"
}

Verified persisted adapter failure runs #90 (unsupported_payload) and #91 (parse_error).
""".strip()

    summary = summarize.build_summary(
        log_text=log_text,
        workflow_context={"name": "Pilot Smoke"},
        log_path=Path("pilot-smoke.log"),
    )

    assert summary["resolved_alternate_actor"]["user_id"] == "pilot-navigator-audit-alt"
    assert summary["import_runs"] == [
        {
            "label": "FHIR unsupported payload run",
            "run_id": 90,
            "status": "failed",
            "source_format": "fhir-diagnostic-report",
            "processed": 0,
            "failed": 1,
            "failure_counts": {"unsupported_payload": 1},
            "imported_sites": [],
            "status_code": 400,
            "detail": "FHIR import payload must be a DiagnosticReport resource or Bundle.",
        },
        {
            "label": "HL7 parse failure run",
            "run_id": 91,
            "status": "failed",
            "source_format": "hl7-oru",
            "processed": 0,
            "failed": 1,
            "failure_counts": {"parse_error": 1},
            "imported_sites": [],
            "status_code": 400,
            "detail": "HL7 ORU import did not contain any OBR report groups.",
        },
    ]
