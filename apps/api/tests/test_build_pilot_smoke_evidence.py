from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_SCRIPT = ROOT / "scripts" / "build_pilot_smoke_evidence.py"


def _load_evidence_module():
    spec = importlib.util.spec_from_file_location("build_pilot_smoke_evidence", EVIDENCE_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _summary(
    *,
    run_id: str,
    run_url: str,
    job_name: str,
    job_scope: str,
    dispatch_scope: str,
    summary_artifact_name: str,
    log_artifact_name: str,
    smoke_command: str,
    source_format: str,
    started_at: str,
    finished_at: str,
    duration_seconds: str,
    visible_case_count: int,
    review_roundtrip_case_id: str,
) -> dict[str, object]:
    return {
        "workflow": {
            "name": "Pilot Smoke",
            "job_name": job_name,
            "job_scope": job_scope,
            "dispatch_scope": dispatch_scope,
            "smoke_command": smoke_command,
            "log_artifact_name": log_artifact_name,
            "summary_artifact_name": summary_artifact_name,
            "event_name": "workflow_dispatch",
            "outcome": "success",
            "exit_code": "0",
            "duration_seconds": duration_seconds,
            "started_at": started_at,
            "finished_at": finished_at,
            "summary_generated_at": finished_at,
            "run_id": run_id,
            "run_attempt": "1",
            "run_url": run_url,
            "repository": "example/repo",
            "ref": "refs/heads/main",
            "sha": "abc123",
        },
        "visible_case_count": visible_case_count,
        "sample_case_ids": [review_roundtrip_case_id],
        "review_roundtrip_case_id": review_roundtrip_case_id,
        "import_runs": [
            {
                "label": f"{source_format} import run",
                "run_id": 88,
                "status": "completed",
                "source_format": source_format,
                "processed": 1,
                "failed": 0,
                "failure_counts": {},
                "imported_sites": ["Demo Hospital"],
                "status_code": None,
                "detail": None,
            }
        ],
    }


def test_build_evidence_bundle_confirms_fhir_and_records_manual_hl7_decision() -> None:
    evidence = _load_evidence_module()
    summaries = [
        _summary(
            run_id="2001",
            run_url="https://github.com/example/repo/actions/runs/2001",
            job_name="Proxy Demo FHIR Smoke",
            job_scope="fhir-success",
            dispatch_scope="fhir-success-only",
            summary_artifact_name="pilot-smoke-summary-proxy-demo-fhir-smoke",
            log_artifact_name="pilot-smoke-proxy-demo-fhir-smoke",
            smoke_command="make pilot-proxy-demo-fhir-smoke",
            source_format="fhir-diagnostic-report",
            started_at="2026-03-25T20:00:00Z",
            finished_at="2026-03-25T20:03:07Z",
            duration_seconds="187",
            visible_case_count=1,
            review_roundtrip_case_id="dr-fhir-proxy",
        ),
        _summary(
            run_id="2001",
            run_url="https://github.com/example/repo/actions/runs/2001",
            job_name="Header Demo FHIR Smoke",
            job_scope="fhir-success",
            dispatch_scope="fhir-success-only",
            summary_artifact_name="pilot-smoke-summary-header-demo-fhir-smoke",
            log_artifact_name="pilot-smoke-header-demo-fhir-smoke",
            smoke_command="make pilot-header-demo-fhir-smoke",
            source_format="fhir-diagnostic-report",
            started_at="2026-03-25T20:00:02Z",
            finished_at="2026-03-25T20:03:11Z",
            duration_seconds="189",
            visible_case_count=1,
            review_roundtrip_case_id="dr-fhir-header",
        ),
    ]

    bundle = evidence.build_evidence_bundle(
        summaries=summaries,
        summary_paths=[Path("proxy/pilot-smoke-summary.json"), Path("header/pilot-smoke-summary.json")],
        hl7_decision="keep-manual",
        hl7_rationales=["HL7 stays manual until hosted trial evidence is intentionally reviewed."],
    )

    assert bundle["phase_status"]["hosted_fhir_confirmed"] is True
    assert bundle["phase_status"]["primary_fhir_run_id"] == "2001"
    assert bundle["phase_status"]["hl7_hosting_mode"] == "manual_only"
    assert bundle["phase_status"]["phase_complete"] is True
    assert (
        "Hosted FHIR smoke confirmation:"
        in bundle["copyable_snippets"]["fhir_handoff"]
    )
    assert (
        "Hosted HL7 decision: keep manual-only"
        in bundle["copyable_snippets"]["hl7_handoff"]
    )

    markdown = evidence.render_markdown(bundle)
    assert "[#2001](https://github.com/example/repo/actions/runs/2001)" in markdown
    assert "- Hosted FHIR confirmed: `True`" in markdown
    assert "- HL7 hosting mode: `manual_only`" in markdown
    assert "pilot-smoke-summary-proxy-demo-fhir-smoke" in markdown


def test_discover_summary_paths_and_bundle_hl7_trial_from_downloaded_artifacts(tmp_path: Path) -> None:
    evidence = _load_evidence_module()
    artifact_root = tmp_path / "pilot-smoke-artifacts"
    proxy_dir = artifact_root / "pilot-smoke-summary-proxy-demo-hl7-smoke"
    header_dir = artifact_root / "pilot-smoke-summary-header-demo-hl7-smoke"
    proxy_dir.mkdir(parents=True)
    header_dir.mkdir(parents=True)

    proxy_summary = _summary(
        run_id="2002",
        run_url="https://github.com/example/repo/actions/runs/2002",
        job_name="Proxy Demo HL7 Smoke",
        job_scope="hl7-success",
        dispatch_scope="hl7-success-only",
        summary_artifact_name="pilot-smoke-summary-proxy-demo-hl7-smoke",
        log_artifact_name="pilot-smoke-proxy-demo-hl7-smoke",
        smoke_command="make pilot-proxy-demo-hl7-smoke",
        source_format="hl7-oru",
        started_at="2026-03-25T21:00:00Z",
        finished_at="2026-03-25T21:03:40Z",
        duration_seconds="220",
        visible_case_count=1,
        review_roundtrip_case_id="oru-proxy",
    )
    header_summary = _summary(
        run_id="2002",
        run_url="https://github.com/example/repo/actions/runs/2002",
        job_name="Header Demo HL7 Smoke",
        job_scope="hl7-success",
        dispatch_scope="hl7-success-only",
        summary_artifact_name="pilot-smoke-summary-header-demo-hl7-smoke",
        log_artifact_name="pilot-smoke-header-demo-hl7-smoke",
        smoke_command="make pilot-header-demo-hl7-smoke",
        source_format="hl7-oru",
        started_at="2026-03-25T21:00:01Z",
        finished_at="2026-03-25T21:03:55Z",
        duration_seconds="234",
        visible_case_count=1,
        review_roundtrip_case_id="oru-header",
    )

    (proxy_dir / "pilot-smoke-summary.json").write_text(
        json.dumps(proxy_summary),
        encoding="utf-8",
    )
    (header_dir / "pilot-smoke-summary.json").write_text(
        json.dumps(header_summary),
        encoding="utf-8",
    )

    discovered = evidence.discover_summary_paths([], [str(artifact_root)])

    assert [path.parent.name for path in discovered] == [
        "pilot-smoke-summary-header-demo-hl7-smoke",
        "pilot-smoke-summary-proxy-demo-hl7-smoke",
    ]

    loaded = [json.loads(path.read_text(encoding="utf-8")) for path in discovered]
    bundle = evidence.build_evidence_bundle(
        summaries=loaded,
        summary_paths=discovered,
        hl7_decision="promote-default",
        hl7_rationales=["Hosted HL7 trial matched the FHIR-only path closely enough to promote."],
    )

    assert bundle["phase_status"]["hosted_hl7_trial_recorded"] is True
    assert bundle["phase_status"]["primary_hl7_run_id"] == "2002"
    assert bundle["phase_status"]["hl7_hosting_mode"] == "default"

    markdown = evidence.render_markdown(bundle)
    assert "[#2002](https://github.com/example/repo/actions/runs/2002)" in markdown
    assert "Hosted HL7 decision: promote into the default hosted matrix" in markdown
