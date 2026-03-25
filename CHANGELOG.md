# Changelog

All notable project-level changes should be documented in this file.

This repository is still pre-release, but the goal is to keep the path to a research-first `1.0` understandable for maintainers, collaborators, and downstream evaluators.

## Unreleased

### Added

- Repo-level contributor, security, and community docs in [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- A release-facing runbook in [docs/RELEASE_RUNBOOK.md](docs/RELEASE_RUNBOOK.md) plus a release notes scaffold in [docs/RELEASE_NOTES_TEMPLATE.md](docs/RELEASE_NOTES_TEMPLATE.md) so maintainers can move from validation to hosted smoke evidence capture without private context
- A clearer public project narrative in [README.md](README.md) and [docs/OPEN_SOURCE_STRATEGY.md](docs/OPEN_SOURCE_STRATEGY.md)
- A release-readiness checklist in [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md)
- An adoption-facing quickstart in [docs/QUICKSTART.md](docs/QUICKSTART.md) plus a checked-in published benchmark snapshot in [`docs/examples/demo-benchmark-current.md`](docs/examples/demo-benchmark-current.md)
- A public benchmark pack with [docs/LABELING_GUIDE.md](docs/LABELING_GUIDE.md), [docs/BENCHMARK_SUBMISSIONS.md](docs/BENCHMARK_SUBMISSIONS.md), validated submission templates, and a benchmark submission validator
- A comparable external evaluation bundle writer in [`scripts/run_external_eval.py`](scripts/run_external_eval.py), a `make benchmark-external` entrypoint, and a checked-in prediction template for outside collaborators
- GitHub Actions pull request and `main` validation via [`.github/workflows/validate.yml`](.github/workflows/validate.yml) using `make validate-strict`
- A hosted pilot smoke workflow in [`.github/workflows/pilot-smoke.yml`](.github/workflows/pilot-smoke.yml) that reuses the base and FHIR proxy and header overlay smoke targets plus the report-path and structured adapter site-rejection variants on manual dispatch and a weekly schedule
- A narrower manual-dispatch path in [`.github/workflows/pilot-smoke.yml`](.github/workflows/pilot-smoke.yml) for hosted attachment-backed FHIR confirmation, plus uploaded per-job smoke log artifacts for later run auditing
- A structured hosted smoke summary generator in [`scripts/summarize_pilot_smoke.py`](scripts/summarize_pilot_smoke.py) plus workflow-uploaded JSON and Markdown summary artifacts for later handoff capture
- A manual-only `hl7-success-only` dispatch path in [`.github/workflows/pilot-smoke.yml`](.github/workflows/pilot-smoke.yml) so hosted HL7 success-path trials can be recorded without widening the default weekly matrix
- Live failed-run shared-visibility smoke coverage for a persisted non-site `validation_error` import run in the proxy and header pilot overlays
- Live structured adapter failed-run shared-visibility smoke coverage for persisted non-site FHIR `unsupported_payload` and HL7 `parse_error` runs in the proxy and header pilot overlays
- Live structured adapter site-scope rejection smoke coverage for persisted FHIR and HL7 `site_scope_rejection` runs in the proxy and header pilot overlays
- Live structured adapter audit-visibility smoke coverage for persisted FHIR and HL7 `site_scope_rejection` runs in the proxy and header pilot overlays

### Changed

- The Next.js home and about surfaces now present Pancreatic Signal as a benchmarkable product entrypoint instead of a bare scaffold shell, and the web app now exposes a dedicated `/proof` page backed by the checked-in benchmark snapshot
- Benchmark-oriented contribution paths now have a documented label schema, stable error-bucket rubric, and a machine-validated submission format for outside collaborators
- Outside collaborators can now turn label and prediction JSONL files into JSON, Markdown, and submission-draft artifacts without hand-assembling benchmark metrics
- FHIR `DiagnosticReport` imports now preserve patient, encounter, and accession metadata from inline `Reference.identifier` values when upstream bundles omit fully resolved resources
- FHIR `DiagnosticReport` imports now decode supported text-like `presentedForm` attachments, including attachment-backed XHTML narratives, and keep unsectioned attachment findings merged with `conclusion` instead of dropping the conclusion text
- The proxy and header FHIR pilot smoke fixtures now submit attachment-backed `DiagnosticReport.presentedForm` XHTML narratives, so deployable smoke coverage exercises the supported text-like attachment decode path instead of only an `Observation`-backed structured result
- HL7 ORU imports now decode base64 `ED` report text, normalize repeated `OBX-5` values, respect custom `MSH-2` component and repetition separators, normalize common HL7 escape sequences, and clean composite metadata fields with subcomponent-aware extraction before triage
- Top-level documentation now describes the implemented research platform instead of the earlier scaffold-era state
- Deployment and API docs now call out cross-actor visibility for non-site failed import runs with empty `imported_sites`
- `make validate-strict` now includes web lint alongside Python checks, API tests, evaluation checks, and the web build so local and hosted validation stay aligned
- The validation and deployment docs now distinguish between hosted base plus report-path and structured adapter site-rejection automation and the broader manual overlay smoke matrix
- Hosted pilot smoke jobs now generate machine-readable and Markdown summary artifacts from `pilot-smoke.log`, so the first green attachment-backed FHIR run can be recorded without manual log scraping
- Hosted pilot smoke summaries now include smoke duration and exit code, and HL7 success-path coverage remains manual by default pending hosted trial evidence
- FHIR `DiagnosticReport` imports now merge multiple supported `presentedForm` attachments in order and suppress shorter overlapping fragments when a richer narrative attachment already contains them
- FHIR `DiagnosticReport` imports now also decode supported `presentedForm.url` attachments when they resolve to bundled or contained FHIR `Binary` resources
- FHIR `DiagnosticReport` imports now expand referenced `Observation.component` findings into report text so structured component-level pancreatic findings are preserved for triage
- FHIR `DiagnosticReport` imports now also expand grouped referenced `Observation.hasMember` findings into report text and fall back to `conclusionCode` text when a report omits free-text `conclusion`
- FHIR `DiagnosticReport` imports now also preserve referenced `Observation.interpretation` and `referenceRange` context for reviewer-visible pancreatic measurements, while avoiding duplicate or cyclic grouped-member expansion

### Validated

- `make validate-strict` passed on 2026-03-25 with `9 pass, 0 warn, 0 fail`
- API validation reported `134 passed` on 2026-03-25
- `apps/api/.venv/bin/python -m pytest apps/api/tests/test_imports.py -q` passed on 2026-03-25 with `34 passed`, including split, overlapping, bundled or contained `Binary`-backed FHIR `presentedForm`, grouped and cycle-safe `Observation.hasMember`, `conclusionCode`, measurement `interpretation` plus `referenceRange`, and `Observation.component` coverage
- `apps/api/.venv/bin/python -m pytest apps/api/tests/test_summarize_pilot_smoke.py apps/api/tests/test_smoke_proxy_auth.py -q` passed on 2026-03-25 with `23 passed`, covering the hosted smoke summary parser plus the attachment-backed FHIR smoke fixture shape
- `apps/api/.venv/bin/python -m pytest apps/api/tests/test_smoke_proxy_auth.py -q` passed on 2026-03-25 with `21 passed`, covering the attachment-backed FHIR smoke fixture shape
- API-only local reruns of the attachment-backed FHIR smoke path passed on 2026-03-25 in proxy mode and header-auth mode, recording persisted import runs `48` and `49` plus visible-case and reviewer round-trip verification
- The public GitHub Actions API reported `0` `Pilot Smoke` workflow runs on 2026-03-25, so hosted attachment-backed FHIR evidence is still pending even though the workflow is active
- `make benchmark-external LABELS=docs/examples/benchmark-label-template.jsonl PREDICTIONS=docs/examples/benchmark-prediction-template.jsonl OUT_DIR=/tmp/pancreatic-signal-external-eval BASENAME=template-external TOP_K=2` wrote JSON, Markdown, and submission-draft artifacts on 2026-03-24
- `make validate-benchmark-submission SUBMISSION=/tmp/pancreatic-signal-external-eval/template-external-submission.json` passed on 2026-03-24
- `apps/api/.venv/bin/python -m pytest apps/api/tests/test_imports.py apps/api/tests/test_import_runs.py -q` passed on 2026-03-24 with `46 passed`, including inline `Reference.identifier` FHIR coverage, attachment-backed `presentedForm` decoding and audit coverage, plus custom `MSH-2` HL7 delimiter, escape-sequence, subcomponent, and audit-visibility coverage
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
