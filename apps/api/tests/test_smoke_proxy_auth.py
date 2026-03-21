from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[3]
SMOKE_SCRIPT = ROOT / "scripts" / "smoke_proxy_auth.py"


def _load_smoke_module():
    spec = importlib.util.spec_from_file_location("smoke_proxy_auth", SMOKE_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_header_auth_headers_includes_identity_fields() -> None:
    smoke = _load_smoke_module()

    headers = smoke.build_header_auth_headers(
        user_id_header_name="X-User-ID",
        display_name_header_name="X-User-Name",
        role_header_name="X-User-Role",
        sites_header_name="X-User-Sites",
        user_id="pilot-navigator",
        display_name="Pilot Navigator",
        role_value="navigator",
        sites="Demo Hospital, North Clinic",
    )

    assert headers == {
        "X-User-ID": "pilot-navigator",
        "X-User-Name": "Pilot Navigator",
        "X-User-Role": "navigator",
        "X-User-Sites": "Demo Hospital, North Clinic",
    }


def test_load_demo_reports_applies_run_id_and_actor_site_scope(tmp_path: Path) -> None:
    smoke = _load_smoke_module()
    demo_file = tmp_path / "reports.jsonl"
    demo_file.write_text(
        (
            '{"report_id":"R-001","case_id":"C-001","site":"Original Site",'
            '"report_text":"Suspicious pancreatic lesion.","modality":"CT"}\n'
        ),
        encoding="utf-8",
    )

    reports = smoke.load_demo_reports(
        auth_actor={"site_scope": ["Demo Hospital"]},
        demo_file=demo_file,
        run_id="smoke-123",
    )

    assert reports == [
        {
            "report_id": "R-001-smoke-123",
            "case_id": "C-001-smoke-123",
            "site": "Demo Hospital",
            "report_text": "Suspicious pancreatic lesion.",
            "modality": "CT",
        }
    ]


def test_override_report_sites_replaces_site_without_mutating_input() -> None:
    smoke = _load_smoke_module()
    original = [
        {"report_id": "R-001", "case_id": "C-001", "site": "Demo Hospital"},
        {"report_id": "R-002", "case_id": "C-002", "site": "Demo Hospital"},
    ]

    updated = smoke.override_report_sites(original, "Out of Scope Site")

    assert updated == [
        {"report_id": "R-001", "case_id": "C-001", "site": "Out of Scope Site"},
        {"report_id": "R-002", "case_id": "C-002", "site": "Out of Scope Site"},
    ]
    assert original == [
        {"report_id": "R-001", "case_id": "C-001", "site": "Demo Hospital"},
        {"report_id": "R-002", "case_id": "C-002", "site": "Demo Hospital"},
    ]


def test_build_validation_failure_demo_payload_uses_run_id_and_site_scope() -> None:
    smoke = _load_smoke_module()

    payload = smoke.build_validation_failure_demo_payload(
        run_id="smoke-321",
        site_scope=["North Clinic"],
    )

    assert payload == (
        b'{"report_id":"R-VAL-smoke-321","case_id":"C-VAL-smoke-321","site":"North Clinic"}\n'
    )


def test_build_parse_failure_demo_payload_uses_run_id() -> None:
    smoke = _load_smoke_module()

    payload = smoke.build_parse_failure_demo_payload(run_id="smoke-654")

    assert payload == b'{"report_id":"R-PARSE-smoke-654","case_id":"C-PARSE-smoke-654"\n'


def test_build_fhir_unsupported_demo_payload_uses_run_id() -> None:
    smoke = _load_smoke_module()

    payload = smoke.build_fhir_unsupported_demo_payload(run_id="smoke-987")

    assert payload == {
        "resourceType": "Observation",
        "id": "obs-unsupported-smoke-987",
    }


def test_build_hl7_parse_failure_demo_payload_uses_run_id_and_site_scope() -> None:
    smoke = _load_smoke_module()

    payload = smoke.build_hl7_parse_failure_demo_payload(
        run_id="smoke-222",
        site_scope=["North Clinic"],
    )

    assert payload == "\r".join(
        [
            "MSH|^~\\&|RADSYS|North Clinic|PS|PS|20260319130000||ORU^R01|MSG-PARSE-smoke-222|P|2.5",
            "PID|1||PAT-PARSE-smoke-222^^^MRN||Doe^Jamie",
        ]
    )


def test_resolve_audit_alt_identity_defaults_to_distinct_scoped_actor() -> None:
    smoke = _load_smoke_module()

    identity = smoke.resolve_audit_alt_identity(
        SimpleNamespace(
            user_id="pilot-navigator",
            display_name="Pilot Navigator",
            role_value="pdac-navigator",
            sites="Demo Hospital",
            groups="rad-team",
            audit_alt_user_id=None,
            audit_alt_display_name=None,
            audit_alt_role_value=None,
            audit_alt_sites=None,
            audit_alt_groups=None,
        )
    )

    assert identity == {
        "user_id": "pilot-navigator-audit-alt",
        "display_name": "Pilot Navigator Audit Alt",
        "role_value": "pdac-navigator",
        "sites": "Demo Hospital",
        "groups": "rad-team",
    }


def test_assert_import_run_accepts_matching_summary_and_detail() -> None:
    smoke = _load_smoke_module()

    run_id = smoke._assert_import_run(
        import_summary={
            "run_id": 7,
            "processed": 2,
            "created": 2,
            "updated": 0,
            "failed": 0,
            "case_ids": ["C-1-smoke", "C-2-smoke"],
            "report_ids": ["R-1-smoke", "R-2-smoke"],
            "source_format": "jsonl",
        },
        import_detail={
            "run_id": 7,
            "status": "completed",
            "processed": 2,
            "failed": 0,
            "source_format": "jsonl",
            "items": [
                {"status": "imported", "case_id": "C-1-smoke", "report_id": "R-1-smoke"},
                {"status": "imported", "case_id": "C-2-smoke", "report_id": "R-2-smoke"},
            ],
        },
        expected_processed=2,
        expected_case_ids=["C-1-smoke", "C-2-smoke"],
        expected_report_ids=["R-1-smoke", "R-2-smoke"],
        expected_source_format="jsonl",
    )

    assert run_id == 7


def test_assert_failed_import_run_accepts_matching_site_scope_rejection_detail() -> None:
    smoke = _load_smoke_module()

    run_id = smoke._assert_failed_import_run(
        failure_summary={
            "run_id": 11,
            "status_code": 403,
            "detail": "Actor 'pilot-navigator' cannot import reports for site(s): Out of Scope Site.",
        },
        import_detail={
            "run_id": 11,
            "status": "failed",
            "processed": 0,
            "failed": 2,
            "source_format": "jsonl",
            "imported_sites": ["Out of Scope Site"],
            "failure_counts": {"site_scope_rejection": 2},
            "items": [
                {
                    "status": "failed",
                    "error_bucket": "site_scope_rejection",
                    "site": "Out of Scope Site",
                    "case_id": "C-1-smoke",
                    "report_id": "R-1-smoke",
                },
                {
                    "status": "failed",
                    "error_bucket": "site_scope_rejection",
                    "site": "Out of Scope Site",
                    "case_id": "C-2-smoke",
                    "report_id": "R-2-smoke",
                },
            ],
        },
        expected_status_code=403,
        expected_source_format="jsonl",
        expected_failure_bucket="site_scope_rejection",
        expected_failed=2,
        expected_imported_sites=["Out of Scope Site"],
        expected_item_count=2,
        expected_case_ids=["C-1-smoke", "C-2-smoke"],
        expected_report_ids=["R-1-smoke", "R-2-smoke"],
        expected_site="Out of Scope Site",
    )

    assert run_id == 11


def test_assert_failed_import_run_accepts_matching_fhir_site_scope_rejection_detail() -> None:
    smoke = _load_smoke_module()

    run_id = smoke._assert_failed_import_run(
        failure_summary={
            "run_id": 12,
            "status_code": 403,
            "detail": "Actor 'pilot-navigator' cannot import reports for site(s): Out of Scope Site.",
        },
        import_detail={
            "run_id": 12,
            "status": "failed",
            "processed": 0,
            "failed": 1,
            "source_format": "fhir-diagnostic-report",
            "imported_sites": ["Out of Scope Site"],
            "failure_counts": {"site_scope_rejection": 1},
            "items": [
                {
                    "status": "failed",
                    "error_bucket": "site_scope_rejection",
                    "site": "Out of Scope Site",
                    "case_id": "dr-fhir-smoke",
                    "report_id": "dr-fhir-smoke",
                }
            ],
        },
        expected_status_code=403,
        expected_source_format="fhir-diagnostic-report",
        expected_failure_bucket="site_scope_rejection",
        expected_failed=1,
        expected_imported_sites=["Out of Scope Site"],
        expected_item_count=1,
        expected_case_ids=["dr-fhir-smoke"],
        expected_report_ids=["dr-fhir-smoke"],
        expected_site="Out of Scope Site",
    )

    assert run_id == 12


def test_assert_failed_import_run_accepts_summary_only_failure_detail_without_items() -> None:
    smoke = _load_smoke_module()

    run_id = smoke._assert_failed_import_run(
        failure_summary={
            "run_id": 13,
            "status_code": 400,
            "detail": "JSONL line 1 is not valid JSON.",
        },
        import_detail={
            "run_id": 13,
            "status": "failed",
            "processed": 0,
            "failed": 1,
            "source_format": "jsonl",
            "imported_sites": [],
            "failure_counts": {"parse_error": 1},
            "items": [],
        },
        expected_status_code=400,
        expected_source_format="jsonl",
        expected_failure_bucket="parse_error",
        expected_failed=1,
        expected_imported_sites=[],
        expected_item_count=0,
    )

    assert run_id == 13


def test_assert_import_run_hidden_responses_accepts_404_and_omitted_recent_run() -> None:
    smoke = _load_smoke_module()

    smoke._assert_import_run_hidden_responses(
        run_id=21,
        detail_status_code=404,
        detail_body={"detail": "Import run not found"},
        list_status_code=200,
        list_body=[{"run_id": 20}, {"run_id": 19}],
        label="Alternate actor audit visibility",
    )


def test_assert_import_run_visible_responses_accepts_visible_detail_and_recent_run() -> None:
    smoke = _load_smoke_module()

    smoke._assert_import_run_visible_responses(
        run_id=22,
        detail_status_code=200,
        detail_body={
            "run_id": 22,
            "actor_user_id": "pilot-navigator",
            "status": "completed",
            "source_format": "jsonl",
        },
        list_status_code=200,
        list_body=[{"run_id": 22}, {"run_id": 21}],
        label="Alternate actor shared visibility",
        expected_actor_user_id="pilot-navigator",
        expected_status="completed",
        expected_source_format="jsonl",
    )


def test_assert_import_run_visible_responses_accepts_failed_visible_detail_and_recent_run() -> None:
    smoke = _load_smoke_module()

    smoke._assert_import_run_visible_responses(
        run_id=23,
        detail_status_code=200,
        detail_body={
            "run_id": 23,
            "actor_user_id": "pilot-navigator",
            "status": "failed",
            "source_format": "jsonl",
            "failure_counts": {"validation_error": 1},
        },
        list_status_code=200,
        list_body=[{"run_id": 24}, {"run_id": 23}],
        label="Alternate actor failed shared visibility",
        expected_actor_user_id="pilot-navigator",
        expected_status="failed",
        expected_source_format="jsonl",
    )


def test_assert_import_run_visible_responses_accepts_failed_adapter_visible_detail_and_recent_run() -> None:
    smoke = _load_smoke_module()

    smoke._assert_import_run_visible_responses(
        run_id=24,
        detail_status_code=200,
        detail_body={
            "run_id": 24,
            "actor_user_id": "pilot-navigator",
            "status": "failed",
            "source_format": "fhir-diagnostic-report",
            "failure_counts": {"unsupported_payload": 1},
        },
        list_status_code=200,
        list_body=[{"run_id": 25}, {"run_id": 24}],
        label="Alternate actor failed FHIR shared visibility",
        expected_actor_user_id="pilot-navigator",
        expected_status="failed",
        expected_source_format="fhir-diagnostic-report",
    )


def test_build_fhir_demo_payload_uses_run_id_and_site_scope() -> None:
    smoke = _load_smoke_module()

    payload, case_ids, report_ids = smoke.build_fhir_demo_payload(
        run_id="smoke-456",
        site_scope=["North Clinic"],
    )

    diagnostic_report = payload["entry"][-1]["resource"]
    organization = payload["entry"][0]["resource"]

    assert organization["name"] == "North Clinic"
    assert diagnostic_report["id"] == "dr-fhir-smoke-456"
    assert diagnostic_report["subject"]["reference"] == "Patient/patient-smoke-456"
    assert diagnostic_report["encounter"]["reference"] == "Encounter/encounter-smoke-456"
    assert case_ids == ["dr-fhir-smoke-456"]
    assert report_ids == ["dr-fhir-smoke-456"]


def test_build_hl7_demo_payload_uses_run_id_and_site_scope() -> None:
    smoke = _load_smoke_module()

    payload, case_ids, report_ids = smoke.build_hl7_demo_payload(
        run_id="smoke-789",
        site_scope=["North Clinic"],
    )

    assert "MSH|^~\\&|RADSYS|North Clinic|PS|PS|20260319110000||ORU^R01|MSG-smoke-789|P|2.5" in payload
    assert "PV1|1|O|RAD^^^North Clinic" in payload
    assert "OBR|1|PLAC-smoke-789|R-HL7-smoke-789|CT ABDOMEN^CT Abdomen" in payload
    assert case_ids == ["R-HL7-smoke-789"]
    assert report_ids == ["R-HL7-smoke-789"]


def test_build_identity_payload_uses_keycloak_claim_shape() -> None:
    smoke = _load_smoke_module()

    payload = smoke.build_identity_payload(
        provider_preset="keycloak",
        user_id="pilot-navigator",
        display_name="Pilot Navigator",
        role_value="pdac-navigator",
        sites="Demo Hospital, North Clinic",
        groups="rad-team, import-operators",
    )

    assert payload == {
        "preferred_username": "pilot-navigator",
        "name": "Pilot Navigator",
        "realm_access": {"roles": ["pdac-navigator"]},
        "sites": ["Demo Hospital", "North Clinic"],
        "groups": ["rad-team", "import-operators"],
    }


def test_encode_identity_payload_base64_round_trips_json() -> None:
    smoke = _load_smoke_module()
    payload = {
        "preferred_username": "pilot-navigator",
        "realm_access": {"roles": ["pdac-navigator"]},
        "sites": ["Demo Hospital"],
    }

    encoded = smoke.encode_identity_payload(payload, use_base64=True)
    decoded = json.loads(base64.urlsafe_b64decode(f"{encoded}==").decode("utf-8"))

    assert decoded == payload
