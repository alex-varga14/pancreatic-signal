# Deployment Guide

## Scope

This project is ready for research and pilot-style deployments, not unsupervised clinical production use.

## Local stack

Use the default compose file for local development:

```bash
docker compose up --build
```

Service checks:
- API liveness: `GET /api/v1/health`
- API live probe: `GET /api/v1/health/live`
- API readiness: `GET /api/v1/health/ready`
- Web root: `GET /`

The compose stack now includes healthchecks for Postgres, the API, and the web app so service startup is gated by readiness rather than timing assumptions.

## Pilot overlay

Use the pilot overlay to remove dev-mode reload behavior and run the web app with `next build` plus `next start`:

```bash
docker compose -f docker-compose.yml -f docker-compose.pilot.yml up --build
```

This keeps the same topology while moving closer to a research-pilot runtime:
- API runs without `--reload`
- web runs as a built Next.js app
- both app services use `restart: unless-stopped`

## Environment variables

API:
- `APP_ENV`
- `DATABASE_URL`
- `CORS_ORIGINS`
- `LOG_LEVEL`
- `REQUEST_ID_HEADER_NAME`
- `MOCK_AUTH_ENABLED`
- `MOCK_AUTH_DEFAULT_USER_ID`
- `MOCK_AUTH_DEFAULT_DISPLAY_NAME`
- `MOCK_AUTH_DEFAULT_ROLE`
- `MOCK_AUTH_DEFAULT_SITES`
- `AUTH_ROLE_ALIAS_MAP`
- `AUTH_PROXY_PROVIDER_PRESET`
- `AUTH_PROXY_IDENTITY_HEADER_NAME`
- `AUTH_PROXY_USER_ID_FIELD`
- `AUTH_PROXY_DISPLAY_NAME_FIELD`
- `AUTH_PROXY_ROLE_FIELD`
- `AUTH_PROXY_SITES_FIELD`
- `AUTH_PROXY_GROUPS_FIELD`
- `AUTH_PROXY_GROUP_ROLE_MAP`
- `AUTH_USER_ID_HEADER_NAME`
- `AUTH_USER_NAME_HEADER_NAME`
- `AUTH_USER_ROLE_HEADER_NAME`
- `AUTH_USER_SITES_HEADER_NAME`
- `RESEARCH_ID_SALT`
- `FHIR_REFERENCE_IDENTIFIER_SOURCE_ORDER`
- `FHIR_SOURCE_SYSTEM_SOURCE_ORDER`
- `FHIR_ACCESSION_SOURCE_ORDER`
- `HL7_PATIENT_IDENTIFIER_FIELD_ORDER`
- `HL7_SOURCE_SYSTEM_FIELD_ORDER`
- `PANCREATIC_SIGNAL_DATA_DIR`

Web:
- `API_BASE_URL`
- `NEXT_PUBLIC_API_BASE_URL`
- `PANCREATIC_SIGNAL_API_USER_ID`
- `PANCREATIC_SIGNAL_API_USER_NAME`
- `PANCREATIC_SIGNAL_API_USER_ROLE`
- `PANCREATIC_SIGNAL_API_USER_SITES`
- `PANCREATIC_SIGNAL_API_TRUSTED_IDENTITY_HEADER_NAME`
- `PANCREATIC_SIGNAL_API_TRUSTED_IDENTITY`
- `PANCREATIC_SIGNAL_API_TRUSTED_IDENTITY_B64`

## Sample env bundles

Checked-in starter env bundles now live under `/Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/deploy/examples`:

- `local-mock/api.env` and `local-mock/web.env`
  Baseline local development with mock auth enabled.
- `pilot-proxy-demo/api.env` and `pilot-proxy-demo/web.env`
  Trusted-proxy demo values for the existing fixed-identity overlay.
- `pilot-header-demo/api.env` and `pilot-header-demo/web.env`
  Field-level header auth values for a fixed site-scoped navigator demo.

These files are non-secret examples. You can use them as-is for demo overlays or copy them when preparing a pilot-specific bundle.

## Proxy demo overlay

Use the proxy demo overlay when you want to simulate a trusted identity provider without standing up a real SSO stack:

```bash
make pilot-proxy-demo-up
```

This overlay:
- disables mock auth on the API
- enables the `keycloak` proxy preset with a sample role alias map
- loads the sample env bundle in `deploy/examples/pilot-proxy-demo/`
- configures the web service to forward a fixed trusted identity envelope for a site-scoped demo navigator at `Demo Hospital`

After startup, validate the full flow from the host with:

```bash
make pilot-proxy-demo-smoke
```

The base smoke target waits for API and web readiness, resolves `/api/v1/auth/me`, verifies `/imports` renders successfully, imports the bundled demo reports through `POST /api/v1/imports/reports`, verifies the persisted audit record at `GET /api/v1/imports/runs/{run_id}`, fetches the visible case queue, and confirms a reviewer-action round-trip using the fixed navigator identity.

Hosted smoke automation is now available in [`.github/workflows/pilot-smoke.yml`](../.github/workflows/pilot-smoke.yml). That workflow reuses `make pilot-proxy-demo-smoke`, `make pilot-proxy-demo-site-rejection-smoke`, `make pilot-proxy-demo-adapter-site-rejection-smoke`, `make pilot-header-demo-smoke`, `make pilot-header-demo-site-rejection-smoke`, and `make pilot-header-demo-adapter-site-rejection-smoke` on manual dispatch and a weekly schedule. It is intentionally narrower than the full smoke matrix below: base success-path plus report-path and structured adapter site-rejection overlay checks are hosted, while the broader shared-visibility, audit-denial, and non-site structured failure targets remain manual operator checks.

Adapter-specific live smoke targets are also available in the proxy demo:

```bash
make pilot-proxy-demo-fhir-smoke
make pilot-proxy-demo-hl7-smoke
make pilot-proxy-demo-shared-visibility-smoke
make pilot-proxy-demo-adapter-shared-visibility-smoke
make pilot-proxy-demo-failed-shared-visibility-smoke
make pilot-proxy-demo-adapter-failed-shared-visibility-smoke
make pilot-proxy-demo-site-rejection-smoke
make pilot-proxy-demo-adapter-site-rejection-smoke
make pilot-proxy-demo-adapter-audit-visibility-smoke
make pilot-proxy-demo-parse-validation-smoke
make pilot-proxy-demo-adapter-failure-smoke
make pilot-proxy-demo-audit-visibility-smoke
```

These targets follow the same readiness and auth-resolution checks, but drive:
- `POST /api/v1/imports/fhir/diagnostic-reports`
- `POST /api/v1/imports/hl7/oru`

Success-path variants verify the returned `run_id`, persisted audit detail, visible imported cases, and reviewer-action round-trip in the same trusted-proxy session. Failure-path and visibility-only variants still reach the same web and audit surfaces, but intentionally skip the reviewer round-trip when no run-specific cases should be visible.

The shared-visibility target reuses the successful `/api/v1/imports/reports` path and then checks the audit endpoints across two actors. It verifies:
- the creating scoped actor can inspect the successful run through `GET /api/v1/imports/runs/{run_id}` and sees it in `GET /api/v1/imports/runs`
- a second import-capable actor with the same scoped site can read the same run detail
- that same second actor also sees the successful run in the recent-run list
- the primary actor still sees run-specific cases and completes the usual reviewer round-trip

The adapter shared-visibility target reuses the successful structured adapter paths and then checks the audit endpoints across two actors. It verifies:
- a FHIR `DiagnosticReport` import persists a successful run that both the creating actor and a second same-site actor can inspect
- an HL7 ORU import persists a successful run that both the creating actor and a second same-site actor can inspect
- both runs appear in the alternate actor's recent-run list
- the primary actor still sees run-specific cases and completes the usual reviewer round-trip

The failed-run shared-visibility target reuses the generic report import path with a validation-failing payload and then checks the audit endpoints across two actors. It verifies:
- the failed response returns HTTP 400 with `X-Import-Run-ID`
- the persisted run records the `validation_error` bucket and no imported sites
- the creating scoped actor can inspect the failed run through `GET /api/v1/imports/runs/{run_id}` and sees it in `GET /api/v1/imports/runs`
- a second import-capable actor with the same scoped site can read the same failed run detail and recent-run list entry
- no run-specific cases become visible, so the smoke intentionally skips the reviewer round-trip

The adapter failed-run shared-visibility target reuses the structured failure paths and then checks the audit endpoints across two actors. It verifies:
- an unsupported FHIR payload persists a failed `unsupported_payload` run that both the creating actor and a second same-site actor can inspect
- a malformed HL7 ORU payload persists a failed `parse_error` run that both the creating actor and a second same-site actor can inspect
- both failed runs appear in the alternate actor's recent-run list even though `imported_sites` is empty
- no run-specific cases become visible, so the smoke intentionally skips the reviewer round-trip

The failure-path target drives the bundled report import through a deliberately out-of-scope site value. It verifies:
- the import returns HTTP 403 with `X-Import-Run-ID`
- the persisted run records the `site_scope_rejection` bucket
- the failed items are visible through `GET /api/v1/imports/runs/{run_id}`
- no run-specific cases become visible, so the smoke intentionally skips the reviewer round-trip

The adapter site-rejection target drives valid structured adapter payloads through the same site-scope boundary. It verifies:
- a FHIR `DiagnosticReport` with an out-of-scope derived site persists a failed `site_scope_rejection` run
- an HL7 ORU payload with an out-of-scope derived site persists a failed `site_scope_rejection` run
- both failed responses return `X-Import-Run-ID`
- both runs remain visible to the creating actor through the audit routes
- no run-specific cases become visible, so the smoke intentionally skips the reviewer round-trip

The adapter audit-visibility target reuses those persisted structured site-scope rejection runs and then checks the audit endpoints across two actors. It verifies:
- the creating scoped actor can inspect both failed runs through `GET /api/v1/imports/runs/{run_id}` and sees them in `GET /api/v1/imports/runs`
- a second import-capable actor with the same in-scope site but a different user ID receives `404` on both failed run details
- that same second actor does not see either failed run in the recent-run list
- no run-specific cases become visible, so the smoke intentionally skips the reviewer round-trip

The malformed-report target exercises two non-site failure buckets on `/api/v1/imports/reports`. It verifies:
- a validation-failing JSONL upload persists a failed run with `validation_error`
- a malformed JSONL upload persists a failed run with `parse_error`
- both failed responses return `X-Import-Run-ID`
- no run-specific cases become visible, so the smoke intentionally skips the reviewer round-trip

The adapter-failure target exercises structured import failures directly on the adapter endpoints. It verifies:
- an unsupported FHIR payload persists a failed run with `unsupported_payload`
- a malformed HL7 ORU payload persists a failed run with `parse_error`
- both failed responses return `X-Import-Run-ID`
- no run-specific cases become visible, so the smoke intentionally skips the reviewer round-trip

The audit-visibility target reuses the persisted site-scope rejection path and then checks the audit endpoints across two actors. It verifies:
- the creating scoped actor can inspect the failed run through `GET /api/v1/imports/runs/{run_id}` and sees it in `GET /api/v1/imports/runs`
- a second import-capable actor with the same in-scope site but a different user ID receives `404` on the failed run detail
- that same second actor does not see the failed run in the recent-run list
- no run-specific cases become visible, so the smoke intentionally skips the reviewer round-trip

When you are done:

```bash
make pilot-proxy-demo-down
```

## Header demo overlay

Use the header demo overlay when an upstream gateway can only stamp simple identity headers such as `X-User-ID` and `X-User-Role`, rather than a structured trusted-identity envelope:

```bash
make pilot-header-demo-up
```

This overlay:
- disables mock auth on the API
- loads the sample env bundle in `deploy/examples/pilot-header-demo/`
- configures the web service to forward fixed `X-User-ID`, `X-User-Name`, `X-User-Role`, and `X-User-Sites` values for a site-scoped navigator

After startup, validate the stack with:

```bash
make pilot-header-demo-smoke
```

The base smoke target waits for API and web readiness, confirms `/api/v1/auth/me` resolves in header-auth mode, verifies `/imports` renders, imports the bundled demo reports through `POST /api/v1/imports/reports`, verifies the persisted audit record at `GET /api/v1/imports/runs/{run_id}`, fetches visible cases, and confirms a reviewer-action round-trip using the fixed navigator identity.

Adapter-specific live smoke targets are also available:

```bash
make pilot-header-demo-fhir-smoke
make pilot-header-demo-hl7-smoke
make pilot-header-demo-shared-visibility-smoke
make pilot-header-demo-adapter-shared-visibility-smoke
make pilot-header-demo-failed-shared-visibility-smoke
make pilot-header-demo-adapter-failed-shared-visibility-smoke
make pilot-header-demo-site-rejection-smoke
make pilot-header-demo-adapter-site-rejection-smoke
make pilot-header-demo-adapter-audit-visibility-smoke
make pilot-header-demo-parse-validation-smoke
make pilot-header-demo-adapter-failure-smoke
make pilot-header-demo-audit-visibility-smoke
```

These targets follow the same readiness and auth-resolution checks, but drive:
- `POST /api/v1/imports/fhir/diagnostic-reports`
- `POST /api/v1/imports/hl7/oru`

Success-path variants verify the returned `run_id`, persisted audit detail, visible imported cases, and reviewer-action round-trip in the same scoped session. Failure-path and visibility-only variants still reach the same web and audit surfaces, but intentionally skip the reviewer round-trip when no run-specific cases should be visible.

The header-auth shared-visibility target exercises the same successful import path and then confirms the owning actor plus a second scoped actor can both access the same persisted run detail and recent-run listing.
The header-auth adapter shared-visibility target exercises the successful FHIR and HL7 import paths and then confirms the owning actor plus a second scoped actor can both access those structured run details and recent-run listings.
The header-auth failed-run shared-visibility target exercises a persisted `validation_error` run and then confirms the owning actor plus a second scoped actor can both access that failed run detail and recent-run listing without exposing any run-specific cases.
The header-auth adapter failed-run shared-visibility target exercises persisted FHIR `unsupported_payload` and HL7 `parse_error` runs and then confirms the owning actor plus a second scoped actor can both access those failed run details and recent-run listings without exposing any run-specific cases.

The header-auth failure-path target exercises the same out-of-scope report import and verifies the persisted `site_scope_rejection` audit record without expecting any visible imported cases.
The header-auth adapter site-rejection target exercises out-of-scope FHIR and HL7 payloads and verifies persisted structured `site_scope_rejection` audit records without expecting any visible imported cases.
The header-auth adapter audit-visibility target exercises those same structured `site_scope_rejection` runs and then confirms the owning actor can inspect them while a second scoped actor cannot access the same audit details or recent-run listings.
The header-auth malformed-report target exercises the same persisted `validation_error` and `parse_error` audit checks without expecting any visible imported cases.
The header-auth adapter-failure target exercises the same persisted FHIR `unsupported_payload` and HL7 `parse_error` audit checks without expecting any visible imported cases.
The header-auth audit-visibility target exercises the same persisted site-scope rejection run and then confirms the owning actor can inspect it while a second scoped actor cannot access the same audit detail or recent-run listing.

When you are done:

```bash
make pilot-header-demo-down
```

For lower-level troubleshooting, the generic helper is still available:

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=proxy \
  SMOKE_PROVIDER_PRESET=keycloak \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=pdac-navigator \
  SMOKE_BASE64=1 \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_DEMO=1
```

For live audit-visibility verification in trusted-proxy mode:

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=proxy \
  SMOKE_PROVIDER_PRESET=keycloak \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=pdac-navigator \
  SMOKE_BASE64=1 \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_AUDIT_VISIBILITY=1 \
  SMOKE_SKIP_REVIEW=1
```

For live failed-run shared-visibility verification in trusted-proxy mode:

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=proxy \
  SMOKE_PROVIDER_PRESET=keycloak \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=pdac-navigator \
  SMOKE_BASE64=1 \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_FAILED_SHARED_VISIBILITY=1 \
  SMOKE_SKIP_REVIEW=1
```

For live structured adapter failed-run shared-visibility verification in trusted-proxy mode:

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=proxy \
  SMOKE_PROVIDER_PRESET=keycloak \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=pdac-navigator \
  SMOKE_BASE64=1 \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_ADAPTER_FAILED_SHARED_VISIBILITY=1 \
  SMOKE_SKIP_REVIEW=1
```

For live structured adapter site-rejection verification in trusted-proxy mode:

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=proxy \
  SMOKE_PROVIDER_PRESET=keycloak \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=pdac-navigator \
  SMOKE_BASE64=1 \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_ADAPTER_SITE_REJECTION=1 \
  SMOKE_REJECTION_SITE="Out of Scope Site" \
  SMOKE_SKIP_REVIEW=1
```

For live structured adapter audit-visibility verification in trusted-proxy mode:

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=proxy \
  SMOKE_PROVIDER_PRESET=keycloak \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=pdac-navigator \
  SMOKE_BASE64=1 \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_ADAPTER_AUDIT_VISIBILITY=1 \
  SMOKE_REJECTION_SITE="Out of Scope Site" \
  SMOKE_SKIP_REVIEW=1
```

For live shared-visibility verification in trusted-proxy mode:

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=proxy \
  SMOKE_PROVIDER_PRESET=keycloak \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=pdac-navigator \
  SMOKE_BASE64=1 \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_SHARED_VISIBILITY=1
```

For live structured shared-visibility verification in trusted-proxy mode:

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=proxy \
  SMOKE_PROVIDER_PRESET=keycloak \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=pdac-navigator \
  SMOKE_BASE64=1 \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_ADAPTER_SHARED_VISIBILITY=1
```

For structured adapter verification in trusted-proxy mode:

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=proxy \
  SMOKE_PROVIDER_PRESET=keycloak \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=pdac-navigator \
  SMOKE_BASE64=1 \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_FHIR_DEMO=1
```

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=proxy \
  SMOKE_PROVIDER_PRESET=keycloak \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=pdac-navigator \
  SMOKE_BASE64=1 \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_HL7_DEMO=1
```

For live site-scope rejection verification in either auth mode:

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=proxy \
  SMOKE_PROVIDER_PRESET=keycloak \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=pdac-navigator \
  SMOKE_BASE64=1 \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_DEMO_SITE_REJECTION=1 \
  SMOKE_REJECTION_SITE="Out of Scope Site" \
  SMOKE_SKIP_REVIEW=1
```

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=proxy \
  SMOKE_PROVIDER_PRESET=keycloak \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=pdac-navigator \
  SMOKE_BASE64=1 \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_DEMO_PARSE_VALIDATION_FAILURE=1 \
  SMOKE_SKIP_REVIEW=1
```

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=proxy \
  SMOKE_PROVIDER_PRESET=keycloak \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=pdac-navigator \
  SMOKE_BASE64=1 \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_ADAPTER_FAILURES=1 \
  SMOKE_SKIP_REVIEW=1
```

For field-level header auth instead of a trusted identity envelope:

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=header \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=navigator \
  SMOKE_SITES="Demo Hospital" \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_DEMO=1
```

For structured adapter verification in header-auth mode:

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=header \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=navigator \
  SMOKE_SITES="Demo Hospital" \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_FHIR_DEMO=1
```

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=header \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=navigator \
  SMOKE_SITES="Demo Hospital" \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_HL7_DEMO=1
```

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=header \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=navigator \
  SMOKE_SITES="Demo Hospital" \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_DEMO_SITE_REJECTION=1 \
  SMOKE_REJECTION_SITE="Out of Scope Site" \
  SMOKE_SKIP_REVIEW=1
```

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=header \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=navigator \
  SMOKE_SITES="Demo Hospital" \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_DEMO_PARSE_VALIDATION_FAILURE=1 \
  SMOKE_SKIP_REVIEW=1
```

```bash
make smoke-proxy-auth \
  SMOKE_AUTH_MODE=header \
  SMOKE_USER_ID=pilot-navigator \
  SMOKE_DISPLAY_NAME="Pilot Navigator" \
  SMOKE_ROLE_VALUE=navigator \
  SMOKE_SITES="Demo Hospital" \
  SMOKE_CHECK_WEB=1 \
  SMOKE_CHECK_IMPORTS_PAGE=1 \
  SMOKE_IMPORT_ADAPTER_FAILURES=1 \
  SMOKE_SKIP_REVIEW=1
```

## Identity modes

The API ships with mock auth enabled by default so reviewer actions, imports, and exports work in local development without an external identity provider.

- Default mock actor: `Demo Reviewer` / `demo-reviewer` / `admin`
- Supported roles: `viewer`, `reviewer`, `navigator`, `analyst`, `admin`
- Trusted proxy identity header defaults to `X-Trusted-Identity`
- Trusted proxy provider presets: `generic`, `authentik`, `keycloak`, `oauth2-proxy`
- Trusted proxy payload fields default to `sub`, `name`, `role`, `sites`, and `groups`
- Trusted proxy identities may be sent as raw JSON or base64url-encoded JSON
- `keycloak` preset reads user ID from `preferred_username` and role candidates from `realm_access.roles`
- `oauth2-proxy` preset reads user ID from `email`
- `authentik` preset reads user ID from `preferred_username`
- `AUTH_PROXY_GROUP_ROLE_MAP` accepts comma-separated mappings like `pdac-reviewers:reviewer,pdac-navigators:navigator`
- `AUTH_ROLE_ALIAS_MAP` accepts comma-separated mappings like `rad_navigator:navigator,site_admin:admin`
- Header override fields default to `X-User-ID`, `X-User-Name`, `X-User-Role`, and `X-User-Sites`
- Site scopes are comma-separated and optional. When present, read access, imports, exports, and feedback summary endpoints are restricted to those sites.

The web app consumes `/api/v1/auth/me` capability flags and hides reviewer and import controls automatically for read-only users, so pilot deployments can rely on the API as the source of truth for both route enforcement and UI gating.

For pilot-style deployments behind a trusted proxy or gateway, disable mock auth and forward either the trusted identity envelope header or the field-level identity headers from that upstream system. The Next.js app can still forward a fixed identity to the API with the `PANCREATIC_SIGNAL_API_*` environment variables when you want a simple shared reviewer identity for demos, including a fixed site scope or a full trusted identity envelope.

## Web import workspace

The built Next.js app now exposes a dedicated operator workspace at `/imports`.

- Allowed roles: `analyst`, `navigator`, `admin`
- Supported submissions: CSV / JSON / JSONL uploads, FHIR `DiagnosticReport` JSON, and HL7 ORU text
- Immediate operator feedback: the page redirects to the persisted import run and shows processed / created / updated / failed counts plus stable failure buckets

Because the page keys off `/api/v1/auth/me` capabilities, read-only sessions can still browse the rest of the web app without seeing import controls.
Both pilot demo overlays now validate this route in their smoke targets.

## De-identification

The API now exposes research-safe case surfaces at:
- `GET /api/v1/cases/research`
- `GET /api/v1/cases/{case_id}/research`

These views preserve evidence offsets while masking PHI-like free text, pseudonymizing case/report/reviewer identifiers, and converting report/review timestamps to date-only fields.

For research exports, pass `redact=true` to:
- `GET /api/v1/exports/cases.csv`
- `GET /api/v1/exports/review-feedback.jsonl`

`RESEARCH_ID_SALT` controls the stable pseudonymization salt for de-identified identifiers. Set it explicitly per deployment if you need deterministic but environment-specific research IDs.

`PANCREATIC_SIGNAL_DATA_DIR` can point the API at an alternate mounted data directory when the default repo-relative or `/data` lookup is not appropriate for the deployment layout.

## FHIR adapter

The initial integration adapter now supports `POST /api/v1/imports/fhir/diagnostic-reports` for:
- single `DiagnosticReport` resources
- FHIR `Bundle` payloads that include `DiagnosticReport` entries plus referenced `Observation` or `Organization` resources

This adapter is intentionally lightweight and feeds the existing `ReportInput` triage path instead of introducing a second persistence model. It is best suited for pilot gateways that can already provide JSON `DiagnosticReport` payloads.

The adapter now also preserves a small explicit provenance surface on each imported report when the payload provides it:
- `patient_identifier`
- `encounter_identifier`
- `accession_number`
- `ordering_provider`
- `source_system`
- `source_format`
- `import_source_id`

These values flow through case detail and export surfaces, while research-safe views pseudonymize the identifier-like fields.

Each import request now also persists an import-run audit summary with source format, actor, timestamps, processed / created / updated / failed counts, and stable failure buckets. Recent runs are available through:
- `GET /api/v1/imports/runs`
- `GET /api/v1/imports/runs/{run_id}`

When a request fails after an audit run has been recorded, the API also returns `X-Import-Run-ID`. The web import workspace uses that header to deep-link operators directly into the failed run detail instead of showing a generic error.

Field selection is now configurable with narrow precedence settings so pilots can adapt to upstream variability without code edits. Current knobs:
- `FHIR_REFERENCE_IDENTIFIER_SOURCE_ORDER`
  Valid values: `resolved_identifier`, `resolved_id`, `reference_tail`
- `FHIR_SOURCE_SYSTEM_SOURCE_ORDER`
  Valid values: `meta_source`, `performer`, `results_interpreter`, `encounter_service_provider`
- `FHIR_ACCESSION_SOURCE_ORDER`
  Valid values: `report_identifier_typed`, `based_on_identifier_typed`, `report_identifier`, `based_on_identifier`

## HL7 adapter

The initial HL7 integration adapter now supports `POST /api/v1/imports/hl7/oru` for raw HL7 v2 ORU result messages.

It currently:
- parses one or more ORU messages from a text payload
- emits one triaged case per `OBR` group
- builds report text from `OBX` / `NTE`
- derives site from `PV1-3` or `MSH-4`
- derives modality heuristically from `OBR-24` / `OBR-4`

Like the FHIR path, this adapter deliberately maps into the existing `ReportInput` triage flow rather than adding a separate hospital-interface persistence layer.

The HL7 path now preserves the same provenance surface from `PID`, `PV1`, `OBR`, and `MSH` with best-effort fallbacks when optional fields are absent, so pilot feeds can retain patient, encounter, accession, provider, and message-source context without changing triage semantics.

Failed imports are bucketed into stable categories for auditability:
- `parse_error`
- `validation_error`
- `unsupported_payload`
- `site_scope_rejection`

HL7 metadata selection now supports narrow field-preference overrides as well:
- `HL7_PATIENT_IDENTIFIER_FIELD_ORDER`
  Valid values: `PID-3`, `PID-2`
- `HL7_SOURCE_SYSTEM_FIELD_ORDER`
  Valid values: `MSH-3`, `MSH-4`

## Observability

The API now emits structured JSON request logs with:
- `event`
- `request_id`
- `method`
- `path`
- `status_code`
- `duration_ms`
- `client`
- `environment`

Clients can provide `X-Request-ID` and the API will echo it back in the response. If one is not provided, the API generates a request ID automatically.

## Readiness semantics

`/api/v1/health/ready` performs a database connectivity check with `SELECT 1`.

- `200 OK` means the app is ready to serve requests.
- `503 Service Unavailable` means a dependency check failed.

## Pilot checklist

1. Run `make validate-strict`.
2. Bring up the compose stack.
3. Verify `curl http://localhost:8000/api/v1/health/ready`.
4. Verify `curl http://localhost:3000`.
5. Verify `curl http://localhost:3000/imports` for import-enabled pilot identities.
6. Load demo data or import a study batch.
7. If using a pilot overlay, run the matching smoke target.
8. Capture request logs and exported benchmark artifacts for the pilot record.
