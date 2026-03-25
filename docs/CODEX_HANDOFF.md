# Codex Handoff

Updated: 2026-03-25

This repository is no longer in early MVP scaffolding. The core research prototype is implemented and validated, and the best next work is now Phase 6 interoperability hardening on top of the existing pilot packaging, proof surfaces, public benchmark pack, and external evaluation bundle writer.

## Current State

- Deterministic pancreatic triage is implemented with section-aware sentence evidence, rationale codes, persistence, exports, and evaluation.
- Reviewer workflow is implemented end to end with worklist filters, case detail, review actions, feedback capture, hybrid prioritization, and trial matching.
- Phase 6 pilot work is materially in place: observability, readiness probes, trusted-proxy auth, site scoping, pilot Docker overlays, checked-in env bundles, de-identified research views, FHIR ingestion, HL7 ORU ingestion, structured import metadata persistence, persisted import-run audit records, env-driven field-preference overrides for upstream variability, a dedicated web import workspace with recent-run audit visibility, and live report/FHIR/HL7 success, successful shared-visibility, report-path failed shared-visibility for `validation_error`, structured failed shared-visibility for FHIR `unsupported_payload` plus HL7 `parse_error`, report-path and structured-adapter site-scope rejection, report-path parse/validation, adapter-specific malformed-import, and generic plus structured cross-actor audit denial smoke coverage in both the header-auth and trusted-proxy pilot paths.
- The web app now has clearer outside-collaborator surfaces: the home and about pages frame the product as an explainable, benchmarkable workflow stack, and `/proof` publishes the checked-in demo benchmark snapshot as a public proof surface.
- The repo now includes an adoption-facing quickstart, a checked-in benchmark snapshot in `docs/examples/demo-benchmark-current.*`, and a refresh path through `make benchmark-demo` plus `make refresh-demo-proof`.
- The repo also now includes a public benchmark pack: `docs/LABELING_GUIDE.md`, `docs/BENCHMARK_SUBMISSIONS.md`, checked-in label and submission templates, a Pydantic benchmark submission schema, and a validator entrypoint through `make validate-benchmark-submission SUBMISSION=...`.
- The repo now also includes a comparable external evaluation bundle writer through `scripts/run_external_eval.py` plus `make benchmark-external`, producing JSON, Markdown, and validator-compatible submission-draft artifacts from label and prediction JSONL inputs.
- FHIR `DiagnosticReport` imports now preserve patient, encounter, and accession metadata from inline `Reference.identifier` values when upstream payloads omit fully resolved `Patient`, `Encounter`, or `ServiceRequest` resources.
- FHIR `DiagnosticReport` imports now also decode supported text-like `presentedForm` attachments, including base64 XHTML narratives with explicit charsets, and keep unsectioned attachment findings merged with `conclusion` text when that preserves a more reviewer-usable report shape.
- HL7 ORU imports now decode base64 `ED` report text, normalize repeated `OBX-5` values, respect custom `MSH-2` component plus repetition separators, normalize common HL7 escape sequences, and clean composite metadata fields with subcomponent-aware extraction before the existing report-text assembly flows into triage and audit persistence.
- Top-level repo docs now reflect the implemented platform instead of the earlier scaffold framing, and the repository includes checked-in contributor, security, and code-of-conduct docs appropriate for a near-1.0 open-source handoff.
- The repo still includes checked-in GitHub Actions workflows for strict validation plus hosted base, attachment-backed FHIR success-path, report-path site-rejection, and structured adapter site-rejection pilot smoke coverage, but that hosted/manual smoke split is now supporting operational context rather than the primary roadmap driver.
- The highest-value remaining work is not bootstrapping. It is deeper FHIR and HL7 interoperability coverage first, then broader pilot operability, without breaking explainability.

## Fresh Validation Status

Confirmed on 2026-03-25:

- `make validate-strict` passes
- Summary: `9 pass, 0 warn, 0 fail`
- API tests: `121 passed`
- `apps/api/.venv/bin/python -m pytest apps/api/tests/test_smoke_proxy_auth.py -q` passed with `21 passed`, covering the attachment-backed FHIR smoke fixture and its expected `presentedForm` payload shape
- An API-only local rerun of the proxy attachment-backed FHIR smoke passed on 2026-03-25, recording import run `48` completed at `2026-03-25T17:13:02.907406Z` with one visible case plus a successful reviewer round-trip
- An API-only local rerun of the header-auth attachment-backed FHIR smoke passed on 2026-03-25, recording import run `49` completed at `2026-03-25T17:14:13.069507Z` with one visible case plus a successful reviewer round-trip
- Those two reruns intentionally booted only the pilot `db` and `api` services because an unrelated local Next dev server was already bound to host port `3000`, so the full web checks from `make pilot-*-fhir-smoke` were not repeated in this slice
- Web checks: `npm run lint` and `npm run build` now both pass through `make validate-strict`
- Demo evaluation compare and sweep both run through the validation script
- `make refresh-demo-proof` succeeded and refreshed the checked-in benchmark snapshot that powers `/proof`
- `make validate-benchmark-submission SUBMISSION=docs/examples/benchmark-submission-template.json` passed
- `cd apps/api && .venv/bin/python -m pytest tests/test_benchmark_submission.py -q` passed
- `make benchmark-external LABELS=docs/examples/benchmark-label-template.jsonl PREDICTIONS=docs/examples/benchmark-prediction-template.jsonl OUT_DIR=/tmp/pancreatic-signal-external-eval BASENAME=template-external TOP_K=2` passed and wrote JSON, Markdown, and submission-draft artifacts
- `make validate-benchmark-submission SUBMISSION=/tmp/pancreatic-signal-external-eval/template-external-submission.json` passed against the generated draft
- `apps/api/.venv/bin/python -m pytest apps/api/tests/test_imports.py apps/api/tests/test_import_runs.py -q` passed with `46 passed`, including inline `Reference.identifier` extraction coverage, attachment-backed `presentedForm` decoding and audit coverage, plus custom `MSH-2` delimiter, escape-sequence, subcomponent, and audit-visibility coverage
- Targeted import / de-identification / export coverage also passes for the new import metadata surface
- Import-run audit coverage now passes for success, update counts, validation failures, unsupported payloads, site-scope rejection, and audit-route access control
- Config-override coverage now passes for one FHIR field-preference override and one HL7 field-preference override while preserving defaults
- The new `/imports` workspace is included in the validated web build and uses persisted run IDs to deep-link failed submissions into their audit detail
- The published demo proof currently includes a checked-in JSON plus Markdown benchmark summary for outside collaborators, and the web app reads that snapshot directly
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
- The latest strict validation pass was rerun after widening the hosted pilot smoke workflow to include the attachment-backed FHIR success path and remains green
- GitHub Actions now runs `make validate-strict` on pull requests, on `main`, and through manual workflow dispatch using a checked-in workflow under `.github/workflows/validate.yml`
- The smoke helper's FHIR demo path now uses an attachment-backed `DiagnosticReport.presentedForm` XHTML narrative encoded as base64 UTF-16, so the existing `pilot-*-fhir-smoke` targets exercise the same supported text-like attachment decode path covered by API tests
- A checked-in workflow under `.github/workflows/pilot-smoke.yml` now reuses `make pilot-proxy-demo-smoke`, `make pilot-proxy-demo-fhir-smoke`, `make pilot-proxy-demo-site-rejection-smoke`, `make pilot-proxy-demo-adapter-site-rejection-smoke`, `make pilot-header-demo-smoke`, `make pilot-header-demo-fhir-smoke`, `make pilot-header-demo-site-rejection-smoke`, and `make pilot-header-demo-adapter-site-rejection-smoke` on manual dispatch plus a weekly Monday schedule; it remains intentionally narrower than the full manual visibility and failure-path overlay matrix
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

### Benchmark proof and public comparison surfaces

- `apps/web/app/page.tsx`
- `apps/web/app/about/page.tsx`
- `apps/web/app/proof/page.tsx`
- `apps/web/app/marketing.module.css`
- `apps/web/lib/demo-proof.ts`
- `apps/api/app/schemas/benchmark_submission.py`
- `apps/api/app/schemas/evaluation.py`
- `apps/api/tests/test_external_evaluation.py`
- `scripts/run_external_eval.py`
- `scripts/write_demo_benchmark.py`
- `scripts/validate_benchmark_submission.py`
- `docs/QUICKSTART.md`
- `docs/EVALUATION.md`
- `docs/BENCHMARK_SUBMISSIONS.md`
- `docs/LABELING_GUIDE.md`
- `docs/examples/demo-benchmark-current.json`
- `docs/examples/demo-benchmark-current.md`
- `docs/examples/benchmark-submission-template.json`
- `docs/examples/benchmark-label-template.jsonl`
- `docs/examples/benchmark-prediction-template.jsonl`

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

Record the first GitHub-hosted attachment-backed FHIR success run, then decide whether the hosted pilot matrix should expand to HL7 success-path coverage.

### Why this is next

- The attachment-backed FHIR `presentedForm` path is now covered in parser tests, the smoke helper fixture, the hosted workflow definition, and fresh local proxy plus header-auth reruns.
- What is still missing is a recorded GitHub-hosted execution of the widened `pilot-smoke` workflow so the repo has both local and hosted evidence for the new fixture.
- HL7 success-path hosting is still manual, and that decision should be made with actual hosted runtime and stability information from the widened FHIR matrix rather than guesswork.

### Target outcome

Add one hosted-operability slice that:
- records the first green GitHub-hosted attachment-backed FHIR success-path run with its exact workflow date or link
- decides explicitly whether HL7 success-path coverage should stay manual or be promoted into the hosted weekly smoke matrix
- updates the handoff and deployment-facing notes with that hosted decision
- leaves the benchmark, reviewer, and import audit surfaces unchanged

### Suggested implementation shape

1. Start with the existing `.github/workflows/pilot-smoke.yml` matrix rather than creating a second hosted workflow.

2. Once a green hosted FHIR run exists, record that exact run in this handoff and compare its duration and stability to the current weekly smoke budget.

3. If the hosted FHIR expansion stays stable, consider mirroring the same promotion for `pilot-proxy-demo-hl7-smoke` and `pilot-header-demo-hl7-smoke`.

4. If hosted runtime or flakiness becomes a concern, explicitly document that HL7 remains manual and keep the workflow narrower on purpose.

### Acceptance criteria

- The handoff includes at least one exact GitHub-hosted attachment-backed FHIR success run.
- The hosted-versus-manual HL7 decision is documented, even if the answer is to defer it.
- Any workflow-matrix change still leaves `make validate-strict` green.
- The handoff distinguishes the new hosted evidence from the local API-only reruns already captured above.

## Good First Commands For The Next Agent

```bash
make validate-strict
sed -n '1,260p' docs/PHASES.md
sed -n '1,260p' docs/API_SPEC.md
sed -n '1,260p' docs/DEPLOYMENT.md
sed -n '1,260p' docs/OPEN_SOURCE_STRATEGY.md
sed -n '1,260p' README.md
sed -n '1,260p' docs/RELEASE_READINESS.md
sed -n '1,260p' apps/api/app/services/hl7_imports.py
sed -n '1,260p' apps/api/tests/test_imports.py
sed -n '1,260p' apps/api/tests/test_import_runs.py
sed -n '1,260p' scripts/smoke_proxy_auth.py
sed -n '1,220p' .github/workflows/pilot-smoke.yml
make benchmark-external LABELS=docs/examples/benchmark-label-template.jsonl PREDICTIONS=docs/examples/benchmark-prediction-template.jsonl
make validate-benchmark-submission SUBMISSION=docs/examples/benchmark-submission-template.json
```

## Handoff Summary

This is a clean checkpoint. The repo is runnable, validated, and already beyond MVP scaffolding. Import metadata preservation, import-run audit trails, config overrides, the web import workspace, concrete proxy plus header-auth pilot packaging, automatic PR and `main` validation, checked-in hosted base plus attachment-backed FHIR success-path plus report-path and structured adapter site-rejection smoke automation, a sharper public landing experience, a checked-in benchmark proof surface, a machine-validated public benchmark submission pack, a reproducible external evaluation bundle writer, FHIR inline `Reference.identifier` fallback coverage, FHIR `presentedForm` attachment-backed narrative decoding, and HL7 `ED`, repeated-`OBX-5`, custom-`MSH-2` delimiter, escape-sequence, plus subcomponent-aware metadata support are complete. Fresh local proxy and header-auth reruns now also confirm the attachment-backed FHIR smoke path operationally with persisted runs `48` and `49`. The next agent should focus on recording the first green hosted FHIR success run and then making an explicit HL7-hosting decision, rather than reopening parser work that is now already covered in tests.
