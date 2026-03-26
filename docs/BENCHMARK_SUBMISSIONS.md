# Benchmark Submissions

This document defines how outside teams should package a comparable benchmark result for Pancreatic Signal.

## Goal

The benchmark pack exists so collaborators can publish comparable results without private back-and-forth about:

- label meaning
- metric interpretation
- operating thresholds
- top-k review assumptions
- error bucket naming

## What to submit

At minimum, prepare:

1. A label file that follows [LABELING_GUIDE.md](./LABELING_GUIDE.md)
2. A prediction file that follows [`docs/examples/benchmark-prediction-template.jsonl`](./examples/benchmark-prediction-template.jsonl)
3. A benchmark submission JSON that follows [`docs/examples/benchmark-submission-template.json`](./examples/benchmark-submission-template.json) or the generated `*-submission.json` draft from `scripts/run_external_eval.py`
4. Any supporting benchmark artifacts you want others to inspect, such as the generated external casebook bundle, confusion-matrix exports, or case-level outputs

## Prediction file format

Each prediction line is one JSON object with:

- `report_id`
- `case_id`
- `score`
- optional `rationale_codes`
- optional `false_negative_bucket`
- optional `notes`

Use `false_negative_bucket` only when you already reviewed a miss and want the generated submission draft to carry that bucket count forward. If you omit it, the generated bundle still remains valid.

See the minimal template in [`docs/examples/benchmark-prediction-template.jsonl`](./examples/benchmark-prediction-template.jsonl).

## Label file enhancements

The public label template now also supports optional reviewer-facing fields:

- `report_excerpt`
- `benchmark_bucket`
- `reviewer_focus`
- `expected_rationale_codes`

These fields are not required for metric validity, but they let the generated external bundle publish dataset coverage, queue previews, and a reviewer-facing casebook instead of only a score table.

The repository also now includes a checked-in deidentified retrospective-style sample pack that uses those fields:

- `docs/examples/retrospective-benchmark-sample-labels.jsonl`
- `docs/examples/retrospective-benchmark-sample-predictions.jsonl`
- `docs/examples/retrospective-benchmark-sample-current.json`
- `docs/examples/retrospective-benchmark-sample-current.md`

## Generate the bundle

Use the built-in external evaluation helper:

```bash
make benchmark-external \
  LABELS=docs/examples/benchmark-label-template.jsonl \
  PREDICTIONS=docs/examples/benchmark-prediction-template.jsonl
```

For the checked-in less-synthetic sample pack:

```bash
make benchmark-external-sample
make refresh-external-sample-proof
```

This writes:

- `artifacts/benchmarks/external-benchmark.json`
- `artifacts/benchmarks/external-benchmark.md`
- `artifacts/benchmarks/external-benchmark-submission.json`

The JSON and Markdown outputs now include:

- dataset coverage by benchmark bucket
- top-k queue previews
- a reviewer-facing external casebook with label notes, reviewer focus, expected rationale cues, and recorded miss buckets

## Validate the submission

Use the built-in validator:

```bash
make validate-benchmark-submission SUBMISSION=docs/examples/benchmark-submission-template.json
```

If you prefer to call the script directly, run it inside a prepared API environment:

```bash
apps/api/.venv/bin/python scripts/validate_benchmark_submission.py docs/examples/benchmark-submission-template.json
```

## Submission JSON fields

The current public schema includes:

- submission metadata: name, project, repository, commit SHA
- dataset metadata: dataset name, split, report count, de-identification status
- operating point: score mode, threshold, top-k, evaluation command
- comparable metrics: precision, recall, F1, top-k precision, top-k sensitivity, reviewer yield
- stable error-bucket counts
- short lists of notable strengths and known limitations

## Required consistency rules

The validator enforces:

- `processed = TP + FP + TN + FN`
- `positives = TP + FN`
- `flagged = TP + FP`
- `precision`, `recall`, and `f1` must match the counts
- `reviewer_yield_at_top_k` must match `precision_at_top_k`
- false-negative bucket counts cannot exceed total false negatives
- `report_count` must match `metrics.processed`

## Recommended submission bundle

For a strong public comparison, include:

- the prediction JSONL you evaluated
- the label JSONL with reviewer-facing fields populated when available
- the benchmark submission JSON
- a short README with dataset framing and labeling policy
- the exact evaluation command
- a threshold sweep or operating-point rationale
- the generated JSON or Markdown casebook bundle from `scripts/run_external_eval.py`
- a small error analysis summary using the shared bucket names

## Safety requirements

- do not submit PHI
- do not imply clinical validation if the dataset is retrospective or synthetic
- be explicit about whether the result is rules, hybrid, or another external method
- keep limitations visible in the submission itself
