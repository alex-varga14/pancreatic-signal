# Changelog

All notable project-level changes should be documented in this file.

This repository is still pre-release, but the goal is to keep the path to a research-first `1.0` understandable for maintainers, collaborators, and downstream evaluators.

## Unreleased

### Added

- Repo-level contributor, security, and community docs in [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- A clearer public project narrative in [README.md](README.md) and [docs/OPEN_SOURCE_STRATEGY.md](docs/OPEN_SOURCE_STRATEGY.md)
- A release-readiness checklist in [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md)
- An adoption-facing quickstart in [docs/QUICKSTART.md](docs/QUICKSTART.md) plus a checked-in published benchmark snapshot in [`docs/examples/demo-benchmark-current.md`](docs/examples/demo-benchmark-current.md)
- GitHub Actions pull request and `main` validation via [`.github/workflows/validate.yml`](.github/workflows/validate.yml) using `make validate-strict`
- A hosted pilot smoke workflow in [`.github/workflows/pilot-smoke.yml`](.github/workflows/pilot-smoke.yml) that reuses the base proxy and header overlay smoke targets plus the report-path and structured adapter site-rejection variants on manual dispatch and a weekly schedule
- Live failed-run shared-visibility smoke coverage for a persisted non-site `validation_error` import run in the proxy and header pilot overlays
- Live structured adapter failed-run shared-visibility smoke coverage for persisted non-site FHIR `unsupported_payload` and HL7 `parse_error` runs in the proxy and header pilot overlays
- Live structured adapter site-scope rejection smoke coverage for persisted FHIR and HL7 `site_scope_rejection` runs in the proxy and header pilot overlays
- Live structured adapter audit-visibility smoke coverage for persisted FHIR and HL7 `site_scope_rejection` runs in the proxy and header pilot overlays

### Changed

- The Next.js home and about surfaces now present Pancreatic Signal as a benchmarkable product entrypoint instead of a bare scaffold shell, and the web app now exposes a dedicated `/proof` page backed by the checked-in benchmark snapshot
- Top-level documentation now describes the implemented research platform instead of the earlier scaffold-era state
- Deployment and API docs now call out cross-actor visibility for non-site failed import runs with empty `imported_sites`
- `make validate-strict` now includes web lint alongside Python checks, API tests, evaluation checks, and the web build so local and hosted validation stay aligned
- The validation and deployment docs now distinguish between hosted base plus report-path and structured adapter site-rejection automation and the broader manual overlay smoke matrix

### Validated

- `make validate-strict` passed on 2026-03-22 with `9 pass, 0 warn, 0 fail`
- API validation reported `101 passed`
- Local reruns of `make pilot-proxy-demo-smoke` and `make pilot-header-demo-smoke` passed on 2026-03-20 local time with persisted run IDs `40` and `41`, matching the checked-in hosted workflow targets
- Local reruns of `make pilot-proxy-demo-site-rejection-smoke` and `make pilot-header-demo-site-rejection-smoke` passed on 2026-03-22 local time with persisted run IDs `42` and `43`, matching the newly hosted failure-path targets
- Local reruns of `make pilot-proxy-demo-adapter-site-rejection-smoke` and `make pilot-header-demo-adapter-site-rejection-smoke` passed on 2026-03-22 local time with persisted run IDs `44`, `45`, `46`, and `47`, matching the newly hosted structured failure-path targets
- Live structured adapter site-scope rejection and audit-visibility smoke runs passed for both trusted-proxy and header-auth overlays and are recorded in [docs/CODEX_HANDOFF.md](docs/CODEX_HANDOFF.md)

## 0.9.0-preview - 2026-03-20

This preview marker captures the repo state before a formal `1.0` release process begins.

### Added

- Deterministic pancreatic triage with evidence spans, rationale codes, persistence, exports, and reproducible evaluation
- Reviewer workflow with worklist filters, case detail, review actions, hybrid prioritization, feedback capture, and research-safe views
- FHIR `DiagnosticReport`, HL7 ORU, and generic report import paths with structured provenance metadata
- Import-run audit summaries and detail routes with stable failure buckets and visibility controls
- Env-driven field-preference overrides for selected FHIR and HL7 metadata extraction
- Dedicated `/imports` web workspace for file uploads, structured submissions, and audit inspection
- Pilot-ready Docker overlays for trusted-proxy and header-auth demos
- Live smoke coverage for report, FHIR, and HL7 import success paths
- Live smoke coverage for site-scope rejection, parse or validation failure, adapter failure, audit denial, shared visibility, and structured shared visibility

### Changed

- The proxy pilot demo now defaults to an import-capable navigator identity so `/imports` and pilot smoke paths exercise the same capability class
- Top-level handoff documentation now reflects late Phase 6 hardening rather than early MVP bootstrap work

### Validated

- `make validate-strict` passed on 2026-03-20 with `8 pass, 0 warn, 0 fail`
- API validation reported `90 passed`
- Live pilot smoke runs passed for both trusted-proxy and header-auth overlays across the documented success and failure paths recorded in [docs/CODEX_HANDOFF.md](docs/CODEX_HANDOFF.md)
