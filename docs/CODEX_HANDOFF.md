# Codex Handoff

Updated: 2026-03-22

This repository is no longer in early MVP scaffolding. The core research prototype is implemented and validated, and the best next work is now Phase 6 hardening around expanding hosted pilot-smoke coverage into structured audit and visibility paths on top of the hosted base, report-path site-rejection, and structured adapter site-rejection smoke coverage.

## Current State

- Deterministic pancreatic triage is implemented with section-aware sentence evidence, rationale codes, persistence, exports, and evaluation.
- Reviewer workflow is implemented end to end with worklist filters, case detail, review actions, feedback capture, hybrid prioritization, and trial matching.
- Phase 6 pilot work is materially in place: observability, readiness probes, trusted-proxy auth, site scoping, pilot Docker overlays, checked-in env bundles, de-identified research views, FHIR ingestion, HL7 ORU ingestion, structured import metadata persistence, persisted import-run audit records, env-driven field-preference overrides for upstream variability, a dedicated web import workspace with recent-run audit visibility, and live report/FHIR/HL7 success, successful shared-visibility, report-path failed shared-visibility for `validation_error`, structured failed shared-visibility for FHIR `unsupported_payload` plus HL7 `parse_error`, report-path and structured-adapter site-scope rejection, report-path parse/validation, adapter-specific malformed-import, and generic plus structured cross-actor audit denial smoke coverage in both the header-auth and trusted-proxy pilot paths.
- Top-level repo docs now reflect the implemented platform instead of the earlier scaffold framing, and the repository includes checked-in contributor, security, and code-of-conduct docs appropriate for a near-1.0 open-source handoff.
- The repo now also includes a top-level changelog, a release-readiness checklist, and checked-in GitHub Actions workflows for strict validation plus hosted base, report-path site-rejection, and structured adapter site-rejection pilot smoke coverage so the next agent can preserve release-facing narrative quality while continuing implementation.
- The highest-value remaining work is not bootstrapping. It is improving interoperability depth and pilot operability without breaking explainability.

## Fresh Validation Status

Confirmed on 2026-03-22:

- `make validate-strict` passes
- Summary: `9 pass, 0 warn, 0 fail`
- API tests: `101 passed`
- Web checks: `npm run lint` and `npm run build` now both pass through `make validate-strict`
- Demo evaluation compare and sweep both run through the validation script
- Targeted import / de-identification / export coverage also passes for the new import metadata surface
- Import-run audit coverage now passes for success, update counts, validation failures, unsupported payloads, site-scope rejection, and audit-route access control
- Config-override coverage now passes for one FHIR field-preference override and one HL7 field-preference override while preserving defaults
- The new `/imports` workspace is included in the validated web build and uses persisted run IDs to deep-link failed submissions into their audit detail
- Both pilot demo overlays resolve successfully through `docker compose config`
- The smoke helper now supports both trusted-identity proxy mode and field-level header-auth mode, plus live verification against `/api/v1/imports/reports`, `/api/v1/imports/fhir/diagnostic-reports`, and `/api/v1/imports/hl7/oru`
- The smoke helper now also supports live `site_scope_rejection` verification through `/api/v1/imports/reports`, including persisted failed run IDs and zero run-specific visible-case assertions
- The smoke helper now also supports live structured adapter `site_scope_rejection` verification through `/api/v1/imports/fhir/diagnostic-reports` and `/api/v1/imports/hl7/oru`, including persisted failed run IDs and zero run-specific visible-case assertions
- The smoke helper now also supports live structured adapter audit-visibility verification by reusing persisted FHIR and HL7 `site_scope_rejection` runs, proving the owner can inspect both while a second scoped actor receives `404` on both details and does not see either in the recent-run list
- The smoke helper now also supports live `validation_error` and `parse_error` verification through `/api/v1/imports/reports`, including persisted failed run IDs and zero run-specific visible-case assertions
- The smoke helper now also supports live structured adapter failure verification through `/api/v1/imports/fhir/diagnostic-reports` and `/api/v1/imports/hl7/oru`, including persisted `unsupported_payload` and `parse_error` run IDs plus zero run-specific visible-case assertions
- The smoke helper now also supports live audit-visibility verification by reusing a persisted `site_scope_rejection` run, proving the owner can inspect it while a second scoped actor receives `404` on detail and does not see it in the recent-run list
- The smoke helper now also supports live shared-visibility verification by reusing a successful `/api/v1/imports/reports` run, proving a second scoped actor can inspect the same completed run detail and recent-run list entry
- The smoke helper now also supports live structured shared-visibility verification by reusing successful FHIR and HL7 imports, proving a second scoped actor can inspect both completed structured runs and their recent-run list entries
- The smoke helper now also supports live failed-run shared-visibility verification by reusing a persisted `/api/v1/imports/reports` `validation_error` run, proving a second same-site actor can inspect the failed detail and recent-run entry even when `imported_sites` is empty
- The smoke helper now also supports live structured failed-run shared-visibility verification by reusing persisted FHIR `unsupported_payload` and HL7 `parse_error` runs, proving a second same-site actor can inspect both failed details and recent-run entries even when `imported_sites` is empty
- The proxy demo overlay now defaults to an import-capable navigator identity so the built `/imports` workspace and the live proxy smoke path exercise the same capability class
- The latest strict validation pass was rerun after expanding the hosted pilot smoke workflow into structured adapter site rejection and remains green
- GitHub Actions now runs `make validate-strict` on pull requests, on `main`, and through manual workflow dispatch using a checked-in workflow under `.github/workflows/validate.yml`
- A checked-in workflow under `.github/workflows/pilot-smoke.yml` now reuses `make pilot-proxy-demo-smoke`, `make pilot-proxy-demo-site-rejection-smoke`, `make pilot-proxy-demo-adapter-site-rejection-smoke`, `make pilot-header-demo-smoke`, `make pilot-header-demo-site-rejection-smoke`, and `make pilot-header-demo-adapter-site-rejection-smoke` on manual dispatch plus a weekly Monday schedule; its first GitHub-hosted run covering the new structured adapter site-rejection jobs is still pending
- Release-facing documentation now includes `CHANGELOG.md` and `docs/RELEASE_READINESS.md`

Last known good live deployment check:

- The header-demo Docker stack was booted with the pilot overlay
- `make pilot-header-demo-smoke` passed on 2026-03-21
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, report import via `/api/v1/imports/reports`, persisted import-run audit detail for run `41`, visible cases, and a persisted reviewer-action round-trip
- `make pilot-header-demo-fhir-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, FHIR import via `/api/v1/imports/fhir/diagnostic-reports`, persisted import-run audit detail, visible cases, and a persisted reviewer-action round-trip
- `make pilot-header-demo-hl7-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, HL7 import via `/api/v1/imports/hl7/oru`, persisted import-run audit detail, visible cases, and a persisted reviewer-action round-trip
- The proxy-demo Docker stack was booted with the pilot overlay
- `make pilot-proxy-demo-smoke` passed on 2026-03-21
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, report import via `/api/v1/imports/reports`, persisted import-run audit detail for run `40`, visible cases, and a persisted reviewer-action round-trip
- `make pilot-proxy-demo-fhir-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, FHIR import via `/api/v1/imports/fhir/diagnostic-reports`, persisted import-run audit detail, visible cases, and a persisted reviewer-action round-trip
- `make pilot-proxy-demo-hl7-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, HL7 import via `/api/v1/imports/hl7/oru`, persisted import-run audit detail, visible cases, and a persisted reviewer-action round-trip
- `make pilot-proxy-demo-site-rejection-smoke` passed on 2026-03-22
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, a persisted `site_scope_rejection` run via `/api/v1/imports/reports`, stable audit detail for run `42`, and zero run-specific visible cases
- `make pilot-proxy-demo-adapter-site-rejection-smoke` passed on 2026-03-22 local time
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, persisted FHIR and HL7 `site_scope_rejection` runs via the structured import endpoints, stable audit detail for runs `44` and `45`, and zero run-specific visible cases
- `make pilot-proxy-demo-adapter-audit-visibility-smoke` passed on 2026-03-21
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, persisted FHIR and HL7 `site_scope_rejection` runs via the structured import endpoints, owner visibility on both audit endpoints, alternate-actor `404` detail denial, alternate-actor omission from the recent-run list, and zero run-specific visible cases
- `make pilot-proxy-demo-parse-validation-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, persisted `validation_error` and `parse_error` runs via `/api/v1/imports/reports`, stable audit detail, and zero run-specific visible cases
- `make pilot-proxy-demo-adapter-failure-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, persisted FHIR `unsupported_payload` and HL7 `parse_error` runs via the structured import endpoints, stable audit detail, and zero run-specific visible cases
- `make pilot-proxy-demo-shared-visibility-smoke` passed on 2026-03-21
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, a successful `/api/v1/imports/reports` run, owner visibility on both audit endpoints, alternate-actor visibility on the same detail and recent-run list entry, visible run-specific cases, and a persisted reviewer-action round-trip
- `make pilot-proxy-demo-adapter-shared-visibility-smoke` passed on 2026-03-21
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, successful FHIR plus HL7 structured imports, owner visibility on both audit endpoints, alternate-actor visibility on both run details and recent-run list entries, visible run-specific cases, and a persisted reviewer-action round-trip
- `make pilot-proxy-demo-audit-visibility-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, a persisted `site_scope_rejection` run via `/api/v1/imports/reports`, owner visibility on both audit endpoints, alternate-actor `404` detail denial, alternate-actor omission from the recent-run list, and zero run-specific visible cases
- `make pilot-proxy-demo-failed-shared-visibility-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, a persisted `validation_error` run via `/api/v1/imports/reports`, owner visibility on both audit endpoints, alternate-actor allow behavior on the same failed detail and recent-run list entry, and zero run-specific visible cases
- `make pilot-proxy-demo-adapter-failed-shared-visibility-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, persisted FHIR `unsupported_payload` plus HL7 `parse_error` runs via the structured import endpoints, owner visibility on both audit endpoints, alternate-actor allow behavior on both failed details and recent-run list entries, and zero run-specific visible cases
- `make pilot-header-demo-site-rejection-smoke` passed on 2026-03-22
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, a persisted `site_scope_rejection` run via `/api/v1/imports/reports`, stable audit detail for run `43`, and zero run-specific visible cases
- `make pilot-header-demo-adapter-site-rejection-smoke` passed on 2026-03-22 local time
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, persisted FHIR and HL7 `site_scope_rejection` runs via the structured import endpoints, stable audit detail for runs `46` and `47`, and zero run-specific visible cases
- `make pilot-header-demo-adapter-audit-visibility-smoke` passed on 2026-03-21
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, persisted FHIR and HL7 `site_scope_rejection` runs via the structured import endpoints, owner visibility on both audit endpoints, alternate-actor `404` detail denial, alternate-actor omission from the recent-run list, and zero run-specific visible cases
- `make pilot-header-demo-parse-validation-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, persisted `validation_error` and `parse_error` runs via `/api/v1/imports/reports`, stable audit detail, and zero run-specific visible cases
- `make pilot-header-demo-adapter-failure-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, persisted FHIR `unsupported_payload` and HL7 `parse_error` runs via the structured import endpoints, stable audit detail, and zero run-specific visible cases
- `make pilot-header-demo-shared-visibility-smoke` passed on 2026-03-21
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, a successful `/api/v1/imports/reports` run, owner visibility on both audit endpoints, alternate-actor visibility on the same detail and recent-run list entry, visible run-specific cases, and a persisted reviewer-action round-trip
- `make pilot-header-demo-adapter-shared-visibility-smoke` passed on 2026-03-21
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, successful FHIR plus HL7 structured imports, owner visibility on both audit endpoints, alternate-actor visibility on both run details and recent-run list entries, visible run-specific cases, and a persisted reviewer-action round-trip
- `make pilot-header-demo-audit-visibility-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, a persisted `site_scope_rejection` run via `/api/v1/imports/reports`, owner visibility on both audit endpoints, alternate-actor `404` detail denial, alternate-actor omission from the recent-run list, and zero run-specific visible cases
- `make pilot-header-demo-failed-shared-visibility-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, a persisted `validation_error` run via `/api/v1/imports/reports`, owner visibility on both audit endpoints, alternate-actor allow behavior on the same failed detail and recent-run list entry, and zero run-specific visible cases
- `make pilot-header-demo-adapter-failed-shared-visibility-smoke` passed on 2026-03-20
- The smoke path verified API readiness, web readiness, `/imports`, `/api/v1/auth/me`, persisted FHIR `unsupported_payload` plus HL7 `parse_error` runs via the structured import endpoints, owner visibility on both audit endpoints, alternate-actor allow behavior on both failed details and recent-run list entries, and zero run-specific visible cases

Additional note from this slice:

- `make pilot-header-demo-up` required host-level Docker access and completed successfully
- The sandboxed `make pilot-header-demo-fhir-smoke` and `make pilot-header-demo-hl7-smoke` would have had the same localhost restriction as the existing smoke targets
- Unsandboxed runs of both `make pilot-header-demo-fhir-smoke` and `make pilot-header-demo-hl7-smoke` passed end to end
- `make pilot-header-demo-down` completed successfully after the live verification run
- `make validate-strict` passed after adding the GitHub Actions validation workflow and the web lint check to the strict gate
- The checked-in workflow at `.github/workflows/validate.yml` now runs `make validate-strict` on pull requests, on `main`, and through manual workflow dispatch
- `docker compose -f docker-compose.yml -f docker-compose.pilot.yml -f docker-compose.pilot.proxy-demo.yml config` passed
- `docker compose -f docker-compose.yml -f docker-compose.pilot.yml -f docker-compose.pilot.header-demo.yml config` passed
- `make pilot-proxy-demo-up` required host-level Docker access and completed successfully
- Unsandboxed runs of `make pilot-proxy-demo-smoke`, `make pilot-proxy-demo-fhir-smoke`, and `make pilot-proxy-demo-hl7-smoke` all passed end to end on 2026-03-20
- `make pilot-proxy-demo-down` completed successfully after the live verification run
- A new failure-path smoke mode now verifies persisted `site_scope_rejection` audit detail plus zero run-specific visible cases without requiring a reviewer round-trip
- Unsandboxed runs of `make pilot-proxy-demo-site-rejection-smoke` and `make pilot-header-demo-site-rejection-smoke` both passed end to end on 2026-03-20
- A new malformed-report smoke mode now verifies persisted `validation_error` and `parse_error` audit detail plus zero run-specific visible cases without requiring a reviewer round-trip
- Unsandboxed runs of `make pilot-proxy-demo-parse-validation-smoke` and `make pilot-header-demo-parse-validation-smoke` both passed end to end on 2026-03-20
- A new adapter-failure smoke mode now verifies persisted FHIR `unsupported_payload` and HL7 `parse_error` audit detail plus zero run-specific visible cases without requiring a reviewer round-trip
- Unsandboxed runs of `make pilot-proxy-demo-adapter-failure-smoke` and `make pilot-header-demo-adapter-failure-smoke` both passed end to end on 2026-03-20
- A new audit-visibility smoke mode now verifies owner access plus alternate-actor denial for a persisted `site_scope_rejection` run across both import-run audit endpoints
- Unsandboxed runs of `make pilot-proxy-demo-audit-visibility-smoke` and `make pilot-header-demo-audit-visibility-smoke` both passed end to end on 2026-03-20
- A new shared-visibility smoke mode now verifies owner access plus alternate-actor allow behavior for a successful persisted `/api/v1/imports/reports` run across both import-run audit endpoints
- Unsandboxed runs of `make pilot-proxy-demo-shared-visibility-smoke` and `make pilot-header-demo-shared-visibility-smoke` both passed end to end on 2026-03-21
- A new structured shared-visibility smoke mode now verifies owner access plus alternate-actor allow behavior for successful FHIR and HL7 imports across both import-run audit endpoints
- Unsandboxed runs of `make pilot-proxy-demo-adapter-shared-visibility-smoke` and `make pilot-header-demo-adapter-shared-visibility-smoke` both passed end to end on 2026-03-21
- A new failed-run shared-visibility smoke mode now verifies owner access plus alternate-actor allow behavior for a persisted `/api/v1/imports/reports` `validation_error` run across both import-run audit endpoints
- Unsandboxed runs of `make pilot-proxy-demo-failed-shared-visibility-smoke` and `make pilot-header-demo-failed-shared-visibility-smoke` both passed end to end on 2026-03-20 local time, producing persisted run timestamps `2026-03-21T04:23:26Z` and `2026-03-21T04:24:10Z`
- A new structured failed-run shared-visibility smoke mode now verifies owner access plus alternate-actor allow behavior for persisted FHIR `unsupported_payload` and HL7 `parse_error` runs across both import-run audit endpoints
- Unsandboxed runs of `make pilot-proxy-demo-adapter-failed-shared-visibility-smoke` and `make pilot-header-demo-adapter-failed-shared-visibility-smoke` both passed end to end on 2026-03-20 local time, producing persisted run timestamps `2026-03-21T04:34:36Z`, `2026-03-21T04:34:36Z`, `2026-03-21T04:35:13Z`, and `2026-03-21T04:35:13Z`
- A new structured site-rejection smoke mode now verifies persisted FHIR and HL7 `site_scope_rejection` audit detail plus zero run-specific visible cases without requiring a reviewer round-trip
- Unsandboxed runs of `make pilot-proxy-demo-adapter-site-rejection-smoke` and `make pilot-header-demo-adapter-site-rejection-smoke` both passed end to end on 2026-03-20 local time, producing persisted run IDs `31`, `32`, `33`, and `34` with UTC timestamps `2026-03-21T04:49:33Z`, `2026-03-21T04:49:33Z`, `2026-03-21T04:50:48Z`, and `2026-03-21T04:50:48Z`
- A new structured audit-visibility smoke mode now verifies owner access plus alternate-actor denial for persisted FHIR and HL7 `site_scope_rejection` runs across both import-run audit endpoints
- Unsandboxed runs of `make pilot-proxy-demo-adapter-audit-visibility-smoke` and `make pilot-header-demo-adapter-audit-visibility-smoke` both passed end to end on 2026-03-20 local time, producing persisted run IDs `36`, `37`, `38`, and `39` with UTC timestamps `2026-03-21T05:19:26Z`, `2026-03-21T05:19:26Z`, `2026-03-21T05:21:57Z`, and `2026-03-21T05:21:57Z`
- A new hosted pilot smoke workflow now reuses the existing base proxy and header Make targets on manual dispatch and a weekly schedule
- Unsandboxed reruns of `make pilot-proxy-demo-smoke` and `make pilot-header-demo-smoke` both passed end to end on 2026-03-20 local time, producing persisted run IDs `40` and `41` with UTC timestamps `2026-03-21T05:46:27Z` and `2026-03-21T05:47:33Z`
- The checked-in hosted workflow under `.github/workflows/pilot-smoke.yml` now also reuses the report-path site-rejection targets, installs API dependencies, and then runs those same overlay targets in GitHub Actions, but its first GitHub-hosted execution is still pending
- Unsandboxed reruns of `make pilot-proxy-demo-site-rejection-smoke` and `make pilot-header-demo-site-rejection-smoke` both passed end to end on 2026-03-22 local time, producing persisted run IDs `42` and `43` with UTC timestamps `2026-03-23T05:05:47Z` and `2026-03-23T05:06:23Z`

## What Is Implemented By Phase

### Phase 0-3

- API and web boot cleanly
- Demo data import works
- Deterministic triage persists `Case`, `Report`, `Finding`, and `ReviewAction`
- Reviewer queue and case detail flow are live
- Evaluation, exports, benchmark scripts, and reproducible validation are in place

### Phase 4

- Explainable PDAC trial matching is implemented
- Case detail shows structured abstractions and eligibility traces

### Phase 5

- Hybrid explainable scoring is implemented
- Worklist supports hybrid review priority, active-learning priority, disagreement queueing, threshold evaluation, and reviewer feedback capture

### Phase 6

- Structured request logging and readiness probes are implemented
- Trusted proxy auth is implemented with provider presets (`generic`, `authentik`, `keycloak`, `oauth2-proxy`)
- Role and site-scope enforcement are implemented in the API and reflected in the UI
- Pilot Docker overlays and smoke scripts are in place
- Research-safe de-identification views and redacted exports are implemented
- FHIR `DiagnosticReport` and HL7 v2 ORU import adapters are implemented
- Imported reports now preserve explicit provenance fields: patient identifier, encounter identifier, accession number, ordering provider, source system, source format, and import source identifier
- The metadata is persisted on reports, exposed in case detail and exports, and pseudonymized in research-safe views
- The generic CSV / JSON import path also accepts the same metadata surface
- Import endpoints now persist import-run summaries with actor, timestamps, processed / created / updated / failed counts, and stable failure buckets
- Analyst-facing audit routes are implemented at `/api/v1/imports/runs` and `/api/v1/imports/runs/{run_id}`
- Audit visibility respects auth plus site scope, while still allowing actors to review their own failed runs
- Selected FHIR and HL7 metadata precedence rules are now configurable through deployment settings rather than code edits
- The Next.js app now exposes `/imports` for CSV / JSON / JSONL uploads, FHIR `DiagnosticReport` submission, HL7 ORU submission, recent run summaries, and per-run failure details
- Failed import responses now include `X-Import-Run-ID` when an audit run was recorded, allowing the web workspace to load stable failure buckets immediately
- Checked-in env bundles now exist for local mock development, the proxy demo overlay, and a new header-auth demo overlay
- A new `docker-compose.pilot.header-demo.yml` overlay now demonstrates site-scoped field-level header auth with a fixed navigator identity
- The smoke helper and Make targets now support both proxy and header auth demos, and both pilot smoke paths verify that `/imports` renders
- The header-demo smoke path now imports demo data through `/api/v1/imports/reports` and verifies the persisted run through `/api/v1/imports/runs/{run_id}`
- The header-demo pilot path now also has live FHIR and HL7 smoke targets that verify structured adapter imports plus persisted audit detail end to end
- The header-demo pilot path now also has a live site-scope rejection smoke target that verifies a persisted failure bucket and zero run-specific visible cases
- The header-demo pilot path now also has a live malformed-report smoke target that verifies persisted `validation_error` plus `parse_error` buckets and zero run-specific visible cases
- The header-demo pilot path now also has a live adapter-failure smoke target that verifies persisted FHIR `unsupported_payload` plus HL7 `parse_error` buckets and zero run-specific visible cases
- The header-demo pilot path now also has a live shared-visibility smoke target that verifies owner visibility plus alternate-actor allow behavior for a successful `/api/v1/imports/reports` run
- The header-demo pilot path now also has a live failed-run shared-visibility smoke target that verifies owner visibility plus alternate-actor allow behavior for a persisted `/api/v1/imports/reports` `validation_error` run
- The header-demo pilot path now also has a live structured failed-run shared-visibility smoke target that verifies owner visibility plus alternate-actor allow behavior for persisted FHIR `unsupported_payload` and HL7 `parse_error` runs
- The header-demo pilot path now also has a live structured shared-visibility smoke target that verifies owner visibility plus alternate-actor allow behavior for successful FHIR and HL7 imports
- The header-demo pilot path now also has a live audit-visibility smoke target that verifies owner visibility plus alternate-actor denial for a persisted `site_scope_rejection` run
- The proxy-demo overlay now uses a fixed site-scoped navigator identity too, and its smoke path imports demo data through `/api/v1/imports/reports` with persisted run verification
- The proxy-demo pilot path now also has live FHIR and HL7 smoke targets that verify structured adapter imports plus persisted audit detail end to end
- The proxy-demo pilot path now also has a live site-scope rejection smoke target that verifies a persisted failure bucket and zero run-specific visible cases
- The proxy-demo pilot path now also has a live malformed-report smoke target that verifies persisted `validation_error` plus `parse_error` buckets and zero run-specific visible cases
- The proxy-demo pilot path now also has a live adapter-failure smoke target that verifies persisted FHIR `unsupported_payload` plus HL7 `parse_error` buckets and zero run-specific visible cases
- The proxy-demo pilot path now also has a live shared-visibility smoke target that verifies owner visibility plus alternate-actor allow behavior for a successful `/api/v1/imports/reports` run
- The proxy-demo pilot path now also has a live failed-run shared-visibility smoke target that verifies owner visibility plus alternate-actor allow behavior for a persisted `/api/v1/imports/reports` `validation_error` run
- The proxy-demo pilot path now also has a live structured failed-run shared-visibility smoke target that verifies owner visibility plus alternate-actor allow behavior for persisted FHIR `unsupported_payload` and HL7 `parse_error` runs
- The proxy-demo pilot path now also has a live structured shared-visibility smoke target that verifies owner visibility plus alternate-actor allow behavior for successful FHIR and HL7 imports
- The proxy-demo pilot path now also has a live audit-visibility smoke target that verifies owner visibility plus alternate-actor denial for a persisted `site_scope_rejection` run
- GitHub Actions now also has a hosted pilot smoke workflow for the base proxy and header success-path overlays plus report-path and structured adapter site rejection in both auth modes

## Important Guardrails

- Preserve deterministic explainability. Do not replace the rule engine with opaque behavior.
- Keep all new ingestion paths mapped into the existing `ReportInput` plus `triage_report()` flow unless there is a strong reason to introduce a new persistence boundary.
- Keep auth, site scoping, and de-identification behavior intact for any new API surfaces.
- Do not regress reviewer usability in favor of backend purity. The worklist and case detail pages are central product surfaces.
- Do not claim clinical validation. This remains a research-first pilot stack.

## Most Important Files

### Core triage and evaluation

- `apps/api/app/services/triage_engine.py`
- `apps/api/app/services/hybrid_analysis.py`
- `apps/api/app/services/evaluation.py`
- `apps/api/app/store/memory_store.py`
- `apps/api/app/models/entities.py`
- `scripts/run_demo_eval.py`
- `scripts/validate_repo.py`

### Reviewer workflow and exports

- `apps/api/app/api/routes/cases.py`
- `apps/api/app/api/routes/exports.py`
- `apps/api/app/schemas/case.py`
- `apps/api/app/schemas/feedback.py`
- `apps/web/app/cases/page.tsx`
- `apps/web/app/cases/[caseId]/page.tsx`
- `apps/web/app/imports/page.tsx`
- `apps/web/app/imports/actions.ts`
- `apps/web/lib/api.ts`

### Deployment, auth, and pilot path

- `README.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `docs/RELEASE_READINESS.md`
- `apps/api/app/main.py`
- `apps/api/app/api/routes/health.py`
- `apps/api/app/auth/dependencies.py`
- `apps/api/app/core/config.py`
- `apps/api/app/observability/logging.py`
- `docker-compose.yml`
- `docker-compose.pilot.yml`
- `docker-compose.pilot.header-demo.yml`
- `docker-compose.pilot.proxy-demo.yml`
- `deploy/examples/README.md`
- `scripts/smoke_proxy_auth.py`
- `Makefile`

### De-identification and research surfaces

- `apps/api/app/services/deidentification.py`
- `apps/api/app/schemas/research.py`
- `apps/api/app/api/routes/cases.py`
- `apps/web/app/cases/[caseId]/research/page.tsx`

### Integration adapters

- `apps/api/app/api/routes/imports.py`
- `apps/api/app/services/imports.py`
- `apps/api/app/services/fhir_imports.py`
- `apps/api/app/services/hl7_imports.py`
- `apps/api/app/db/session.py`
- `apps/api/app/models/entities.py`
- `apps/api/app/schemas/imports.py`
- `apps/api/app/schemas/triage.py`
- `apps/api/tests/test_imports.py`
- `apps/api/tests/test_import_runs.py`

## Recommended Next Slice

Proceed with a hosted structured adapter audit-visibility smoke expansion.

### Why this is next

- The base proxy and header success-path pilot smokes plus the report-path and structured adapter site-rejection flows are now wired into a checked-in hosted workflow, so the highest-value remaining CI gap is structured audit-denial coverage for persisted FHIR and HL7 adapter failures.
- The existing structured adapter audit-visibility smoke targets are already live, deterministic, and comparatively cheap because they keep visible-case assertions at zero and avoid reviewer round-trips.
- Promoting one or both structured adapter audit-visibility paths into hosted automation would strengthen auth and site-scope confidence without changing product behavior or inventing a second smoke harness.

### Target outcome

Add hosted structured audit-denial smoke automation that:
- runs at least one existing `make pilot-*-adapter-audit-visibility-smoke` target in GitHub Actions
- keeps the current hosted base plus report-path and structured adapter site-rejection workflow intact and the existing local Make targets as the source-of-truth operational path
- stays scoped honestly so the docs still distinguish hosted base, hosted report-path failure, hosted structured site-rejection, and hosted structured audit-denial coverage from the broader manual smoke matrix
- documents which shared-visibility and other higher-cost failure checks still remain manual after the new hosted expansion

### Suggested implementation shape

1. Extend the existing hosted smoke workflow or add a tightly scoped sibling workflow rather than folding Docker overlay execution into the fast PR validation job.

2. Reuse the existing `make pilot-*-adapter-audit-visibility-smoke` targets as the workflow entrypoints so local and hosted smoke behavior stay aligned.

3. Keep the workflow readable:
   - boot one overlay at a time
   - run the relevant audit-visibility smoke target against `localhost`
   - tear the overlay down even on failure
   - start with one or two high-value structured auth-sensitive paths rather than the entire matrix

4. Keep the smoke assertions operational:
   - the existing manual smoke targets remain usable locally
   - hosted smoke output makes it obvious which overlay and target ran
   - docs explain any intentionally manual validation that remains outside hosted smoke coverage

5. Prefer additive workflow and docs updates over new runtime abstractions.

### Acceptance criteria

- At least one hosted structured adapter audit-visibility pilot smoke target is wired into GitHub Actions.
- The hosted workflow configuration is checked in and documented honestly.
- Release-facing docs explain what hosted smoke now covers and what still requires manual live validation.
- `make validate-strict` passes.
- Local live validation is rerun for any newly hosted structured audit-visibility target, and if GitHub-hosted execution is not run yet that gap is called out explicitly.
- If workflow scope changes validation posture materially, update the release-facing docs in the same change set.

## Good First Commands For The Next Agent

```bash
make validate-strict
sed -n '1,260p' docs/PHASES.md
sed -n '1,260p' docs/API_SPEC.md
sed -n '1,260p' docs/DEPLOYMENT.md
sed -n '1,220p' .github/workflows/pilot-smoke.yml
sed -n '1,260p' scripts/smoke_proxy_auth.py
sed -n '1,260p' apps/api/app/services/fhir_imports.py
sed -n '1,260p' apps/api/app/services/hl7_imports.py
sed -n '1,260p' docker-compose.pilot.yml
sed -n '1,260p' docker-compose.pilot.header-demo.yml
sed -n '1,260p' docker-compose.pilot.proxy-demo.yml
find deploy/examples -maxdepth 2 -type f | sort
make pilot-header-demo-up
make pilot-header-demo-smoke
make pilot-header-demo-shared-visibility-smoke
make pilot-header-demo-failed-shared-visibility-smoke
make pilot-header-demo-adapter-shared-visibility-smoke
make pilot-header-demo-adapter-failed-shared-visibility-smoke
make pilot-header-demo-adapter-site-rejection-smoke
make pilot-header-demo-adapter-audit-visibility-smoke
make pilot-header-demo-fhir-smoke
make pilot-header-demo-hl7-smoke
make pilot-header-demo-site-rejection-smoke
make pilot-header-demo-parse-validation-smoke
make pilot-header-demo-adapter-failure-smoke
make pilot-header-demo-audit-visibility-smoke
make pilot-proxy-demo-up
make pilot-proxy-demo-smoke
make pilot-proxy-demo-shared-visibility-smoke
make pilot-proxy-demo-failed-shared-visibility-smoke
make pilot-proxy-demo-adapter-shared-visibility-smoke
make pilot-proxy-demo-adapter-failed-shared-visibility-smoke
make pilot-proxy-demo-adapter-site-rejection-smoke
make pilot-proxy-demo-adapter-audit-visibility-smoke
make pilot-proxy-demo-fhir-smoke
make pilot-proxy-demo-hl7-smoke
make pilot-proxy-demo-site-rejection-smoke
make pilot-proxy-demo-parse-validation-smoke
make pilot-proxy-demo-adapter-failure-smoke
make pilot-proxy-demo-audit-visibility-smoke
```

## Handoff Summary

This is a clean checkpoint. The repo is runnable, validated, and already beyond MVP scaffolding. Import metadata preservation, import-run audit trails, config overrides, the web import workspace, concrete proxy plus header-auth pilot packaging, automatic PR and `main` validation, checked-in hosted base plus report-path and structured adapter site-rejection pilot smoke automation, and live generic plus structured success, failed shared-visibility, site-scope rejection, parse or validation failure, adapter failure, and audit-visibility denial smoke coverage in both pilot auth modes are complete, so the next agent should focus on promoting structured adapter audit-denial paths into hosted smoke coverage and tightening release hygiene rather than missing product fundamentals.
