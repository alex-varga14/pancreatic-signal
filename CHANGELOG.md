# Changelog

All notable project-level changes should be documented in this file.

This repository is still pre-release, but the goal is to keep the path to a research-first `1.0` understandable for maintainers, collaborators, and downstream evaluators.

## Unreleased

### Added

- Repo-level contributor, security, and community docs in [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- A clearer public project narrative in [README.md](README.md) and [docs/OPEN_SOURCE_STRATEGY.md](docs/OPEN_SOURCE_STRATEGY.md)
- A release-readiness checklist in [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md)
- Live failed-run shared-visibility smoke coverage for a persisted non-site `validation_error` import run in the proxy and header pilot overlays
- Live structured adapter failed-run shared-visibility smoke coverage for persisted non-site FHIR `unsupported_payload` and HL7 `parse_error` runs in the proxy and header pilot overlays

### Changed

- Top-level documentation now describes the implemented research platform instead of the earlier scaffold-era state
- Deployment and API docs now call out cross-actor visibility for non-site failed import runs with empty `imported_sites`

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
