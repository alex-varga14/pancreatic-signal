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
- a casebook-style proof artifact with dataset coverage, top-k queue previews, and reviewer cues for each benchmark case in the current 10-report demo corpus

## 2. Local Product Walkthrough

If you want the reviewer workflow:

```bash
docker compose up --build
```

Then open:

- web: `http://localhost:3000`
- worklist: `http://localhost:3000/cases`
- benchmark proof: `http://localhost:3000/proof` for the checked-in demo comparison plus the multi-cohort retrospective-style sample
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

Those published artifacts now include:

- 10 labeled demo reports across 5 benchmark buckets
- dataset coverage by benchmark bucket
- current top-k queue previews for rules and hybrid scoring
- reviewer-facing casebook notes plus expected rationale cues per case

Maintain that published proof with:

```bash
make refresh-demo-proof
```

Use this when the demo benchmark changes and you want the landing page plus docs to reflect the new state.

## 4. Where To Look Next

If you need release or pilot evidence rather than just a local walkthrough:

- release operator path: [RELEASE_RUNBOOK.md](./RELEASE_RUNBOOK.md)
- release checklist: [RELEASE_READINESS.md](./RELEASE_READINESS.md)

Hosted pilot evidence currently flows through the `Pilot Smoke` workflow with manual `smoke_scope=fhir-success-only` and `smoke_scope=hl7-success-only` dispatches. The current recorded baseline is hosted FHIR run [`#23563902873`](https://github.com/alex-varga14/pancreatic-signal/actions/runs/23563902873) plus hosted HL7 trial [`#23564057337`](https://github.com/alex-varga14/pancreatic-signal/actions/runs/23564057337).

- comparable external bundle:

```bash
make benchmark-external \
  LABELS=docs/examples/benchmark-label-template.jsonl \
  PREDICTIONS=docs/examples/benchmark-prediction-template.jsonl \
  MANIFEST=docs/examples/benchmark-manifest-template.json
```

That external helper now emits a casebook-shaped JSON and Markdown bundle with dataset coverage, top-k queue previews, and reviewer-facing notes drawn from the optional label fields.

If you want a checked-in less-synthetic multi-cohort sample rather than the tiny template pack, run:

```bash
make benchmark-external-sample
make refresh-external-sample-proof
```

That sample writes and refreshes:

- `artifacts/benchmarks/retrospective-benchmark-sample.json`
- `artifacts/benchmarks/retrospective-benchmark-sample.md`
- `docs/examples/published-external-benchmarks.json`
- `docs/examples/retrospective-benchmark-sample-current.json`
- `docs/examples/retrospective-benchmark-sample-current.md`

The `/proof` page now reads the published demo proof plus every external pack listed in `docs/examples/published-external-benchmarks.json`, so the public web surface can grow beyond a single checked-in sample without more one-off UI wiring. Registry entries should keep unique `id` values and point at checked-in relative JSON snapshot paths.

- product framing: [README.md](../README.md)
- benchmark philosophy: [EVALUATION.md](./EVALUATION.md)
- deployment and smoke matrix: [DEPLOYMENT.md](./DEPLOYMENT.md)
- open-source posture: [OPEN_SOURCE_STRATEGY.md](./OPEN_SOURCE_STRATEGY.md)

## 5. Guardrails

- research-use workflow software only
- human review stays in the loop
- explainability is a feature, not an afterthought
- benchmark claims should stay reproducible and honest
