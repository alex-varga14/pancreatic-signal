from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib import error, parse, request

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEMO_FILE = ROOT / "data" / "examples" / "reports.jsonl"
_PRESETS = {
    "generic": {
        "user_id_field": "sub",
        "display_name_field": "name",
        "role_field": "role",
        "sites_field": "sites",
        "groups_field": "groups",
    },
    "authentik": {
        "user_id_field": "preferred_username",
        "display_name_field": "name",
        "role_field": "role",
        "sites_field": "sites",
        "groups_field": "groups",
    },
    "keycloak": {
        "user_id_field": "preferred_username",
        "display_name_field": "name",
        "role_field": "realm_access.roles",
        "sites_field": "sites",
        "groups_field": "groups",
    },
    "oauth2-proxy": {
        "user_id_field": "email",
        "display_name_field": "name",
        "role_field": "role",
        "sites_field": "sites",
        "groups_field": "groups",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Exercise trusted proxy or header auth against a running Pancreatic Signal stack.",
    )
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL without /api/v1.")
    parser.add_argument("--web-url", default="http://localhost:3000", help="Optional web base URL to smoke.")
    parser.add_argument(
        "--auth-mode",
        choices=("proxy", "header"),
        default="proxy",
        help="Whether to send a trusted identity envelope or field-level identity headers.",
    )
    parser.add_argument(
        "--provider-preset",
        choices=sorted(_PRESETS),
        default="generic",
        help="Trusted identity provider preset used to shape the payload in proxy mode.",
    )
    parser.add_argument(
        "--header-name",
        default="X-Trusted-Identity",
        help="Trusted identity header name used in proxy mode.",
    )
    parser.add_argument("--user-id-header-name", default="X-User-ID", help="User ID header name in header mode.")
    parser.add_argument(
        "--display-name-header-name",
        default="X-User-Name",
        help="Display name header name in header mode.",
    )
    parser.add_argument("--role-header-name", default="X-User-Role", help="Role header name in header mode.")
    parser.add_argument("--sites-header-name", default="X-User-Sites", help="Site scope header name in header mode.")
    parser.add_argument("--user-id", default="smoke-reviewer", help="User identifier claim value.")
    parser.add_argument("--display-name", default="Smoke Reviewer", help="Display name claim value.")
    parser.add_argument(
        "--role-value",
        default="reviewer",
        help="Raw role claim value written into the trusted identity payload.",
    )
    parser.add_argument(
        "--sites",
        default="Demo Hospital",
        help="Comma-separated site scope to embed in the payload.",
    )
    parser.add_argument(
        "--groups",
        default="",
        help="Optional comma-separated groups claim value.",
    )
    parser.add_argument(
        "--base64",
        action="store_true",
        help="Send the trusted identity payload as base64url-encoded JSON.",
    )
    parser.add_argument(
        "--check-web",
        action="store_true",
        help="Wait for the web root and require an HTTP 200 response.",
    )
    parser.add_argument(
        "--check-imports-page",
        action="store_true",
        help="Wait for the web import workspace and require an HTTP 200 response.",
    )
    parser.add_argument(
        "--check-cases",
        action="store_true",
        help="Request /api/v1/cases and print visible case information.",
    )
    seed_group = parser.add_mutually_exclusive_group()
    seed_group.add_argument(
        "--seed-demo",
        action="store_true",
        help="Seed a live stack with the bundled demo reports via /api/v1/triage/batch.",
    )
    seed_group.add_argument(
        "--import-demo",
        action="store_true",
        help="Import the bundled demo reports via /api/v1/imports/reports and verify the audit trail.",
    )
    seed_group.add_argument(
        "--import-shared-visibility",
        action="store_true",
        help="Import the bundled demo reports, verify the owner can inspect the successful run, and confirm an alternate scoped actor can access it.",
    )
    seed_group.add_argument(
        "--import-adapter-shared-visibility",
        action="store_true",
        help="Import built-in FHIR and HL7 demo payloads, verify the owner can inspect both successful runs, and confirm an alternate scoped actor can access them.",
    )
    seed_group.add_argument(
        "--import-fhir-demo",
        action="store_true",
        help="Import a built-in FHIR DiagnosticReport bundle and verify the audit trail.",
    )
    seed_group.add_argument(
        "--import-hl7-demo",
        action="store_true",
        help="Import a built-in HL7 ORU payload and verify the audit trail.",
    )
    seed_group.add_argument(
        "--import-demo-site-rejection",
        action="store_true",
        help="Import the bundled demo reports with an out-of-scope site and verify the persisted site-scope rejection audit trail.",
    )
    seed_group.add_argument(
        "--import-audit-visibility",
        action="store_true",
        help="Import the bundled demo reports with an out-of-scope site, verify the owner can inspect the failed run, and confirm an alternate actor cannot access it.",
    )
    seed_group.add_argument(
        "--import-failed-shared-visibility",
        action="store_true",
        help="Submit a validation-failing report upload, verify the owner can inspect the failed run, and confirm an alternate scoped actor can access it.",
    )
    seed_group.add_argument(
        "--import-adapter-failed-shared-visibility",
        action="store_true",
        help="Submit unsupported FHIR and malformed HL7 adapter payloads, verify the owner can inspect both failed runs, and confirm an alternate scoped actor can access them.",
    )
    seed_group.add_argument(
        "--import-demo-parse-validation-failure",
        action="store_true",
        help="Submit malformed and validation-failing report uploads and verify persisted parse_error plus validation_error audit trails.",
    )
    seed_group.add_argument(
        "--import-adapter-failures",
        action="store_true",
        help="Submit unsupported FHIR and malformed HL7 payloads and verify persisted adapter-specific failure audit trails.",
    )
    parser.add_argument(
        "--demo-file",
        default=str(DEFAULT_DEMO_FILE),
        help="Path to a JSONL report file to use with --seed-demo, --import-demo, or --import-shared-visibility.",
    )
    parser.add_argument(
        "--rejection-site",
        default="Out of Scope Site",
        help="Site value to apply when exercising --import-demo-site-rejection or --import-audit-visibility.",
    )
    parser.add_argument(
        "--audit-alt-user-id",
        default=None,
        help="Optional user ID for the alternate actor used by shared-visibility or audit-visibility smoke modes.",
    )
    parser.add_argument(
        "--audit-alt-display-name",
        default=None,
        help="Optional display name for the alternate actor used by shared-visibility or audit-visibility smoke modes.",
    )
    parser.add_argument(
        "--audit-alt-role-value",
        default=None,
        help="Optional role claim value for the alternate actor used by shared-visibility or audit-visibility smoke modes.",
    )
    parser.add_argument(
        "--audit-alt-sites",
        default=None,
        help="Optional comma-separated site scope for the alternate actor used by shared-visibility or audit-visibility smoke modes.",
    )
    parser.add_argument(
        "--audit-alt-groups",
        default=None,
        help="Optional comma-separated groups claim value for the alternate actor used by shared-visibility or audit-visibility smoke modes.",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Optional run identifier suffix; defaults to a UTC timestamp.",
    )
    parser.add_argument(
        "--review-action",
        default="in_review",
        help="Reviewer action to post after seeding or listing cases. Set to '' to skip.",
    )
    parser.add_argument(
        "--review-note",
        default="Pilot proxy smoke check.",
        help="Review action note to persist during the round-trip check.",
    )
    parser.add_argument(
        "--wait-seconds",
        type=float,
        default=60.0,
        help="How long to wait for health and optional web checks.",
    )
    parser.add_argument(
        "--skip-review",
        action="store_true",
        help="Skip the reviewer round-trip even when a review action is configured.",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    smoke_run_id = args.run_id or datetime.now(UTC).strftime("smoke-%Y%m%d%H%M%S")
    auth_headers = build_auth_headers(args)
    review_action = (
        ""
        if (
            args.skip_review
            or args.import_demo_site_rejection
            or args.import_audit_visibility
            or args.import_failed_shared_visibility
            or args.import_adapter_failed_shared_visibility
            or args.import_demo_parse_validation_failure
            or args.import_adapter_failures
        )
        else args.review_action
    )

    print(f"Waiting for API readiness at {base_url}/api/v1/health/ready")
    ready = wait_for_json(
        f"{base_url}/api/v1/health/ready",
        timeout_seconds=args.wait_seconds,
    )
    print(f"API ready: {ready.get('status')}")

    if args.check_web:
        print(f"Waiting for web root at {args.web_url}")
        wait_for_http_ok(args.web_url, timeout_seconds=args.wait_seconds)
        print("Web root responded with HTTP 200.")

    if args.check_imports_page:
        imports_url = f"{args.web_url.rstrip('/')}/imports"
        print(f"Waiting for web import workspace at {imports_url}")
        wait_for_http_ok(imports_url, timeout_seconds=args.wait_seconds)
        print("Import workspace responded with HTTP 200.")

    auth_me = fetch_json(
        f"{base_url}/api/v1/auth/me",
        headers=auth_headers,
    )

    print()
    print("Resolved actor:")
    print(json.dumps(auth_me, indent=2, sort_keys=True))

    seeded_case_ids: list[str] = []
    prepared_reports: list[dict[str, object]] = []
    case_query_hint = smoke_run_id if any(
        [
            args.seed_demo,
            args.import_demo,
            args.import_shared_visibility,
            args.import_adapter_shared_visibility,
            args.import_fhir_demo,
            args.import_hl7_demo,
            args.import_demo_site_rejection,
            args.import_audit_visibility,
            args.import_failed_shared_visibility,
            args.import_adapter_failed_shared_visibility,
            args.import_demo_parse_validation_failure,
            args.import_adapter_failures,
        ]
    ) else ""
    expect_no_visible_cases = False

    if (
        args.seed_demo
        or args.import_demo
        or args.import_shared_visibility
        or args.import_demo_site_rejection
        or args.import_audit_visibility
        or args.import_demo_parse_validation_failure
    ):
        prepared_reports = load_demo_reports(
            auth_actor=auth_me,
            demo_file=Path(args.demo_file),
            run_id=smoke_run_id,
        )

    if args.seed_demo:
        seeded_case_ids = seed_demo_reports(
            base_url=base_url,
            reports=prepared_reports,
        )
        print()
        print(f"Seeded {len(seeded_case_ids)} demo case(s) with run id {smoke_run_id}.")

    if args.import_demo or args.import_shared_visibility:
        if not auth_me["capabilities"]["can_import_reports"]:
            print("Resolved actor cannot import reports; choose an analyst, navigator, or admin identity.", file=sys.stderr)
            return 1
        import_summary, import_detail = import_demo_reports(
            base_url=base_url,
            auth_headers=auth_headers,
            demo_file=Path(args.demo_file),
            reports=prepared_reports,
        )
        import_run_id = _assert_import_run(
            import_summary=import_summary,
            import_detail=import_detail,
            expected_processed=len(prepared_reports),
            expected_case_ids=[str(report["case_id"]) for report in prepared_reports],
            expected_report_ids=[str(report["report_id"]) for report in prepared_reports],
            expected_source_format="jsonl",
        )
        seeded_case_ids = [str(case_id) for case_id in import_summary["case_ids"]]
        print()
        print(f"Imported {len(seeded_case_ids)} demo case(s) through /api/v1/imports/reports.")
        print(f"Verified persisted import run #{import_run_id}.")

        if args.import_shared_visibility:
            alternate_identity, alternate_headers, _ = resolve_alternate_actor(
                args=args,
                base_url=base_url,
            )
            _assert_import_run_visible_to_actor(
                base_url=base_url,
                auth_headers=alternate_headers,
                run_id=import_run_id,
                label="Alternate actor shared visibility",
                expected_actor_user_id=auth_me["user_id"],
                expected_status="completed",
            )
            print()
            print(
                f"Verified alternate actor {alternate_identity['user_id']} can access successful import run #{import_run_id}."
            )

    if args.import_fhir_demo:
        if not auth_me["capabilities"]["can_import_reports"]:
            print("Resolved actor cannot import reports; choose an analyst, navigator, or admin identity.", file=sys.stderr)
            return 1
        fhir_payload, expected_case_ids, expected_report_ids = build_fhir_demo_payload(
            run_id=smoke_run_id,
            site_scope=auth_me.get("site_scope"),
        )
        import_summary, import_detail = import_fhir_demo_payload(
            base_url=base_url,
            auth_headers=auth_headers,
            payload=fhir_payload,
        )
        import_run_id = _assert_import_run(
            import_summary=import_summary,
            import_detail=import_detail,
            expected_processed=len(expected_case_ids),
            expected_case_ids=expected_case_ids,
            expected_report_ids=expected_report_ids,
            expected_source_format="fhir-diagnostic-report",
        )
        seeded_case_ids = expected_case_ids
        print()
        print(f"Imported {len(seeded_case_ids)} demo case(s) through /api/v1/imports/fhir/diagnostic-reports.")
        print(f"Verified persisted FHIR import run #{import_run_id}.")

    if args.import_hl7_demo:
        if not auth_me["capabilities"]["can_import_reports"]:
            print("Resolved actor cannot import reports; choose an analyst, navigator, or admin identity.", file=sys.stderr)
            return 1
        hl7_payload, expected_case_ids, expected_report_ids = build_hl7_demo_payload(
            run_id=smoke_run_id,
            site_scope=auth_me.get("site_scope"),
        )
        import_summary, import_detail = import_hl7_demo_payload(
            base_url=base_url,
            auth_headers=auth_headers,
            payload=hl7_payload,
        )
        import_run_id = _assert_import_run(
            import_summary=import_summary,
            import_detail=import_detail,
            expected_processed=len(expected_case_ids),
            expected_case_ids=expected_case_ids,
            expected_report_ids=expected_report_ids,
            expected_source_format="hl7-oru",
        )
        seeded_case_ids = expected_case_ids
        print()
        print(f"Imported {len(seeded_case_ids)} demo case(s) through /api/v1/imports/hl7/oru.")
        print(f"Verified persisted HL7 import run #{import_run_id}.")

    if args.import_adapter_shared_visibility:
        if not auth_me["capabilities"]["can_import_reports"]:
            print("Resolved actor cannot import reports; choose an analyst, navigator, or admin identity.", file=sys.stderr)
            return 1

        alternate_identity, alternate_headers, _ = resolve_alternate_actor(
            args=args,
            base_url=base_url,
        )

        fhir_payload, fhir_case_ids, fhir_report_ids = build_fhir_demo_payload(
            run_id=smoke_run_id,
            site_scope=auth_me.get("site_scope"),
        )
        fhir_summary, fhir_detail = import_fhir_demo_payload(
            base_url=base_url,
            auth_headers=auth_headers,
            payload=fhir_payload,
        )
        fhir_run_id = _assert_import_run(
            import_summary=fhir_summary,
            import_detail=fhir_detail,
            expected_processed=len(fhir_case_ids),
            expected_case_ids=fhir_case_ids,
            expected_report_ids=fhir_report_ids,
            expected_source_format="fhir-diagnostic-report",
        )
        _assert_import_run_visible_to_actor(
            base_url=base_url,
            auth_headers=alternate_headers,
            run_id=fhir_run_id,
            label="Alternate actor FHIR shared visibility",
            expected_actor_user_id=auth_me["user_id"],
            expected_status="completed",
            expected_source_format="fhir-diagnostic-report",
        )

        hl7_payload, hl7_case_ids, hl7_report_ids = build_hl7_demo_payload(
            run_id=smoke_run_id,
            site_scope=auth_me.get("site_scope"),
        )
        hl7_summary, hl7_detail = import_hl7_demo_payload(
            base_url=base_url,
            auth_headers=auth_headers,
            payload=hl7_payload,
        )
        hl7_run_id = _assert_import_run(
            import_summary=hl7_summary,
            import_detail=hl7_detail,
            expected_processed=len(hl7_case_ids),
            expected_case_ids=hl7_case_ids,
            expected_report_ids=hl7_report_ids,
            expected_source_format="hl7-oru",
        )
        _assert_import_run_visible_to_actor(
            base_url=base_url,
            auth_headers=alternate_headers,
            run_id=hl7_run_id,
            label="Alternate actor HL7 shared visibility",
            expected_actor_user_id=auth_me["user_id"],
            expected_status="completed",
            expected_source_format="hl7-oru",
        )

        seeded_case_ids = [*fhir_case_ids, *hl7_case_ids]
        print()
        print(
            f"Verified structured shared visibility for FHIR run #{fhir_run_id} "
            f"and HL7 run #{hl7_run_id}."
        )

    if args.import_demo_site_rejection or args.import_audit_visibility:
        if not auth_me["capabilities"]["can_import_reports"]:
            print("Resolved actor cannot import reports; choose an analyst, navigator, or admin identity.", file=sys.stderr)
            return 1
        rejected_reports = override_report_sites(prepared_reports, args.rejection_site)
        failure_summary, import_detail = import_demo_reports_expect_site_scope_rejection(
            base_url=base_url,
            auth_headers=auth_headers,
            demo_file=Path(args.demo_file),
            reports=rejected_reports,
        )
        import_run_id = _assert_failed_import_run(
            failure_summary=failure_summary,
            import_detail=import_detail,
            expected_status_code=403,
            expected_source_format="jsonl",
            expected_failure_bucket="site_scope_rejection",
            expected_failed=len(rejected_reports),
            expected_imported_sites=[args.rejection_site],
            expected_item_count=len(rejected_reports),
            expected_case_ids=[str(report["case_id"]) for report in rejected_reports],
            expected_report_ids=[str(report["report_id"]) for report in rejected_reports],
            expected_site=args.rejection_site,
        )
        expect_no_visible_cases = True
        print()
        print(f"Verified persisted site-scope rejection run #{import_run_id} for {len(rejected_reports)} demo report(s).")

        if args.import_audit_visibility:
            alternate_identity, alternate_headers, _ = resolve_alternate_actor(
                args=args,
                base_url=base_url,
            )
            _assert_import_run_hidden_from_actor(
                base_url=base_url,
                auth_headers=alternate_headers,
                run_id=import_run_id,
                label="Alternate actor audit visibility",
            )
            print()
            print(
                f"Verified alternate actor {alternate_identity['user_id']} cannot access failed import run #{import_run_id}."
            )

    if args.import_demo_parse_validation_failure:
        if not auth_me["capabilities"]["can_import_reports"]:
            print("Resolved actor cannot import reports; choose an analyst, navigator, or admin identity.", file=sys.stderr)
            return 1

        validation_payload = build_validation_failure_demo_payload(
            run_id=smoke_run_id,
            site_scope=auth_me.get("site_scope"),
        )
        validation_summary, validation_detail = import_report_payload_expect_failure(
            base_url=base_url,
            auth_headers=auth_headers,
            filename="validation-failure.jsonl",
            content_type="application/x-ndjson",
            payload_bytes=validation_payload,
            expected_status_code=400,
            label="Validation failure run",
        )
        validation_run_id = _assert_failed_import_run(
            failure_summary=validation_summary,
            import_detail=validation_detail,
            expected_status_code=400,
            expected_source_format="jsonl",
            expected_failure_bucket="validation_error",
            expected_failed=1,
            expected_imported_sites=[],
            expected_item_count=0,
        )

        parse_payload = build_parse_failure_demo_payload(run_id=smoke_run_id)
        parse_summary, parse_detail = import_report_payload_expect_failure(
            base_url=base_url,
            auth_headers=auth_headers,
            filename="parse-failure.jsonl",
            content_type="application/x-ndjson",
            payload_bytes=parse_payload,
            expected_status_code=400,
            label="Parse failure run",
        )
        parse_run_id = _assert_failed_import_run(
            failure_summary=parse_summary,
            import_detail=parse_detail,
            expected_status_code=400,
            expected_source_format="jsonl",
            expected_failure_bucket="parse_error",
            expected_failed=1,
            expected_imported_sites=[],
            expected_item_count=0,
        )

        expect_no_visible_cases = True
        print()
        print(
            f"Verified persisted malformed upload runs #{validation_run_id} (validation_error) "
            f"and #{parse_run_id} (parse_error)."
        )

    if args.import_failed_shared_visibility:
        if not auth_me["capabilities"]["can_import_reports"]:
            print("Resolved actor cannot import reports; choose an analyst, navigator, or admin identity.", file=sys.stderr)
            return 1

        validation_payload = build_validation_failure_demo_payload(
            run_id=smoke_run_id,
            site_scope=auth_me.get("site_scope"),
        )
        validation_summary, validation_detail = import_report_payload_expect_failure(
            base_url=base_url,
            auth_headers=auth_headers,
            filename="validation-failure-shared-visibility.jsonl",
            content_type="application/x-ndjson",
            payload_bytes=validation_payload,
            expected_status_code=400,
            label="Failed shared-visibility validation run",
        )
        validation_run_id = _assert_failed_import_run(
            failure_summary=validation_summary,
            import_detail=validation_detail,
            expected_status_code=400,
            expected_source_format="jsonl",
            expected_failure_bucket="validation_error",
            expected_failed=1,
            expected_imported_sites=[],
            expected_item_count=0,
        )

        alternate_identity, alternate_headers, _ = resolve_alternate_actor(
            args=args,
            base_url=base_url,
        )
        _assert_import_run_visible_to_actor(
            base_url=base_url,
            auth_headers=alternate_headers,
            run_id=validation_run_id,
            label="Alternate actor failed shared visibility",
            expected_actor_user_id=auth_me["user_id"],
            expected_status="failed",
            expected_source_format="jsonl",
        )

        expect_no_visible_cases = True
        print()
        print(
            f"Verified alternate actor {alternate_identity['user_id']} can access "
            f"failed validation run #{validation_run_id}."
        )

    if args.import_adapter_failed_shared_visibility:
        if not auth_me["capabilities"]["can_import_reports"]:
            print("Resolved actor cannot import reports; choose an analyst, navigator, or admin identity.", file=sys.stderr)
            return 1

        alternate_identity, alternate_headers, _ = resolve_alternate_actor(
            args=args,
            base_url=base_url,
        )

        unsupported_fhir_payload = build_fhir_unsupported_demo_payload(run_id=smoke_run_id)
        fhir_summary, fhir_detail = import_fhir_payload_expect_failure(
            base_url=base_url,
            auth_headers=auth_headers,
            payload=unsupported_fhir_payload,
            expected_status_code=400,
            label="FHIR failed shared-visibility run",
        )
        fhir_run_id = _assert_failed_import_run(
            failure_summary=fhir_summary,
            import_detail=fhir_detail,
            expected_status_code=400,
            expected_source_format="fhir-diagnostic-report",
            expected_failure_bucket="unsupported_payload",
            expected_failed=1,
            expected_imported_sites=[],
            expected_item_count=0,
        )
        _assert_import_run_visible_to_actor(
            base_url=base_url,
            auth_headers=alternate_headers,
            run_id=fhir_run_id,
            label="Alternate actor failed FHIR shared visibility",
            expected_actor_user_id=auth_me["user_id"],
            expected_status="failed",
            expected_source_format="fhir-diagnostic-report",
        )

        hl7_failure_payload = build_hl7_parse_failure_demo_payload(
            run_id=smoke_run_id,
            site_scope=auth_me.get("site_scope"),
        )
        hl7_summary, hl7_detail = import_hl7_payload_expect_failure(
            base_url=base_url,
            auth_headers=auth_headers,
            payload=hl7_failure_payload,
            expected_status_code=400,
            label="HL7 failed shared-visibility run",
        )
        hl7_run_id = _assert_failed_import_run(
            failure_summary=hl7_summary,
            import_detail=hl7_detail,
            expected_status_code=400,
            expected_source_format="hl7-oru",
            expected_failure_bucket="parse_error",
            expected_failed=1,
            expected_imported_sites=[],
            expected_item_count=0,
        )
        _assert_import_run_visible_to_actor(
            base_url=base_url,
            auth_headers=alternate_headers,
            run_id=hl7_run_id,
            label="Alternate actor failed HL7 shared visibility",
            expected_actor_user_id=auth_me["user_id"],
            expected_status="failed",
            expected_source_format="hl7-oru",
        )

        expect_no_visible_cases = True
        print()
        print(
            f"Verified alternate actor {alternate_identity['user_id']} can access failed "
            f"FHIR run #{fhir_run_id} and HL7 run #{hl7_run_id}."
        )

    if args.import_adapter_failures:
        if not auth_me["capabilities"]["can_import_reports"]:
            print("Resolved actor cannot import reports; choose an analyst, navigator, or admin identity.", file=sys.stderr)
            return 1

        unsupported_fhir_payload = build_fhir_unsupported_demo_payload(run_id=smoke_run_id)
        fhir_summary, fhir_detail = import_fhir_payload_expect_failure(
            base_url=base_url,
            auth_headers=auth_headers,
            payload=unsupported_fhir_payload,
            expected_status_code=400,
            label="FHIR unsupported payload run",
        )
        fhir_run_id = _assert_failed_import_run(
            failure_summary=fhir_summary,
            import_detail=fhir_detail,
            expected_status_code=400,
            expected_source_format="fhir-diagnostic-report",
            expected_failure_bucket="unsupported_payload",
            expected_failed=1,
            expected_imported_sites=[],
            expected_item_count=0,
        )

        hl7_failure_payload = build_hl7_parse_failure_demo_payload(
            run_id=smoke_run_id,
            site_scope=auth_me.get("site_scope"),
        )
        hl7_summary, hl7_detail = import_hl7_payload_expect_failure(
            base_url=base_url,
            auth_headers=auth_headers,
            payload=hl7_failure_payload,
            expected_status_code=400,
            label="HL7 parse failure run",
        )
        hl7_run_id = _assert_failed_import_run(
            failure_summary=hl7_summary,
            import_detail=hl7_detail,
            expected_status_code=400,
            expected_source_format="hl7-oru",
            expected_failure_bucket="parse_error",
            expected_failed=1,
            expected_imported_sites=[],
            expected_item_count=0,
        )

        expect_no_visible_cases = True
        print()
        print(
            f"Verified persisted adapter failure runs #{fhir_run_id} (unsupported_payload) "
            f"and #{hl7_run_id} (parse_error)."
        )

    case_list: list[dict[str, object]] = []
    if args.check_cases or review_action:
        case_query = {"limit": 10}
        if case_query_hint:
            case_query["q"] = case_query_hint
        case_list = fetch_json(
            f"{base_url}/api/v1/cases?{parse.urlencode(case_query)}",
            headers=auth_headers,
        )
        print()
        print(f"Visible cases: {len(case_list)}")
        if case_list:
            print("Sample case IDs:", ", ".join(str(item["case_id"]) for item in case_list[:5]))
        if expect_no_visible_cases and case_list:
            print("Failure-path smoke unexpectedly produced visible cases for the run-specific query.", file=sys.stderr)
            return 1

    if review_action:
        if not case_list:
            print("No visible cases available for the review round-trip.", file=sys.stderr)
            return 1
        if not auth_me["capabilities"]["can_review_cases"]:
            print("Resolved actor is read-only; cannot perform a review round-trip.", file=sys.stderr)
            return 1
        roundtrip_case_id = str(case_list[0]["case_id"])
        review_result = post_json(
            f"{base_url}/api/v1/cases/{roundtrip_case_id}/review",
            headers=auth_headers,
            payload={
                "action": review_action,
                "note": f"{args.review_note} ({smoke_run_id})",
            },
        )
        case_detail = fetch_json(
            f"{base_url}/api/v1/cases/{roundtrip_case_id}",
            headers=auth_headers,
        )
        _assert_review_roundtrip(
            auth_actor=auth_me,
            case_id=roundtrip_case_id,
            review_action=review_action,
            review_result=review_result,
            case_detail=case_detail,
        )
        print()
        print(f"Review round-trip verified for case {roundtrip_case_id}.")

    return 0


def build_auth_headers(args: argparse.Namespace) -> dict[str, str]:
    return build_auth_headers_for_actor(
        args,
        user_id=args.user_id,
        display_name=args.display_name,
        role_value=args.role_value,
        sites=args.sites,
        groups=args.groups,
    )


def build_auth_headers_for_actor(
    args: argparse.Namespace,
    *,
    user_id: str,
    display_name: str,
    role_value: str,
    sites: str,
    groups: str,
) -> dict[str, str]:
    if args.auth_mode == "header":
        return build_header_auth_headers(
            user_id_header_name=args.user_id_header_name,
            display_name_header_name=args.display_name_header_name,
            role_header_name=args.role_header_name,
            sites_header_name=args.sites_header_name,
            user_id=user_id,
            display_name=display_name,
            role_value=role_value,
            sites=sites,
        )

    payload = build_identity_payload(
        provider_preset=args.provider_preset,
        user_id=user_id,
        display_name=display_name,
        role_value=role_value,
        sites=sites,
        groups=groups,
    )
    header_value = encode_identity_payload(payload, use_base64=args.base64)
    return {args.header_name: header_value}


def resolve_audit_alt_identity(args: argparse.Namespace) -> dict[str, str]:
    user_id = (args.audit_alt_user_id or f"{args.user_id}-audit-alt").strip()
    if not user_id:
        print("Audit visibility smoke requires a non-empty alternate actor user ID.", file=sys.stderr)
        raise SystemExit(1)
    if user_id == args.user_id:
        print("Audit visibility smoke requires the alternate actor to use a different user ID.", file=sys.stderr)
        raise SystemExit(1)

    display_name = (args.audit_alt_display_name or f"{args.display_name or args.user_id} Audit Alt").strip()
    role_value = (args.audit_alt_role_value or args.role_value).strip()
    sites = (args.audit_alt_sites or args.sites).strip()
    groups = (args.audit_alt_groups if args.audit_alt_groups is not None else args.groups).strip()

    return {
        "user_id": user_id,
        "display_name": display_name or user_id,
        "role_value": role_value,
        "sites": sites,
        "groups": groups,
    }


def resolve_alternate_actor(
    *,
    args: argparse.Namespace,
    base_url: str,
) -> tuple[dict[str, str], dict[str, str], dict[str, object]]:
    alternate_identity = resolve_audit_alt_identity(args)
    alternate_headers = build_auth_headers_for_actor(
        args,
        user_id=alternate_identity["user_id"],
        display_name=alternate_identity["display_name"],
        role_value=alternate_identity["role_value"],
        sites=alternate_identity["sites"],
        groups=alternate_identity["groups"],
    )
    alternate_auth_me = fetch_json(
        f"{base_url}/api/v1/auth/me",
        headers=alternate_headers,
    )
    print()
    print("Resolved alternate actor:")
    print(json.dumps(alternate_auth_me, indent=2, sort_keys=True))

    if not isinstance(alternate_auth_me, dict) or not alternate_auth_me.get("capabilities", {}).get(
        "can_import_reports",
    ):
        print(
            "Resolved alternate actor cannot access import audit routes; choose an analyst, navigator, or admin identity.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    return alternate_identity, alternate_headers, alternate_auth_me


def build_header_auth_headers(
    *,
    user_id_header_name: str,
    display_name_header_name: str,
    role_header_name: str,
    sites_header_name: str,
    user_id: str,
    display_name: str,
    role_value: str,
    sites: str,
) -> dict[str, str]:
    headers = {
        user_id_header_name: user_id,
        role_header_name: role_value,
    }

    if display_name:
        headers[display_name_header_name] = display_name

    site_values = [item.strip() for item in sites.split(",") if item.strip()]
    if site_values:
        headers[sites_header_name] = ", ".join(site_values)

    return headers


def build_identity_payload(
    *,
    provider_preset: str,
    user_id: str,
    display_name: str,
    role_value: str,
    sites: str,
    groups: str,
) -> dict[str, object]:
    preset = _PRESETS[provider_preset]
    payload: dict[str, object] = {}
    _set_nested_claim(payload, preset["user_id_field"], user_id)
    _set_nested_claim(payload, preset["display_name_field"], display_name)
    _set_nested_claim(payload, preset["role_field"], [role_value] if "." in preset["role_field"] else role_value)

    site_values = [item for item in (site.strip() for site in sites.split(",")) if item]
    if site_values:
        _set_nested_claim(payload, preset["sites_field"], site_values)

    group_values = [item for item in (group.strip() for group in groups.split(",")) if item]
    if group_values:
        _set_nested_claim(payload, preset["groups_field"], group_values)

    return payload


def encode_identity_payload(payload: dict[str, object], *, use_base64: bool) -> str:
    raw = json.dumps(payload, separators=(",", ":"))
    if not use_base64:
        return raw
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8").rstrip("=")


def load_demo_reports(
    *,
    auth_actor: dict[str, object],
    demo_file: Path,
    run_id: str,
) -> list[dict[str, object]]:
    if not demo_file.exists():
        print(f"Demo file not found: {demo_file}", file=sys.stderr)
        raise SystemExit(1)

    actor_sites = auth_actor.get("site_scope") or []
    target_site = actor_sites[0] if actor_sites else None
    reports: list[dict[str, object]] = []

    with demo_file.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            payload["case_id"] = f"{payload['case_id']}-{run_id}"
            payload["report_id"] = f"{payload['report_id']}-{run_id}"
            if target_site:
                payload["site"] = target_site
            reports.append(payload)

    return reports


def override_report_sites(reports: list[dict[str, object]], site: str) -> list[dict[str, object]]:
    return [{**report, "site": site} for report in reports]


def build_validation_failure_demo_payload(*, run_id: str, site_scope: object) -> bytes:
    target_site = _target_site(site_scope)
    payload = {
        "report_id": f"R-VAL-{run_id}",
        "case_id": f"C-VAL-{run_id}",
        "site": target_site,
    }
    return (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")


def build_parse_failure_demo_payload(*, run_id: str) -> bytes:
    return f'{{"report_id":"R-PARSE-{run_id}","case_id":"C-PARSE-{run_id}"\n'.encode("utf-8")


def build_fhir_unsupported_demo_payload(*, run_id: str) -> dict[str, object]:
    return {
        "resourceType": "Observation",
        "id": f"obs-unsupported-{run_id}",
    }


def build_hl7_parse_failure_demo_payload(*, run_id: str, site_scope: object) -> str:
    target_site = _target_site(site_scope)
    return "\r".join(
        [
            f"MSH|^~\\&|RADSYS|{target_site}|PS|PS|20260319130000||ORU^R01|MSG-PARSE-{run_id}|P|2.5",
            f"PID|1||PAT-PARSE-{run_id}^^^MRN||Doe^Jamie",
        ]
    )


def seed_demo_reports(
    *,
    base_url: str,
    reports: list[dict[str, object]],
) -> list[str]:
    batch_result = post_json(
        f"{base_url}/api/v1/triage/batch",
        headers={},
        payload={"reports": reports},
    )
    print("Seed batch result:")
    print(json.dumps(batch_result, indent=2, sort_keys=True))
    return [str(report["case_id"]) for report in reports]


def import_demo_reports(
    *,
    base_url: str,
    auth_headers: dict[str, str],
    demo_file: Path,
    reports: list[dict[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    payload_lines = [json.dumps(report, separators=(",", ":")) for report in reports]
    payload_bytes = ("\n".join(payload_lines) + "\n").encode("utf-8")
    source_name = demo_file.name or "reports.jsonl"

    import_summary = post_multipart_file(
        f"{base_url}/api/v1/imports/reports",
        headers=auth_headers,
        field_name="file",
        filename=source_name,
        content_type="application/x-ndjson",
        content=payload_bytes,
    )
    if not isinstance(import_summary, dict):
        print("Import route returned an unexpected payload.", file=sys.stderr)
        raise SystemExit(1)

    run_id = import_summary.get("run_id")
    if not isinstance(run_id, int):
        print(f"Import route did not return a valid run_id: {import_summary}", file=sys.stderr)
        raise SystemExit(1)

    import_run_detail = fetch_json(
        f"{base_url}/api/v1/imports/runs/{run_id}",
        headers=auth_headers,
    )
    if not isinstance(import_run_detail, dict):
        print("Import run detail route returned an unexpected payload.", file=sys.stderr)
        raise SystemExit(1)

    import_runs = fetch_json(
        f"{base_url}/api/v1/imports/runs?limit=5",
        headers=auth_headers,
    )
    if not isinstance(import_runs, list) or not any(_run_matches_id(item, run_id) for item in import_runs):
        print(f"Recent import runs did not include run #{run_id}.", file=sys.stderr)
        raise SystemExit(1)

    print("Import run summary:")
    print(json.dumps(import_summary, indent=2, sort_keys=True))
    print("Import run detail:")
    print(json.dumps(import_run_detail, indent=2, sort_keys=True))

    return import_summary, import_run_detail


def import_demo_reports_expect_site_scope_rejection(
    *,
    base_url: str,
    auth_headers: dict[str, str],
    demo_file: Path,
    reports: list[dict[str, object]],
) -> tuple[dict[str, object], dict[str, object]]:
    payload_lines = [json.dumps(report, separators=(",", ":")) for report in reports]
    payload_bytes = ("\n".join(payload_lines) + "\n").encode("utf-8")
    source_name = demo_file.name or "reports.jsonl"

    failure_summary, import_run_detail = import_report_payload_expect_failure(
        base_url=base_url,
        auth_headers=auth_headers,
        filename=source_name,
        content_type="application/x-ndjson",
        payload_bytes=payload_bytes,
        expected_status_code=403,
        label="Site-scope rejection run",
    )
    return failure_summary, import_run_detail


def import_report_payload_expect_failure(
    *,
    base_url: str,
    auth_headers: dict[str, str],
    filename: str,
    content_type: str,
    payload_bytes: bytes,
    expected_status_code: int,
    label: str,
) -> tuple[dict[str, object], dict[str, object]]:
    status_code, response_headers, response_body = post_multipart_file_response(
        f"{base_url}/api/v1/imports/reports",
        headers=auth_headers,
        field_name="file",
        filename=filename,
        content_type=content_type,
        content=payload_bytes,
    )
    if status_code != expected_status_code:
        print(
            f"Expected HTTP {expected_status_code} from failed import, got {status_code}: {response_body}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    run_id = _extract_import_run_id(response_headers, label=f"{label} response")
    import_run_detail = _fetch_and_print_import_run_by_id(
        base_url=base_url,
        auth_headers=auth_headers,
        run_id=run_id,
        label=label,
        summary={
            "detail": response_body.get("detail") if isinstance(response_body, dict) else response_body,
            "run_id": run_id,
            "status_code": status_code,
        },
    )
    failure_summary = {
        "detail": response_body.get("detail") if isinstance(response_body, dict) else response_body,
        "run_id": run_id,
        "status_code": status_code,
    }
    return failure_summary, import_run_detail


def build_fhir_demo_payload(
    *,
    run_id: str,
    site_scope: object,
) -> tuple[dict[str, object], list[str], list[str]]:
    target_site = _target_site(site_scope)
    diagnostic_report_id = f"dr-fhir-{run_id}"
    payload: dict[str, object] = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Organization",
                    "id": "org-smoke",
                    "name": target_site,
                }
            },
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": f"patient-{run_id}",
                    "identifier": [{"value": f"MRN-{run_id}"}],
                }
            },
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": f"encounter-{run_id}",
                    "identifier": [{"value": f"ENC-{run_id}"}],
                    "serviceProvider": {"reference": "Organization/org-smoke"},
                }
            },
            {
                "resource": {
                    "resourceType": "Practitioner",
                    "id": f"practitioner-{run_id}",
                    "name": [{"given": ["Jamie"], "family": "Patel"}],
                }
            },
            {
                "resource": {
                    "resourceType": "ServiceRequest",
                    "id": f"service-request-{run_id}",
                    "identifier": [
                        {
                            "type": {"text": "Accession Number"},
                            "value": f"ACC-{run_id}",
                        }
                    ],
                    "requester": {"reference": f"Practitioner/practitioner-{run_id}"},
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": f"observation-{run_id}",
                    "code": {"text": "Pancreatic duct"},
                    "valueString": "Abrupt cutoff of the pancreatic duct with upstream dilation.",
                }
            },
            {
                "resource": {
                    "resourceType": "DiagnosticReport",
                    "id": diagnostic_report_id,
                    "meta": {"source": f"urn:source:fhir-smoke:{run_id}"},
                    "effectiveDateTime": "2026-03-19T11:00:00Z",
                    "subject": {"reference": f"Patient/patient-{run_id}"},
                    "encounter": {"reference": f"Encounter/encounter-{run_id}"},
                    "basedOn": [{"reference": f"ServiceRequest/service-request-{run_id}"}],
                    "category": [{"text": "MRI abdomen"}],
                    "performer": [{"reference": "Organization/org-smoke"}],
                    "result": [{"reference": f"Observation/observation-{run_id}"}],
                    "conclusion": "Suspicious for pancreatic neoplasm. Recommend EUS.",
                }
            },
        ],
    }
    return payload, [diagnostic_report_id], [diagnostic_report_id]


def import_fhir_demo_payload(
    *,
    base_url: str,
    auth_headers: dict[str, str],
    payload: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    import_summary = post_json(
        f"{base_url}/api/v1/imports/fhir/diagnostic-reports",
        headers=auth_headers,
        payload=payload,
    )
    if not isinstance(import_summary, dict):
        print("FHIR import route returned an unexpected payload.", file=sys.stderr)
        raise SystemExit(1)
    return _fetch_and_print_import_run(
        base_url=base_url,
        auth_headers=auth_headers,
        import_summary=import_summary,
        label="FHIR import run",
    )


def import_fhir_payload_expect_failure(
    *,
    base_url: str,
    auth_headers: dict[str, str],
    payload: dict[str, object],
    expected_status_code: int,
    label: str,
) -> tuple[dict[str, object], dict[str, object]]:
    status_code, response_headers, response_body = post_json_response(
        f"{base_url}/api/v1/imports/fhir/diagnostic-reports",
        headers=auth_headers,
        payload=payload,
    )
    return _failure_response_to_run(
        base_url=base_url,
        auth_headers=auth_headers,
        status_code=status_code,
        response_headers=response_headers,
        response_body=response_body,
        expected_status_code=expected_status_code,
        label=label,
    )


def build_hl7_demo_payload(
    *,
    run_id: str,
    site_scope: object,
) -> tuple[str, list[str], list[str]]:
    target_site = _target_site(site_scope)
    report_id = f"R-HL7-{run_id}"
    pv1_fields = ["PV1", "1", "O", f"RAD^^^{target_site}", *[""] * 15, f"ENC-{run_id}"]
    obr_fields = [
        "OBR",
        "1",
        f"PLAC-{run_id}",
        report_id,
        "CT ABDOMEN^CT Abdomen",
        "",
        "",
        "20260319110000",
        *[""] * 8,
        "PROV-1^Patel^Jamie",
        "",
        f"ACC-{run_id}",
    ]
    payload = "\r".join(
        [
            f"MSH|^~\\&|RADSYS|{target_site}|PS|PS|20260319110000||ORU^R01|MSG-{run_id}|P|2.5",
            f"PID|1||PAT-{run_id}^^^MRN||Doe^Jamie",
            "|".join(pv1_fields),
            "|".join(obr_fields),
            "OBX|1|TX|FINDINGS^Findings||Abrupt cutoff of the pancreatic duct with ill-defined pancreatic head lesion.|",
            "OBX|2|TX|IMPRESSION^Impression||Suspicious for pancreatic neoplasm. Recommend biopsy.|",
        ]
    )
    return payload, [report_id], [report_id]


def import_hl7_demo_payload(
    *,
    base_url: str,
    auth_headers: dict[str, str],
    payload: str,
) -> tuple[dict[str, object], dict[str, object]]:
    import_summary = post_text(
        f"{base_url}/api/v1/imports/hl7/oru",
        headers=auth_headers,
        payload=payload,
        content_type="text/plain; charset=utf-8",
    )
    if not isinstance(import_summary, dict):
        print("HL7 import route returned an unexpected payload.", file=sys.stderr)
        raise SystemExit(1)
    return _fetch_and_print_import_run(
        base_url=base_url,
        auth_headers=auth_headers,
        import_summary=import_summary,
        label="HL7 import run",
    )


def import_hl7_payload_expect_failure(
    *,
    base_url: str,
    auth_headers: dict[str, str],
    payload: str,
    expected_status_code: int,
    label: str,
) -> tuple[dict[str, object], dict[str, object]]:
    status_code, response_headers, response_body = post_text_response(
        f"{base_url}/api/v1/imports/hl7/oru",
        headers=auth_headers,
        payload=payload,
        content_type="text/plain; charset=utf-8",
    )
    return _failure_response_to_run(
        base_url=base_url,
        auth_headers=auth_headers,
        status_code=status_code,
        response_headers=response_headers,
        response_body=response_body,
        expected_status_code=expected_status_code,
        label=label,
    )


def wait_for_json(url: str, *, timeout_seconds: float, headers: dict[str, str] | None = None) -> dict[str, object]:
    deadline = time.monotonic() + timeout_seconds
    last_error: str | None = None
    while time.monotonic() < deadline:
        try:
            result = fetch_json(url, headers=headers or {})
            if isinstance(result, dict):
                return result
            last_error = f"Unexpected JSON payload type: {type(result).__name__}"
        except SystemExit as exc:
            last_error = f"request failed with exit code {exc.code}"
        time.sleep(1)
    print(f"Timed out waiting for {url}. Last error: {last_error}", file=sys.stderr)
    raise SystemExit(1)


def wait_for_http_ok(url: str, *, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: str | None = None
    while time.monotonic() < deadline:
        try:
            req = request.Request(url)
            with request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return
                last_error = f"HTTP {response.status}"
        except error.URLError as exc:
            last_error = str(exc)
        except OSError as exc:
            last_error = str(exc)
        time.sleep(1)

    print(f"Timed out waiting for {url}. Last error: {last_error}", file=sys.stderr)
    raise SystemExit(1)


def fetch_json(url: str, *, headers: dict[str, str]) -> object:
    req = request.Request(url, headers=headers)
    try:
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code} from {url}: {body}", file=sys.stderr)
        raise SystemExit(1) from exc
    except error.URLError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except OSError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def fetch_json_response(url: str, *, headers: dict[str, str]) -> tuple[int, dict[str, str], object]:
    req = request.Request(url, headers=headers)
    try:
        with request.urlopen(req, timeout=10) as response:
            return response.status, dict(response.headers.items()), json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            body_value: object = json.loads(raw_body)
        except json.JSONDecodeError:
            body_value = raw_body
        return exc.code, dict(exc.headers.items()), body_value
    except error.URLError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except OSError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def post_json(url: str, *, headers: dict[str, str], payload: dict[str, object]) -> object:
    req_headers = {"Content-Type": "application/json", **headers}
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=req_headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code} from {url}: {body}", file=sys.stderr)
        raise SystemExit(1) from exc
    except error.URLError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except OSError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def post_json_response(
    url: str,
    *,
    headers: dict[str, str],
    payload: dict[str, object],
) -> tuple[int, dict[str, str], object]:
    req_headers = {"Content-Type": "application/json", **headers}
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=req_headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as response:
            return response.status, dict(response.headers.items()), json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            body_value: object = json.loads(raw_body)
        except json.JSONDecodeError:
            body_value = raw_body
        return exc.code, dict(exc.headers.items()), body_value
    except error.URLError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except OSError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def post_text(url: str, *, headers: dict[str, str], payload: str, content_type: str) -> object:
    req_headers = {"Content-Type": content_type, **headers}
    req = request.Request(
        url,
        data=payload.encode("utf-8"),
        headers=req_headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code} from {url}: {body}", file=sys.stderr)
        raise SystemExit(1) from exc
    except error.URLError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except OSError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def post_text_response(
    url: str,
    *,
    headers: dict[str, str],
    payload: str,
    content_type: str,
) -> tuple[int, dict[str, str], object]:
    req_headers = {"Content-Type": content_type, **headers}
    req = request.Request(
        url,
        data=payload.encode("utf-8"),
        headers=req_headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            return response.status, dict(response.headers.items()), json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            body_value: object = json.loads(raw_body)
        except json.JSONDecodeError:
            body_value = raw_body
        return exc.code, dict(exc.headers.items()), body_value
    except error.URLError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except OSError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def post_multipart_file(
    url: str,
    *,
    headers: dict[str, str],
    field_name: str,
    filename: str,
    content_type: str,
    content: bytes,
) -> object:
    boundary = f"----PancreaticSignalSmoke{time.time_ns()}"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{filename}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
            content,
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    req_headers = {"Content-Type": f"multipart/form-data; boundary={boundary}", **headers}
    req = request.Request(
        url,
        data=body,
        headers=req_headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code} from {url}: {body}", file=sys.stderr)
        raise SystemExit(1) from exc
    except error.URLError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except OSError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def post_multipart_file_response(
    url: str,
    *,
    headers: dict[str, str],
    field_name: str,
    filename: str,
    content_type: str,
    content: bytes,
) -> tuple[int, dict[str, str], object]:
    boundary = f"----PancreaticSignalSmoke{time.time_ns()}"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{filename}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
            content,
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    req_headers = {"Content-Type": f"multipart/form-data; boundary={boundary}", **headers}
    req = request.Request(
        url,
        data=body,
        headers=req_headers,
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=20) as response:
            return response.status, dict(response.headers.items()), json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            body_value: object = json.loads(raw_body)
        except json.JSONDecodeError:
            body_value = raw_body
        return exc.code, dict(exc.headers.items()), body_value
    except error.URLError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except OSError as exc:
        print(f"Failed to reach {url}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def _assert_import_run(
    *,
    import_summary: dict[str, object],
    import_detail: dict[str, object],
    expected_processed: int,
    expected_case_ids: list[str],
    expected_report_ids: list[str],
    expected_source_format: str,
) -> int:
    run_id = import_summary.get("run_id")
    processed = import_summary.get("processed")
    created = import_summary.get("created")
    updated = import_summary.get("updated")
    failed = import_summary.get("failed")
    case_ids = import_summary.get("case_ids")
    report_ids = import_summary.get("report_ids")
    source_format = import_summary.get("source_format")

    if not isinstance(run_id, int):
        print(f"Import summary missing integer run_id: {import_summary}", file=sys.stderr)
        raise SystemExit(1)
    if source_format != expected_source_format:
        print(
            f"Unexpected source_format for import run #{run_id}. "
            f"Expected {expected_source_format}, got {source_format}.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if processed != expected_processed:
        print(
            f"Unexpected processed count for import run #{run_id}. "
            f"Expected {expected_processed}, got {processed}.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if failed != 0:
        print(f"Import run #{run_id} recorded failures unexpectedly: {import_summary}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(created, int) or not isinstance(updated, int) or created + updated != expected_processed:
        print(f"Import run #{run_id} returned inconsistent created/updated counts: {import_summary}", file=sys.stderr)
        raise SystemExit(1)
    if case_ids != expected_case_ids:
        print(f"Import run #{run_id} returned unexpected case IDs: {case_ids}", file=sys.stderr)
        raise SystemExit(1)
    if report_ids != expected_report_ids:
        print(f"Import run #{run_id} returned unexpected report IDs: {report_ids}", file=sys.stderr)
        raise SystemExit(1)

    if import_detail.get("run_id") != run_id or import_detail.get("status") != "completed":
        print(f"Import detail did not match completed run #{run_id}: {import_detail}", file=sys.stderr)
        raise SystemExit(1)
    if import_detail.get("source_format") != expected_source_format:
        print(f"Import detail returned unexpected source format for run #{run_id}: {import_detail}", file=sys.stderr)
        raise SystemExit(1)
    if import_detail.get("processed") != expected_processed or import_detail.get("failed") != 0:
        print(f"Import detail returned unexpected counts for run #{run_id}: {import_detail}", file=sys.stderr)
        raise SystemExit(1)
    items = import_detail.get("items")
    if not isinstance(items, list) or len(items) != expected_processed:
        print(f"Import detail returned unexpected items for run #{run_id}: {import_detail}", file=sys.stderr)
        raise SystemExit(1)
    if any(not isinstance(item, dict) or item.get("status") != "imported" for item in items):
        print(f"Import detail returned non-imported items for run #{run_id}: {import_detail}", file=sys.stderr)
        raise SystemExit(1)

    return run_id


def _assert_failed_import_run(
    *,
    failure_summary: dict[str, object],
    import_detail: dict[str, object],
    expected_status_code: int,
    expected_source_format: str,
    expected_failure_bucket: str,
    expected_failed: int,
    expected_imported_sites: list[str],
    expected_item_count: int,
    expected_case_ids: list[str] | None = None,
    expected_report_ids: list[str] | None = None,
    expected_site: str | None = None,
) -> int:
    run_id = failure_summary.get("run_id")
    status_code = failure_summary.get("status_code")
    detail_message = failure_summary.get("detail")

    if not isinstance(run_id, int):
        print(f"Failure summary missing integer run_id: {failure_summary}", file=sys.stderr)
        raise SystemExit(1)
    if status_code != expected_status_code:
        print(f"Failure summary returned unexpected status code for run #{run_id}: {failure_summary}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(detail_message, str) or not detail_message:
        print(f"Failure summary missing detail message for run #{run_id}: {failure_summary}", file=sys.stderr)
        raise SystemExit(1)

    if import_detail.get("run_id") != run_id or import_detail.get("status") != "failed":
        print(f"Import detail did not match failed run #{run_id}: {import_detail}", file=sys.stderr)
        raise SystemExit(1)
    if import_detail.get("source_format") != expected_source_format:
        print(f"Import detail returned unexpected source format for run #{run_id}: {import_detail}", file=sys.stderr)
        raise SystemExit(1)
    if import_detail.get("processed") != 0 or import_detail.get("failed") != expected_failed:
        print(f"Import detail returned unexpected counts for run #{run_id}: {import_detail}", file=sys.stderr)
        raise SystemExit(1)

    failure_counts = import_detail.get("failure_counts")
    if not isinstance(failure_counts, dict) or failure_counts.get(expected_failure_bucket) != expected_failed:
        print(f"Import detail returned unexpected failure buckets for run #{run_id}: {import_detail}", file=sys.stderr)
        raise SystemExit(1)

    imported_sites = import_detail.get("imported_sites")
    if imported_sites != expected_imported_sites:
        print(f"Import detail returned unexpected imported sites for run #{run_id}: {import_detail}", file=sys.stderr)
        raise SystemExit(1)

    items = import_detail.get("items")
    if not isinstance(items, list) or len(items) != expected_item_count:
        print(f"Import detail returned unexpected items for run #{run_id}: {import_detail}", file=sys.stderr)
        raise SystemExit(1)

    if expected_case_ids is not None or expected_report_ids is not None:
        case_ids = [item.get("case_id") for item in items if isinstance(item, dict)]
        report_ids = [item.get("report_id") for item in items if isinstance(item, dict)]
        if case_ids != (expected_case_ids or []) or report_ids != (expected_report_ids or []):
            print(f"Import detail returned unexpected case/report IDs for run #{run_id}: {import_detail}", file=sys.stderr)
            raise SystemExit(1)

    for item in items:
        if not isinstance(item, dict):
            print(f"Import detail returned a non-dict failure item for run #{run_id}: {import_detail}", file=sys.stderr)
            raise SystemExit(1)
        if item.get("status") != "failed" or item.get("error_bucket") != expected_failure_bucket:
            print(f"Import detail returned an unexpected failed item for run #{run_id}: {import_detail}", file=sys.stderr)
            raise SystemExit(1)
        if expected_site is not None and item.get("site") != expected_site:
            print(f"Import detail returned an unexpected site for run #{run_id}: {import_detail}", file=sys.stderr)
            raise SystemExit(1)

    return run_id


def _assert_review_roundtrip(
    *,
    auth_actor: dict[str, object],
    case_id: str,
    review_action: str,
    review_result: object,
    case_detail: object,
) -> None:
    if not isinstance(review_result, dict):
        print("Review route returned an unexpected payload.", file=sys.stderr)
        raise SystemExit(1)
    if review_result.get("case_id") != case_id or review_result.get("action") != review_action:
        print("Review result did not echo the expected case/action.", file=sys.stderr)
        raise SystemExit(1)

    if not isinstance(case_detail, dict):
        print("Case detail route returned an unexpected payload.", file=sys.stderr)
        raise SystemExit(1)

    review_actions = case_detail.get("review_actions") or []
    if not review_actions:
        print("Case detail contains no review actions after the round-trip.", file=sys.stderr)
        raise SystemExit(1)

    last_action = review_actions[-1]
    expected_reviewer = auth_actor["user_id"]
    if last_action.get("action") != review_action or last_action.get("reviewer") != expected_reviewer:
        print(
            f"Unexpected review history tail. Expected {review_action}/{expected_reviewer}, "
            f"got {last_action}.",
            file=sys.stderr,
        )
        raise SystemExit(1)


def _set_nested_claim(payload: dict[str, object], field_path: str, value: object) -> None:
    segments = field_path.split(".")
    cursor = payload
    for segment in segments[:-1]:
        next_value = cursor.get(segment)
        if not isinstance(next_value, dict):
            next_value = {}
            cursor[segment] = next_value
        cursor = next_value
    cursor[segments[-1]] = value


def _run_matches_id(item: object, run_id: int) -> bool:
    return isinstance(item, dict) and item.get("run_id") == run_id


def _extract_import_run_id(headers: dict[str, str], *, label: str) -> int:
    header_value = headers.get("X-Import-Run-ID") or headers.get("x-import-run-id")
    if header_value is None:
        print(f"{label} did not return X-Import-Run-ID.", file=sys.stderr)
        raise SystemExit(1)
    try:
        return int(header_value)
    except ValueError as exc:
        print(f"{label} returned an invalid X-Import-Run-ID value: {header_value}", file=sys.stderr)
        raise SystemExit(1) from exc


def _failure_response_to_run(
    *,
    base_url: str,
    auth_headers: dict[str, str],
    status_code: int,
    response_headers: dict[str, str],
    response_body: object,
    expected_status_code: int,
    label: str,
) -> tuple[dict[str, object], dict[str, object]]:
    if status_code != expected_status_code:
        print(
            f"Expected HTTP {expected_status_code} from failed import, got {status_code}: {response_body}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    run_id = _extract_import_run_id(response_headers, label=f"{label} response")
    import_run_detail = _fetch_and_print_import_run_by_id(
        base_url=base_url,
        auth_headers=auth_headers,
        run_id=run_id,
        label=label,
        summary={
            "detail": response_body.get("detail") if isinstance(response_body, dict) else response_body,
            "run_id": run_id,
            "status_code": status_code,
        },
    )
    failure_summary = {
        "detail": response_body.get("detail") if isinstance(response_body, dict) else response_body,
        "run_id": run_id,
        "status_code": status_code,
    }
    return failure_summary, import_run_detail


def _assert_import_run_hidden_from_actor(
    *,
    base_url: str,
    auth_headers: dict[str, str],
    run_id: int,
    label: str,
) -> None:
    detail_status_code, _, detail_body = fetch_json_response(
        f"{base_url}/api/v1/imports/runs/{run_id}",
        headers=auth_headers,
    )
    list_status_code, _, list_body = fetch_json_response(
        f"{base_url}/api/v1/imports/runs?limit=10",
        headers=auth_headers,
    )
    _assert_import_run_hidden_responses(
        run_id=run_id,
        detail_status_code=detail_status_code,
        detail_body=detail_body,
        list_status_code=list_status_code,
        list_body=list_body,
        label=label,
    )
    print(f"{label} detail response:")
    print(json.dumps(detail_body, indent=2, sort_keys=True))
    print(f"{label} recent runs:")
    print(json.dumps(list_body, indent=2, sort_keys=True))


def _assert_import_run_visible_to_actor(
    *,
    base_url: str,
    auth_headers: dict[str, str],
    run_id: int,
    label: str,
    expected_actor_user_id: str | None = None,
    expected_status: str | None = None,
    expected_source_format: str | None = None,
) -> None:
    detail_status_code, _, detail_body = fetch_json_response(
        f"{base_url}/api/v1/imports/runs/{run_id}",
        headers=auth_headers,
    )
    list_status_code, _, list_body = fetch_json_response(
        f"{base_url}/api/v1/imports/runs?limit=10",
        headers=auth_headers,
    )
    _assert_import_run_visible_responses(
        run_id=run_id,
        detail_status_code=detail_status_code,
        detail_body=detail_body,
        list_status_code=list_status_code,
        list_body=list_body,
        label=label,
        expected_actor_user_id=expected_actor_user_id,
        expected_status=expected_status,
        expected_source_format=expected_source_format,
    )
    print(f"{label} detail response:")
    print(json.dumps(detail_body, indent=2, sort_keys=True))
    print(f"{label} recent runs:")
    print(json.dumps(list_body, indent=2, sort_keys=True))


def _assert_import_run_visible_responses(
    *,
    run_id: int,
    detail_status_code: int,
    detail_body: object,
    list_status_code: int,
    list_body: object,
    label: str,
    expected_actor_user_id: str | None = None,
    expected_status: str | None = None,
    expected_source_format: str | None = None,
) -> None:
    if detail_status_code != 200:
        print(
            f"{label} could not reach import run #{run_id}: HTTP {detail_status_code} {detail_body}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if not isinstance(detail_body, dict) or detail_body.get("run_id") != run_id:
        print(f"{label} returned an unexpected detail payload for run #{run_id}: {detail_body}", file=sys.stderr)
        raise SystemExit(1)
    if expected_actor_user_id is not None and detail_body.get("actor_user_id") != expected_actor_user_id:
        print(f"{label} returned an unexpected actor for run #{run_id}: {detail_body}", file=sys.stderr)
        raise SystemExit(1)
    if expected_status is not None and detail_body.get("status") != expected_status:
        print(f"{label} returned an unexpected status for run #{run_id}: {detail_body}", file=sys.stderr)
        raise SystemExit(1)
    if expected_source_format is not None and detail_body.get("source_format") != expected_source_format:
        print(f"{label} returned an unexpected source format for run #{run_id}: {detail_body}", file=sys.stderr)
        raise SystemExit(1)
    if list_status_code != 200:
        print(f"{label} list route returned HTTP {list_status_code}: {list_body}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(list_body, list):
        print(f"{label} list route returned an unexpected payload: {list_body}", file=sys.stderr)
        raise SystemExit(1)
    if not any(_run_matches_id(item, run_id) for item in list_body):
        print(f"{label} did not list import run #{run_id}: {list_body}", file=sys.stderr)
        raise SystemExit(1)


def _assert_import_run_hidden_responses(
    *,
    run_id: int,
    detail_status_code: int,
    detail_body: object,
    list_status_code: int,
    list_body: object,
    label: str,
) -> None:
    if detail_status_code != 404:
        print(
            f"{label} unexpectedly reached import run #{run_id}: HTTP {detail_status_code} {detail_body}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if not isinstance(detail_body, dict) or detail_body.get("detail") != "Import run not found":
        print(f"{label} returned an unexpected detail payload for run #{run_id}: {detail_body}", file=sys.stderr)
        raise SystemExit(1)
    if list_status_code != 200:
        print(f"{label} list route returned HTTP {list_status_code}: {list_body}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(list_body, list):
        print(f"{label} list route returned an unexpected payload: {list_body}", file=sys.stderr)
        raise SystemExit(1)
    if any(_run_matches_id(item, run_id) for item in list_body):
        print(f"{label} unexpectedly listed import run #{run_id}: {list_body}", file=sys.stderr)
        raise SystemExit(1)


def _target_site(site_scope: object) -> str:
    if isinstance(site_scope, list) and site_scope:
        first_site = site_scope[0]
        if isinstance(first_site, str) and first_site.strip():
            return first_site.strip()
    return "Demo Hospital"


def _fetch_and_print_import_run(
    *,
    base_url: str,
    auth_headers: dict[str, str],
    import_summary: dict[str, object],
    label: str,
) -> tuple[dict[str, object], dict[str, object]]:
    run_id = import_summary.get("run_id")
    if not isinstance(run_id, int):
        print(f"{label} did not return a valid run_id: {import_summary}", file=sys.stderr)
        raise SystemExit(1)

    import_run_detail = _fetch_and_print_import_run_by_id(
        base_url=base_url,
        auth_headers=auth_headers,
        run_id=run_id,
        label=label,
        summary=import_summary,
    )
    return import_summary, import_run_detail


def _fetch_and_print_import_run_by_id(
    *,
    base_url: str,
    auth_headers: dict[str, str],
    run_id: int,
    label: str,
    summary: dict[str, object] | None,
) -> dict[str, object]:
    import_run_detail = fetch_json(
        f"{base_url}/api/v1/imports/runs/{run_id}",
        headers=auth_headers,
    )
    if not isinstance(import_run_detail, dict):
        print(f"{label} detail route returned an unexpected payload.", file=sys.stderr)
        raise SystemExit(1)

    import_runs = fetch_json(
        f"{base_url}/api/v1/imports/runs?limit=5",
        headers=auth_headers,
    )
    if not isinstance(import_runs, list) or not any(_run_matches_id(item, run_id) for item in import_runs):
        print(f"Recent import runs did not include run #{run_id}.", file=sys.stderr)
        raise SystemExit(1)

    if summary is not None:
        print(f"{label} summary:")
        print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"{label} detail:")
    print(json.dumps(import_run_detail, indent=2, sort_keys=True))
    return import_run_detail


if __name__ == "__main__":
    raise SystemExit(main())
