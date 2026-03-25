# Quickstart

This is the shortest path from clone to credible proof.

## 1. Fastest First Proof

If you want evidence before UI:

```bash
make validate-strict
make benchmark-demo
```

What you get:

- strict validation across API, web, and demo evaluation
- a local benchmark snapshot in `artifacts/benchmarks/demo-benchmark.json`
- a readable benchmark summary in `artifacts/benchmarks/demo-benchmark.md`

## 2. Local Product Walkthrough

If you want the reviewer workflow:

```bash
docker compose up --build
```

Then open:

- web: `http://localhost:3000`
- worklist: `http://localhost:3000/cases`
- benchmark proof: `http://localhost:3000/proof`
- imports: `http://localhost:3000/imports`
- API docs: `http://localhost:8000/docs`

To import the sample dataset:

```bash
curl -F "file=@data/examples/reports.jsonl" http://localhost:8000/api/v1/imports/reports
```

## 3. Published Demo Proof

The repo now carries a checked-in benchmark snapshot for outside collaborators:

- JSON snapshot: `docs/examples/demo-benchmark-current.json`
- Markdown summary: `docs/examples/demo-benchmark-current.md`

Maintain that published proof with:

```bash
make refresh-demo-proof
```

Use this when the demo benchmark changes and you want the landing page plus docs to reflect the new state.

## 4. Where To Look Next

If you need release or pilot evidence rather than just a local walkthrough:

- release operator path: [RELEASE_RUNBOOK.md](./RELEASE_RUNBOOK.md)
- release checklist: [RELEASE_READINESS.md](./RELEASE_READINESS.md)

Hosted pilot evidence currently flows through the `Pilot Smoke` workflow with manual `smoke_scope=fhir-success-only` and `smoke_scope=hl7-success-only` dispatches. Record the uploaded `pilot-smoke-summary.json` and `pilot-smoke-summary.md` artifacts in the handoff once those runs exist.

- comparable external bundle:

```bash
make benchmark-external \
  LABELS=docs/examples/benchmark-label-template.jsonl \
  PREDICTIONS=docs/examples/benchmark-prediction-template.jsonl
```

- product framing: [README.md](../README.md)
- benchmark philosophy: [EVALUATION.md](./EVALUATION.md)
- deployment and smoke matrix: [DEPLOYMENT.md](./DEPLOYMENT.md)
- open-source posture: [OPEN_SOURCE_STRATEGY.md](./OPEN_SOURCE_STRATEGY.md)

## 5. Guardrails

- research-use workflow software only
- human review stays in the loop
- explainability is a feature, not an afterthought
- benchmark claims should stay reproducible and honest
