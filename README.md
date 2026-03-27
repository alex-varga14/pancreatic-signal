# Pancreatic Signal

Open-source, research-first triage software for identifying radiology reports suspicious for pancreatic malignancy or other high-risk pancreatic findings and routing them into a human-reviewed workflow.

> Research-use workflow software. Not for autonomous diagnosis, treatment recommendation, or unsupervised clinical deployment.

## Current Status

Pancreatic Signal is no longer a scaffold. As of 2026-03-25, this repository includes:

- deterministic, evidence-backed report triage with rationale codes and auditability
- a reviewer worklist with case detail, review actions, and research-safe views
- evaluation and export paths for retrospective benchmarking
- CSV, JSON, JSONL, attachment-backed FHIR `DiagnosticReport`, and HL7 ORU import paths
- persisted import-run audit records with stable failure buckets and visibility rules
- a dedicated `/imports` web workspace for uploads and audit inspection
- pilot-ready Docker overlays for trusted-proxy auth and header-auth demos
- live smoke coverage across success, failure, and cross-actor visibility paths

## What A `1.0` Release Should Mean

For this project, a credible `1.0` is:

- a stable research and navigation workflow platform
- transparent and explainable in how it flags reports
- benchmarkable on retrospective datasets
- usable by collaborators without private tribal knowledge
- explicit about safety boundaries and non-clinical positioning

It is not:

- clinical validation
- autonomous diagnosis
- production hospital deployment guidance for unsupervised use
- a claim of regulatory clearance

## Repo Structure

```text
.
├── AGENTS.md
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── LICENSE
├── Makefile
├── docker-compose.yml
├── docs/
│   ├── PRD.md
│   ├── MVP_PLAN.md
│   ├── QUICKSTART.md
│   ├── LABELING_GUIDE.md
│   ├── BENCHMARK_SUBMISSIONS.md
│   ├── ARCHITECTURE.md
│   ├── PHASES.md
│   ├── API_SPEC.md
│   ├── DATA_MODEL.md
│   ├── EVALUATION.md
│   ├── DEPLOYMENT.md
│   ├── RELEASE_RUNBOOK.md
│   ├── RELEASE_READINESS.md
│   ├── RELEASE_NOTES_TEMPLATE.md
│   ├── SAFETY_AND_COMPLIANCE.md
│   ├── OPEN_SOURCE_STRATEGY.md
│   └── CODEX_HANDOFF.md
├── apps/
│   ├── api/
│   └── web/
├── data/
│   ├── examples/
│   └── ontologies/
├── deploy/
│   └── examples/
└── scripts/
```

## Product Vision

Pancreatic Signal helps hospitals and research groups avoid missed follow-up on suspicious pancreatic findings by turning free-text radiology reports into an evidence-highlighted triage worklist that still requires human review.

Current product focus:

- CT and MRI abdomen report text
- deterministic rules and explainable scoring
- reviewer and navigator workflow support
- retrospective, pilot, and simulation workflows first
- interoperability paths that do not compromise explainability

## Quick Start

API runtime requires Python 3.11+. This repo includes a root `.python-version` pinned to `3.12.0` for `pyenv` users so `python3` resolves to a compatible interpreter inside the workspace.

### Fastest First Proof

If you want outside-collaborator proof before you touch the UI:

```bash
make validate-strict
make benchmark-demo
```

This validates the repo and writes benchmark artifacts to `artifacts/benchmarks/`. The checked-in published snapshot that powers the web proof page lives in [docs/examples/demo-benchmark-current.md](docs/examples/demo-benchmark-current.md) and can be refreshed with `make refresh-demo-proof`.
If you want to package a comparable external benchmark, start with [docs/LABELING_GUIDE.md](docs/LABELING_GUIDE.md) and [docs/BENCHMARK_SUBMISSIONS.md](docs/BENCHMARK_SUBMISSIONS.md).

For a comparable external results bundle:

```bash
make benchmark-external \
  LABELS=docs/examples/benchmark-label-template.jsonl \
  PREDICTIONS=docs/examples/benchmark-prediction-template.jsonl \
  MANIFEST=docs/examples/benchmark-manifest-template.json
```

For a checked-in less-synthetic multi-cohort sample bundle with deidentified report excerpts and a reviewer-facing external casebook:

```bash
make benchmark-external-sample
make refresh-external-sample-proof
```

The public `/proof` page now renders the checked-in demo comparison plus the registry of published external benchmark packs in `docs/examples/published-external-benchmarks.json`, which currently includes the retrospective-style multi-cohort sample.

### API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload --port 8000
```

### Web

```bash
cd apps/web
npm install
npm run dev
```

### Validation

```bash
make validate
make validate-strict
```

`make validate` is tolerant of missing local prerequisites and reports readiness gaps as warnings. `make validate-strict` upgrades those same gaps to failures and is the preferred pre-handoff or pre-release check.
GitHub Actions now runs the same `make validate-strict` gate on pull requests, on `main`, and via manual workflow dispatch. A separate hosted smoke workflow in [`.github/workflows/pilot-smoke.yml`](.github/workflows/pilot-smoke.yml) reuses the base proxy and header pilot smokes plus the report-path and structured adapter site-rejection variants on manual dispatch and a weekly schedule. The broader shared-visibility, audit-denial, and non-site structured failure matrix in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) remains a manual validation path.
For the release-facing evidence path that ties validation, hosted smoke artifacts, and docs updates together, use [docs/RELEASE_RUNBOOK.md](docs/RELEASE_RUNBOOK.md).
For a concise outside-collaborator path, see [docs/QUICKSTART.md](docs/QUICKSTART.md).

### Demo Imports

With the API running, you can import the sample dataset through the report ingestion endpoint:

```bash
curl -F "file=@data/examples/reports.jsonl" http://localhost:8000/api/v1/imports/reports
```

FHIR `DiagnosticReport` input is supported:

The same path now accepts supported text-like `presentedForm` attachments, including plain-text and XHTML narrative payloads, without changing the downstream triage or audit flow.

```bash
curl http://localhost:8000/api/v1/imports/fhir/diagnostic-reports \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "DiagnosticReport",
    "id": "dr-demo-1",
    "effectiveDateTime": "2026-03-19T10:00:00Z",
    "category": [{"text": "CT abdomen"}],
    "performer": [{"display": "Demo Hospital"}],
    "conclusion": "Suspicious for pancreatic neoplasm. Recommend biopsy."
  }'
```

HL7 v2 ORU input is also supported:

```bash
curl http://localhost:8000/api/v1/imports/hl7/oru \
  -H "Content-Type: text/plain" \
  --data-binary $'MSH|^~\\&|RADSYS|Demo Hospital|PS|PS|20260319100000||ORU^R01|MSG-1|P|2.5\rPV1|1|O|RAD^^^Demo Hospital\rOBR|1|PLAC-1|R-HL7-1|CT ABDOMEN^CT Abdomen|||20260319100000\rOBX|1|TX|FINDINGS^Findings||Abrupt cutoff of the pancreatic duct with ill-defined pancreatic head lesion.|\rOBX|2|TX|IMPRESSION^Impression||Suspicious for pancreatic neoplasm. Recommend biopsy.|'
```

## Pilot Path

For a local multi-service stack:

```bash
docker compose up --build
```

For the pilot overlays that exercise built API and web images plus auth wiring:

```bash
make pilot-proxy-demo-up
make pilot-header-demo-up
```

Representative smoke targets:

```bash
make pilot-proxy-demo-smoke
make pilot-proxy-demo-fhir-smoke
make pilot-proxy-demo-hl7-smoke
make pilot-proxy-demo-failed-shared-visibility-smoke
make pilot-proxy-demo-adapter-failed-shared-visibility-smoke
make pilot-proxy-demo-adapter-site-rejection-smoke
make pilot-proxy-demo-adapter-audit-visibility-smoke
make pilot-header-demo-smoke
make pilot-header-demo-failed-shared-visibility-smoke
make pilot-header-demo-adapter-failed-shared-visibility-smoke
make pilot-header-demo-adapter-site-rejection-smoke
make pilot-header-demo-adapter-audit-visibility-smoke
```

These smoke paths now exercise real import endpoints plus persisted import-run audit checks, including same-site visibility checks for successful runs, non-site failed runs, and denial checks for structured site-scope rejection runs. The full overlay and smoke matrix lives in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

For hosted smoke automation, GitHub Actions now reuses `make pilot-proxy-demo-smoke`, `make pilot-proxy-demo-site-rejection-smoke`, `make pilot-proxy-demo-adapter-site-rejection-smoke`, `make pilot-header-demo-smoke`, `make pilot-header-demo-site-rejection-smoke`, and `make pilot-header-demo-adapter-site-rejection-smoke` through [`.github/workflows/pilot-smoke.yml`](.github/workflows/pilot-smoke.yml). That workflow is intentionally narrower than the full local smoke matrix and is meant to complement, not replace, the still-manual shared-visibility, audit-denial, and non-site structured failure checks.
Manual dispatch now also supports `smoke_scope=fhir-success-only` and `smoke_scope=hl7-success-only`, with `pilot-smoke-summary.json` and `pilot-smoke-summary.md` artifacts intended for release and handoff capture.

## Documentation Map

- Quickstart and published proof: [docs/QUICKSTART.md](docs/QUICKSTART.md), [docs/examples/demo-benchmark-current.md](docs/examples/demo-benchmark-current.md)
- Public benchmark pack: [docs/LABELING_GUIDE.md](docs/LABELING_GUIDE.md), [docs/BENCHMARK_SUBMISSIONS.md](docs/BENCHMARK_SUBMISSIONS.md), [docs/examples/benchmark-label-template.jsonl](docs/examples/benchmark-label-template.jsonl), [docs/examples/benchmark-prediction-template.jsonl](docs/examples/benchmark-prediction-template.jsonl), [docs/examples/benchmark-submission-template.json](docs/examples/benchmark-submission-template.json)
- Architecture and roadmap: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/PHASES.md](docs/PHASES.md)
- API and data model: [docs/API_SPEC.md](docs/API_SPEC.md), [docs/DATA_MODEL.md](docs/DATA_MODEL.md)
- Evaluation and deployment: [docs/EVALUATION.md](docs/EVALUATION.md), [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- Release posture: [CHANGELOG.md](CHANGELOG.md), [docs/RELEASE_RUNBOOK.md](docs/RELEASE_RUNBOOK.md), [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md), [docs/RELEASE_NOTES_TEMPLATE.md](docs/RELEASE_NOTES_TEMPLATE.md)
- Safety and project posture: [docs/SAFETY_AND_COMPLIANCE.md](docs/SAFETY_AND_COMPLIANCE.md), [docs/OPEN_SOURCE_STRATEGY.md](docs/OPEN_SOURCE_STRATEGY.md)
- Agent handoff context: [docs/CODEX_HANDOFF.md](docs/CODEX_HANDOFF.md)

## Contributing And Security

Project expectations and community docs now live at the repo root:

- contribution workflow: [CONTRIBUTING.md](CONTRIBUTING.md)
- vulnerability reporting: [SECURITY.md](SECURITY.md)
- community expectations: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## License

Apache-2.0
