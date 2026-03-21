# Pancreatic Signal

Open-source, research-first triage software for identifying radiology reports suspicious for pancreatic malignancy or other high-risk pancreatic findings and routing them into a human-reviewed workflow.

> Research-use workflow software. Not for autonomous diagnosis, treatment recommendation, or unsupervised clinical deployment.

## Current Status

Pancreatic Signal is no longer a scaffold. As of 2026-03-20, this repository includes:

- deterministic, evidence-backed report triage with rationale codes and auditability
- a reviewer worklist with case detail, review actions, and research-safe views
- evaluation and export paths for retrospective benchmarking
- CSV, JSON, JSONL, FHIR `DiagnosticReport`, and HL7 ORU import paths
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
│   ├── ARCHITECTURE.md
│   ├── PHASES.md
│   ├── API_SPEC.md
│   ├── DATA_MODEL.md
│   ├── EVALUATION.md
│   ├── DEPLOYMENT.md
│   ├── RELEASE_READINESS.md
│   ├── SAFETY_AND_COMPLIANCE.md
│   ├── OPEN_SOURCE_STRATEGY.md
│   ├── CODEX_HANDOFF.md
│   └── NEXT_AGENT_PROMPT.md
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

### Demo Imports

With the API running, you can import the sample dataset through the report ingestion endpoint:

```bash
curl -F "file=@data/examples/reports.jsonl" http://localhost:8000/api/v1/imports/reports
```

FHIR `DiagnosticReport` input is supported:

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
make pilot-header-demo-smoke
make pilot-header-demo-failed-shared-visibility-smoke
```

These smoke paths now exercise real import endpoints plus persisted import-run audit checks, including same-site visibility checks for successful runs and non-site failed runs. The full overlay and smoke matrix lives in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Documentation Map

- Architecture and roadmap: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/PHASES.md](docs/PHASES.md)
- API and data model: [docs/API_SPEC.md](docs/API_SPEC.md), [docs/DATA_MODEL.md](docs/DATA_MODEL.md)
- Evaluation and deployment: [docs/EVALUATION.md](docs/EVALUATION.md), [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- Release posture: [CHANGELOG.md](CHANGELOG.md), [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md)
- Safety and project posture: [docs/SAFETY_AND_COMPLIANCE.md](docs/SAFETY_AND_COMPLIANCE.md), [docs/OPEN_SOURCE_STRATEGY.md](docs/OPEN_SOURCE_STRATEGY.md)
- Agent handoff context: [docs/CODEX_HANDOFF.md](docs/CODEX_HANDOFF.md), [docs/NEXT_AGENT_PROMPT.md](docs/NEXT_AGENT_PROMPT.md)

## Contributing And Security

Project expectations and community docs now live at the repo root:

- contribution workflow: [CONTRIBUTING.md](CONTRIBUTING.md)
- vulnerability reporting: [SECURITY.md](SECURITY.md)
- community expectations: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## License

Apache-2.0
