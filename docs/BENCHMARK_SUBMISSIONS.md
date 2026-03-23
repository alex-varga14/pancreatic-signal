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
2. A benchmark submission JSON that follows [`docs/examples/benchmark-submission-template.json`](./examples/benchmark-submission-template.json)
3. Any supporting benchmark artifacts you want others to inspect, such as confusion-matrix exports or case-level outputs

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

- the benchmark submission JSON
- a short README with dataset framing and labeling policy
- the exact evaluation command
- a threshold sweep or operating-point rationale
- a small error analysis summary using the shared bucket names

## Safety requirements

- do not submit PHI
- do not imply clinical validation if the dataset is retrospective or synthetic
- be explicit about whether the result is rules, hybrid, or another external method
- keep limitations visible in the submission itself
