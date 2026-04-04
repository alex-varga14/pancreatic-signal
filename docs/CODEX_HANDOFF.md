# Codex Handoff

Updated: 2026-04-04

This repository is no longer in early MVP scaffolding. The core research prototype is implemented and validated, Phase 6
hosted smoke evidence capture is now complete, and the codebase now also carries the research-intel branch-wrap work that
adds watchtower scheduling, audited watchtower automation, multi-run council comparison, contributor packets, richer
stress-test experiments, and explicit governance for paid-source or donation-funded expansion. The best next work should
now move from the expanded proof set and automated research-intel watchtower toward broader de-identified or externally
supplied benchmark inputs, longer-horizon discovery calibration, and deeper live corpus quality built on top of the
existing pilot packaging, proof surfaces, public benchmark pack, external evaluation bundle writer, and cited pancreatic
oncology watchtower.

## Current State

- Deterministic pancreatic triage is implemented with section-aware sentence evidence, rationale codes, persistence, exports, and evaluation.
- Reviewer workflow is implemented end to end with worklist filters, case detail, review actions, feedback capture, hybrid prioritization, and trial matching.
- A second primary pillar, Research Intelligence, is now implemented with a sibling `/research-intel` workspace, a `/api/v1/research-intel/*` namespace, seeded pancreatic oncology source and topic catalogs, a lightweight domain graph, persisted run audits, normalized research documents, cited evidence spans, topic watchlists, council digests, opportunity proposals, and case-level research briefs.
- Landing, about, quickstart, README, and handoff surfaces now frame Research Intelligence as the primary entry point, with triage, imports, benchmark proof, and case briefs positioned as explainable downstream applications of the discovery engine.
- The discovery layer now also includes watchtower scheduling and automation: broader curated literature and trial watches, due-only ingest support, schedule snapshots, consecutive-failure tracking, a `make research-intel-ingest-due` path, a `make research-intel-watchtower` path, an audited `/api/v1/research-intel/runs/watchtower` trigger, and a dedicated `/research-intel/schedule` workspace.
- Research-intel digests now compare themselves against recent runs, preserving confidence trend, disagreement deltas, recurring open questions, recurring disagreement points, and resolved items instead of treating each digest as a sealed one-off summary.
- Research-intel opportunities now carry contributor packets for issue, benchmark, dataset, rule, trial, case-brief, and tooling follow-through, with packet artifacts written under `artifacts/research-intel/packets/`.
- Safe experiment support is stronger too: benchmark and rule opportunities now expose both readiness and stress-test modes with dimension-level scoring, while still staying proposal-only and human-gated.
- Governance for paid-source access and donation-funded operations is now documented in `docs/RESEARCH_INTELLIGENCE_GOVERNANCE.md`, and autonomous payment or procurement remains explicitly out of scope.
- The research-intel watchtower is still fixture-first and operator-triggered for reproducibility, but it now also carries selectively live-ready curated connectors with pancreas-aware filtering and source-health tracking instead of remaining purely seeded.
- The watchtower can now run as one audited automation tick: schedule state is captured before and after each tick, digest generation is policy-gated to avoid synthetic churn, and a cache-backed GitHub Actions workflow under `.github/workflows/research-watchtower.yml` can preserve state across hosted runs.
- Phase 1 of the scientific-discovery pivot is now implemented: discovery ingest supports fixture-backed connector runs, selectively live-ready Europe PMC, ClinicalTrials.gov, NCI, FDA, and GitHub-backed open-source discovery connectors, source-health tracking, and per-document provenance plus novelty metadata.
- Phase 2 is now underway as well: the pancreatic oncology graph is richer, typed, family-aware, and exposed through graph-backed entity resolution plus a dedicated `/research-intel/graph` surface.
- Phase 3 is now underway as well: the research council persists independent opinions, peer critique, explicit confidence, open questions, evidence gaps, and next experiments.
- Phase 4 is now underway too: opportunities are now typed discovery-to-action specs with evidence bundles, measurable outcomes, downstream artifact hints, and artifact-backed promotion flows.
- Phase 5 is now underway too: benchmark and rule opportunities support safe experiment runs with keep-or-discard ratchet outcomes, experiment artifacts, and persisted last-result summaries on each opportunity.
- Phase 6 pilot work is materially in place: observability, readiness probes, trusted-proxy auth, site scoping, pilot Docker overlays, checked-in env bundles, de-identified research views, FHIR ingestion, HL7 ORU ingestion, structured import metadata persistence, persisted import-run audit records, env-driven field-preference overrides for upstream variability, a dedicated web import workspace with recent-run audit visibility, and live report/FHIR/HL7 success, successful shared-visibility, report-path failed shared-visibility for `validation_error`, structured failed shared-visibility for FHIR `unsupported_payload` plus HL7 `parse_error`, report-path and structured-adapter site-scope rejection, report-path parse/validation, adapter-specific malformed-import, and generic plus structured cross-actor audit denial smoke coverage in both the header-auth and trusted-proxy pilot paths.
- The web app now has clearer outside-collaborator surfaces: the home and about pages frame the product as an explainable, benchmarkable workflow stack, and `/proof` now publishes the checked-in demo benchmark snapshot plus a registry of published external benchmark packs as a public proof surface with side-by-side cross-pack comparison, anchored navigation, dataset coverage, queue previews, and reviewer-facing casebooks.
- The repo now includes an adoption-facing quickstart, checked-in benchmark snapshots in `docs/examples/demo-benchmark-current.json` and `docs/examples/demo-benchmark-current.md`, and a refresh path through `make benchmark-demo` plus `make refresh-demo-proof`; that published proof now carries benchmark buckets, reviewer cues, expected rationale codes, per-case rules-versus-hybrid outcomes, and an expanded 10-report casebook spanning 5 recurring benchmark buckets.
- The repo also now includes a public benchmark pack: `docs/LABELING_GUIDE.md`, `docs/BENCHMARK_SUBMISSIONS.md`, checked-in label and submission templates, a Pydantic benchmark submission schema, and a validator entrypoint through `make validate-benchmark-submission SUBMISSION=...`.
- The repo now also includes a comparable external evaluation bundle writer through `scripts/run_external_eval.py` plus `make benchmark-external`, producing JSON, Markdown, and validator-compatible submission-draft artifacts from label and prediction JSONL inputs; that external path now also preserves cohort labels, benchmark buckets, reviewer focus, expected rationale cues, optional deidentified report excerpts, dataset coverage, queue previews, and a reviewer-facing casebook in its generated outputs.
- The external benchmark helper now also accepts an optional manifest JSON so collaborator-supplied datasets can carry dataset framing, labeling-policy notes, cohort descriptions, benchmark-bucket descriptions, and default operating-point metadata into the generated JSON, Markdown, submission draft, and checked-in proof sample without ad hoc hand editing.
- Published external proof packs are now registry-driven through `docs/examples/published-external-benchmarks.json`, and `make validate-strict` now verifies that registry entries keep valid checked-in JSON artifact paths.
- The repo now also carries two checked-in deidentified external proof packs: the retrospective-style multi-cohort sample under `docs/examples/retrospective-benchmark-sample-*` and a wording-variance challenge pack under `docs/examples/wording-variance-benchmark-sample-*`, each with reproducible JSON, Markdown, and submission outputs refreshed by dedicated Make targets.
- The release-facing docs now also include a concrete operator runbook in `docs/RELEASE_RUNBOOK.md` plus a reusable `docs/RELEASE_NOTES_TEMPLATE.md` so the remaining hosted smoke evidence path is explicit rather than tribal.
- FHIR `DiagnosticReport` imports now preserve patient, encounter, and accession metadata from inline `Reference.identifier` values when upstream payloads omit fully resolved `Patient`, `Encounter`, or `ServiceRequest` resources.
- FHIR `DiagnosticReport` imports now also decode supported text-like `presentedForm` attachments, including base64 XHTML narratives with explicit charsets, bundled or contained `Binary`-backed attachment URLs, merge multiple supported attachments in order, suppress shorter overlapping fragments when a richer attachment already contains them, expand referenced `Observation.component` plus grouped `Observation.hasMember` findings into reviewer-visible report text, preserve `interpretation` plus `referenceRange` measurement context, fall back to `conclusionCode` text when free-text `conclusion` is absent, avoid duplicate or cyclic grouped-member expansion, and keep unsectioned attachment findings merged with `conclusion` text when that preserves a more reviewer-usable report shape.
- HL7 ORU imports now decode base64 `ED` report text, normalize repeated `OBX-5` values, respect custom `MSH-2` component plus repetition separators, normalize common HL7 escape sequences, and clean composite metadata fields with subcomponent-aware extraction before the existing report-text assembly flows into triage and audit persistence.
- Top-level repo docs now reflect the implemented platform instead of the earlier scaffold framing, and the repository includes checked-in contributor, security, and code-of-conduct docs appropriate for a near-1.0 open-source handoff.
- The repo still includes checked-in GitHub Actions workflows for strict validation plus hosted base, attachment-backed FHIR success-path, report-path site-rejection, and structured adapter site-rejection pilot smoke coverage, and the hosted pilot workflow now supports narrower manual FHIR-only plus HL7-only dispatches with per-job raw-log and structured-summary artifacts. Those hosted slices are now verified with green March 25, 2026 runs for FHIR and HL7, while HL7 remains manual-only in the default weekly matrix by explicit decision.
- The highest-value remaining work is no longer bootstrapping or late-Phase-6 smoke capture. The repo-side Phase 6D release polish is already in place, the research-first repositioning is visible across product and docs surfaces, the watchtower and council history loop are in place, the external starter pack matches the reviewer-facing proof shape, `/proof` compares the checked-in packs directly, and recurring watchtower automation is now in place, so the next work should move toward broader collaborator-supplied or deidentified benchmark inputs, longer-horizon calibration, and deeper live discovery quality instead of reopening parser or smoke-baseline work.
- The next benchmark-proof slice should focus on either a larger collaborator-supplied benchmark drop through the registry flow or deeper cross-pack analysis features such as bucket-level comparisons or reviewer-focused filtering, rather than just adding another static pack section.

## Fresh Validation Status

Confirmed on 2026-04-04:

- `make validate-strict` passes
- Summary: `12 pass, 0 warn, 0 fail`
- Research-intel validation now covers seeded catalogs plus a temp-database ingest and digest run, reporting `9` sources, `7` topics, `25` graph nodes, `7` seeded documents, and a passing artifact-backed digest pipeline
- Discovery ingest now also validates `9` discovery fixtures and `8` live-ready sources through the same catalog check, runs the watchtower pipeline in fixture mode for reproducible validation, and verifies both pre-run and post-run schedule state
- Opportunity generation now also emits structured JSON and Markdown action specs under `artifacts/research-intel/opportunities/`, plus contributor packet artifacts under `artifacts/research-intel/packets/`
- Research-intel validation now also runs one safe experiment and records a ratchet outcome in the strict pipeline summary
- `pytest` now passes with `155 passed`
- `cd apps/api && .venv/bin/python -m pytest tests/test_research_intel.py tests/test_research_intel_connectors.py -q` passed with `11 passed`
- `npm run lint` and `npm run build` in `apps/web` both pass with the new `/research-intel` routes included in the build

Previously confirmed during the broader post-Phase-6 slice:

- `make validate-strict` passes
- Summary: `10 pass, 0 warn, 0 fail`
- API tests: `144 passed`
- `apps/api/.venv/bin/python -m pytest apps/api/tests/test_imports.py -q` passed with `34 passed`, including split, overlapping, bundled or contained `Binary`-backed FHIR `presentedForm`, grouped and cycle-safe `Observation.hasMember`, `conclusionCode`, measurement `interpretation` plus `referenceRange`, and `Observation.component` coverage
- `apps/api/.venv/bin/python -m pytest apps/api/tests/test_summarize_pilot_smoke.py apps/api/tests/test_smoke_proxy_auth.py -q` passed with `23 passed`, covering the hosted smoke summary parser plus the attachment-backed FHIR smoke fixture and its expected `presentedForm` payload shape
- `apps/api/.venv/bin/python -m pytest apps/api/tests/test_smoke_proxy_auth.py -q` passed with `21 passed`, covering the attachment-backed FHIR smoke fixture and its expected `presentedForm` payload shape
- Unsandboxed full local reruns of `make pilot-proxy-demo-fhir-smoke` and `make pilot-header-demo-fhir-smoke` both passed on 2026-03-25 after the compose fix, recording persisted import runs `50` and `51` plus web, `/imports`, visible-case, and reviewer round-trip verification
- Web checks: `npm run lint` and `npm run build` now both pass through `make validate-strict`
- Demo evaluation compare and sweep both run through the validation script
- `make refresh-demo-proof` succeeded and refreshed the checked-in benchmark snapshot that powers `/proof`
- `apps/api/.venv/bin/python -m pytest apps/api/tests/test_demo_benchmark_snapshot.py apps/api/tests/test_exports_metrics.py -q` passed with `11 passed`, covering the casebook-backed proof snapshot and richer evaluation-case payload fields
- `apps/api/.venv/bin/python -m pytest apps/api/tests/test_validate_repo.py apps/api/tests/test_external_evaluation.py -q` passed with `10 passed`, covering the new published-registry validator plus the retrospective and wording-variance external sample packs
- `make validate-benchmark-submission SUBMISSION=docs/examples/benchmark-submission-template.json` passed
- `cd apps/api && .venv/bin/python -m pytest tests/test_benchmark_submission.py -q` passed
- `make benchmark-external LABELS=docs/examples/benchmark-label-template.jsonl PREDICTIONS=docs/examples/benchmark-prediction-template.jsonl OUT_DIR=/tmp/pancreatic-signal-external-eval BASENAME=template-external TOP_K=2` passed and wrote JSON, Markdown, and submission-draft artifacts
- `apps/api/.venv/bin/python -m pytest apps/api/tests/test_external_evaluation.py -q` passed with `6 passed`, covering manifest-driven dataset framing plus CLI override precedence for collaborator benchmark bundles
- `make benchmark-external-sample` passed and wrote a retrospective-style external bundle from the checked-in sample pack
- `make refresh-external-sample-proof` passed and refreshed the checked-in retrospective-style external benchmark proof under `docs/examples/`
- `make benchmark-external-wording-sample` passed and wrote the wording-variance challenge bundle under `artifacts/benchmarks/`
- `make refresh-external-wording-sample-proof` passed and refreshed the checked-in wording-variance benchmark proof under `docs/examples/`
- `make validate-benchmark-submission SUBMISSION=docs/examples/wording-variance-benchmark-sample-current-submission.json` passed
- `make validate-benchmark-submission SUBMISSION=/tmp/pancreatic-signal-external-eval/template-external-submission.json` passed against the generated draft
- `apps/api/.venv/bin/python -m pytest apps/api/tests/test_imports.py apps/api/tests/test_import_runs.py -q` passed with `46 passed`, including inline `Reference.identifier` extraction coverage, attachment-backed `presentedForm` decoding and audit coverage, plus custom `MSH-2` delimiter, escape-sequence, subcomponent, and audit-visibility coverage
- Targeted import / de-identification / export coverage also passes for the new import metadata surface
- Import-run audit coverage now passes for success, update counts, validation failures, unsupported payloads, site-scope rejection, and audit-route access control
- Config-override coverage now passes for one FHIR field-preference override and one HL7 field-preference override while preserving defaults
- The new `/imports` workspace is included in the validated web build and uses persisted run IDs to deep-link failed submissions into their audit detail
- The published demo proof currently includes a checked-in JSON plus Markdown benchmark summary for outside collaborators, and the web app reads that snapshot directly into dataset coverage cards, queue previews, and reviewer-facing casebook entries; the current checked-in corpus is 10 labeled reports across 5 recurring benchmark buckets, with hybrid-only recovery of the follow-up-only cases `C-005` and `C-008`
- The public external benchmark starter pack now uses the same reviewer-facing fields and publishes a casebook-shaped JSON plus Markdown bundle, so collaborators can benchmark less-synthetic datasets without losing the coverage, queue, and reviewer-cue structure established by the demo proof
- The repo now also includes a 12-case deidentified retrospective-style multi-cohort sample pack plus a 9-case wording-variance challenge pack, both with report excerpts, reviewer cues, cohort coverage, and visible misses or confounders that demonstrate the same casebook structure on less-synthetic external datasets; `/proof` now renders both packs alongside the demo comparison and compares them directly instead of leaving them docs-only
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
- That hosted pilot workflow now also supports `workflow_dispatch` with `smoke_scope=fhir-success-only` plus a manual-dispatch `smoke_scope=hl7-success-only`, and every hosted matrix job uploads both its `pilot-smoke.log` output and generated `pilot-smoke-summary.json` plus `pilot-smoke-summary.md` artifacts, including duration, absolute smoke timestamps, and exit code, to preserve exact run context once hosted execution starts
- A bundled evidence builder now exists as `make pilot-smoke-evidence SUMMARY_DIR=/path/to/downloaded/pilot-smoke-artifacts HL7_DECISION=pending|keep-manual|promote-default`, producing `pilot-smoke-evidence.json` plus `pilot-smoke-evidence.md` from downloaded hosted summary artifacts so release notes and handoff updates do not depend on manual copy-paste
- GitHub-hosted `Pilot Smoke (fhir-success-only)` run [`#23563902873`](https://github.com/alex-varga14/pancreatic-signal/actions/runs/23563902873) passed on 2026-03-25 across proxy and header auth, with summary artifacts `pilot-smoke-summary-proxy-demo-fhir-smoke` and `pilot-smoke-summary-header-demo-fhir-smoke`
- GitHub-hosted `Pilot Smoke (hl7-success-only)` run [`#23564057337`](https://github.com/alex-varga14/pancreatic-signal/actions/runs/23564057337) passed on 2026-03-25 across proxy and header auth, with summary artifacts `pilot-smoke-summary-proxy-demo-hl7-smoke` and `pilot-smoke-summary-header-demo-hl7-smoke`
- Bundled hosted evidence now records `phase_complete: true` plus `hl7_hosting_mode: manual_only`, with the explicit rationale that HL7 proved operable in GitHub Actions but still stays out of the default weekly matrix to limit recurring runtime and maintenance cost
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
- The checked-in hosted workflow under `.github/workflows/pilot-smoke.yml` now also reuses the report-path site-rejection targets, installs API dependencies, and runs those same overlay targets in GitHub Actions with recorded green hosted FHIR and HL7 success-path evidence on 2026-03-25

## Hosted Phase 6 Evidence

- Hosted FHIR confirmation: [`#23563902873`](https://github.com/alex-varga14/pancreatic-signal/actions/runs/23563902873) succeeded on 2026-03-25 with dispatch scope `fhir-success-only`, total job duration `53` seconds, max job duration `27` seconds, and summary artifacts `pilot-smoke-summary-header-demo-fhir-smoke` plus `pilot-smoke-summary-proxy-demo-fhir-smoke`
- Hosted HL7 trial: [`#23564057337`](https://github.com/alex-varga14/pancreatic-signal/actions/runs/23564057337) succeeded on 2026-03-25 with dispatch scope `hl7-success-only`, total job duration `52` seconds, max job duration `26` seconds, and summary artifacts `pilot-smoke-summary-header-demo-hl7-smoke` plus `pilot-smoke-summary-proxy-demo-hl7-smoke`
- Hosted evidence bundle output is now produced by `make pilot-smoke-evidence SUMMARY_DIR=/path/to/downloaded/pilot-smoke-artifacts HL7_DECISION=keep-manual`, and the current copyable outcome is: hosted FHIR confirmed, hosted HL7 trial recorded, HL7 hosting mode `manual_only`, phase complete `True`
- The compose-side root cause behind the earlier hosted failures was the bind-mounted web service losing image-installed `node_modules`; the fix is the anonymous `/app/node_modules` volume now checked into `docker-compose.yml`
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

### Research Intelligence foundation

- Shared persisted records now exist for research sources, runs, run items, documents, evidence, topics, digests, and opportunities
- Seed catalogs now live under `data/research/` for sources, topics, a lightweight pancreatic oncology graph, and seeded documents
- Manual ingest, due-only ingest, schedule, and digest scripts now exist through `make research-intel-ingest`, `make research-intel-ingest-due`, `make research-intel-schedule`, `make research-intel-digest`, and `make research-intel-refresh`
- The Next.js app now exposes `/research-intel`, `/research-intel/schedule`, `/research-intel/documents`, `/research-intel/digests`, and `/research-intel/opportunities`
- Case detail now links to a generated research brief that maps rationale or trial context to current research-intel topics and cited documents
- Promotion stays human-gated, triage scores remain untouched, and payment or crypto execution is still intentionally out of scope

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

Broaden from the checked-in retrospective-style multi-cohort sample to a larger de-identified or collaborator-supplied benchmark drop using the same reviewer-facing proof shape.

### Why this is next

- Phase 6 exit criteria are now met: the hosted/manual smoke boundary is verified, the hosted evidence is recorded, and the release-facing docs reflect the real product state.
- The proof surface now carries benchmark buckets, queue previews, reviewer cues, expected rationale codes, and a 10-report casebook across 5 recurring categories, while the public external benchmark helper now emits the same shape for collaborator datasets and the repo now includes both a 12-case retrospective-style multi-cohort sample pack and a 9-case wording-variance challenge pack.
- More parser or smoke-baseline work would now deliver less value than bringing a broader real-world benchmark drop into that established structure.

### Target outcome

Add one post-Phase-6 proof slice that:
- introduces a broader de-identified or collaborator-supplied benchmark input set using the same published casebook fields
- keeps the existing reviewer-facing proof shape while improving data realism, provenance, or collaborator handoff quality
- refreshes `/proof`, release notes inputs, and benchmark-facing docs from that stronger evidence base
- leaves the now-recorded hosted smoke baseline intact rather than reopening it unnecessarily

### Suggested implementation shape

1. Start from the existing benchmark proof surfaces under `docs/examples/`, `/proof`, and the external evaluation tooling rather than adding new infrastructure.

2. Use the current expanded casebook fields, optional report excerpts, optional cohort labels, and checked-in retrospective sample as the compatibility target for any broader de-identified retrospective sample or externally supplied benchmark set.

3. Refresh the published proof artifacts and make sure the updated benchmark narrative still matches the current release-facing docs and the now-explicit hosted/manual smoke boundary.

### Acceptance criteria

- The next slice improves public proof quality rather than just re-stating existing smoke evidence.
- Any refreshed benchmark or reviewer-facing artifact is reproducible from checked-in commands.
- `make validate-strict` stays green.
- The hosted Phase 6 evidence recorded above remains accurate and unchanged unless a newer deliberate rerun supersedes it.

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
make benchmark-external-sample
make refresh-external-sample-proof
make validate-benchmark-submission SUBMISSION=docs/examples/benchmark-submission-template.json
```

## Handoff Summary

This is a clean post-Phase-6 checkpoint. The repo is runnable, validated, and already beyond MVP scaffolding. Import metadata preservation, import-run audit trails, config overrides, the web import workspace, concrete proxy plus header-auth pilot packaging, automatic PR and `main` validation, checked-in hosted base plus attachment-backed FHIR success-path plus report-path and structured adapter site-rejection smoke automation, a sharper public landing experience, a checked-in benchmark proof surface, a machine-validated public benchmark submission pack, a reproducible external evaluation bundle writer, FHIR inline `Reference.identifier` fallback coverage, FHIR `presentedForm` attachment-backed narrative decoding, and HL7 `ED`, repeated-`OBX-5`, custom-`MSH-2` delimiter, escape-sequence, plus subcomponent-aware metadata support are complete. The benchmark proof surface now also publishes dataset coverage, top-k queue previews, benchmark buckets, expected rationale cues, reviewer-facing casebook notes from an expanded 10-report demo snapshot that covers 5 recurring benchmark buckets, a side-by-side comparison of the published external packs, and anchored links into each checked-in external casebook; the repo also includes both a checked-in 12-case retrospective-style multi-cohort sample pack and a 9-case wording-variance challenge pack, and `make validate-strict` verifies the published external benchmark registry that feeds `/proof`. The next agent should focus on bringing in a broader de-identified or collaborator-supplied benchmark drop, or deeper bucket-level cross-pack analysis, rather than reopening hosted smoke capture or parser work that is already covered in tests.
