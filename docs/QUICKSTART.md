# Quickstart

This is the shortest path from clone to credible proof.

## 1. Fastest First Proof

If you want evidence before UI:

```bash
make validate-strict
make benchmark-demo
make research-intel-refresh
```

What you get:

- strict validation across API, web, and demo evaluation
- a local benchmark snapshot in `artifacts/benchmarks/demo-benchmark.json`
- a readable benchmark summary in `artifacts/benchmarks/demo-benchmark.md`
- seeded research-intel artifacts in `artifacts/research-intel/`
- a casebook-style proof artifact with dataset coverage, top-k queue previews, and reviewer cues for each benchmark case in the current 10-report demo corpus

## 2. Local Product Walkthrough

If you want the reviewer workflow:

```bash
docker compose up --build
```

Then open:

- web: `http://localhost:3000`
- worklist: `http://localhost:3000/cases`
- research intelligence: `http://localhost:3000/research-intel`
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

## 4. Research Intelligence Walkthrough

To seed the local pancreatic oncology watchtower and generate the first cited digest:

```bash
make research-intel-refresh
```

For the reproducible discovery-ingest path:

```bash
make research-intel-discovery-fixture
```

Then explore:

- `/research-intel` for ingest health, topic heat, and recent digest activity
- `/research-intel/documents` for the normalized document explorer
- `/research-intel/graph` for the active pancreatic oncology knowledge graph
- `/research-intel/digests` for the cited council summaries
- `/research-intel/opportunities` for benchmark, rule, trial-catalog, and tooling proposals

Current note:
- The first implementation is intentionally seeded and manual-triggered. It establishes the data model, audit trail, case-brief linkage, and contributor workflow before live internet polling is added.

## 5. Where To Look Next

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

If you want the checked-in external proof packs rather than the tiny template pack, run:

```bash
make benchmark-external-sample
make refresh-external-sample-proof
make benchmark-external-wording-sample
make refresh-external-wording-sample-proof
```

Those commands write and refresh:

- `artifacts/benchmarks/retrospective-benchmark-sample.json`
- `artifacts/benchmarks/retrospective-benchmark-sample.md`
- `artifacts/benchmarks/wording-variance-benchmark-sample.json`
- `artifacts/benchmarks/wording-variance-benchmark-sample.md`
- `docs/examples/published-external-benchmarks.json`
- `docs/examples/retrospective-benchmark-sample-current.json`
- `docs/examples/retrospective-benchmark-sample-current.md`
- `docs/examples/wording-variance-benchmark-sample-current.json`
- `docs/examples/wording-variance-benchmark-sample-current.md`

The `/proof` page now reads the published demo proof plus every external pack listed in `docs/examples/published-external-benchmarks.json`, compares those packs side by side, and still links into each full casebook section. Registry entries should keep unique `id` values, point at checked-in relative JSON snapshot paths, and stay green under `make validate-strict`.

- product framing: [README.md](../README.md)
- benchmark philosophy: [EVALUATION.md](./EVALUATION.md)
- deployment and smoke matrix: [DEPLOYMENT.md](./DEPLOYMENT.md)
- open-source posture: [OPEN_SOURCE_STRATEGY.md](./OPEN_SOURCE_STRATEGY.md)

## 6. Guardrails

- research-use workflow software only
- human review stays in the loop
- explainability is a feature, not an afterthought
- benchmark claims should stay reproducible and honest
