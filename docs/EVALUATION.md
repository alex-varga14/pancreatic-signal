# Evaluation

## Evaluation philosophy

The primary goal is practical triage usefulness, not headline AUROC. The most important questions are:

- does the system surface the right cases early in the queue?
- can a reviewer understand why a case was flagged quickly?
- do the benchmark artifacts make comparison honest and reproducible?
- does the published casebook cover enough wording variance and confounders to be reviewer-useful rather than only illustrative?

## Current evaluation assets

The repository already ships with:

- a synthetic/demo dataset for repeatable local evaluation, now expanded to 10 labeled reports across 5 benchmark buckets
- a deterministic-versus-hybrid comparison flow
- threshold sweep helpers for review-depth tuning
- generated benchmark proof artifacts in `docs/examples/`, including dataset coverage, top-k queue previews, and a reviewer-facing casebook
- an external benchmark bundle writer and submission validator

## Datasets

Current datasets:

- synthetic demo data in this repository, including explicit malignancy, secondary-sign, follow-up-only, negative-control, and pancreatitis-confounder slices
- public benchmark templates in `docs/examples/`

Next datasets to prioritize:

- de-identified retrospective labeled report sets
- site-specific validation sets for interoperability and wording variance

## Ground-truth framing

The current benchmark logic supports labels for:

- suspicious pancreatic malignancy present
- high-risk pancreatic abnormality present
- action-worthy follow-up recommendation present
- reviewer escalation expected

For benchmark comparison, `should_flag` is derived from the logical OR of those labels so the evaluation can reward important non-malignancy follow-up cases as well as overtly suspicious lesions.

The demo labels can also carry benchmark-bucket, reviewer-focus, and expected-rationale metadata so the published proof artifacts read like an explainable casebook rather than a flat score dump.

## Metrics

### Core performance

- precision
- recall
- F1
- sensitivity at top-k
- precision at top-k
- reviewer yield
- false-negative count by shared bucket name

### Operational usefulness

- average cases reviewed to find one true action-worthy signal
- estimated review-time savings
- threshold-versus-volume tradeoffs
- reviewer comprehension of evidence and rationale

### Platform quality

- repeatability of demo benchmark outputs
- validity of exported benchmark submission bundles
- consistency between docs, commands, and generated artifacts

## Error-analysis buckets

Use these stable buckets when reviewing misses:

- negation failure
- historical finding interpreted as current
- incidental cyst overcall
- pancreatitis or inflammatory confounder
- secondary signs missed
- recommendation language missed
- uncommon wording

## Current repo workflows

### Demo proof and comparison

- `python scripts/run_demo_eval.py --compare --json`
- `python scripts/run_demo_eval.py --sweep --json`
- `python scripts/write_demo_benchmark.py`
- `make refresh-demo-proof`

### External benchmark workflow

- `python scripts/run_external_eval.py --labels docs/examples/benchmark-label-template.jsonl --predictions docs/examples/benchmark-prediction-template.jsonl`
- `make benchmark-external LABELS=docs/examples/benchmark-label-template.jsonl PREDICTIONS=docs/examples/benchmark-prediction-template.jsonl`
- `make validate-benchmark-submission SUBMISSION=docs/examples/benchmark-submission-template.json`

### Repo health gate

- `python scripts/validate_repo.py --strict`

## Published proof surfaces

- `docs/examples/demo-benchmark-current.json` with dataset coverage, queue previews, and per-case casebook entries
- `docs/examples/demo-benchmark-current.md` with the same publishable casebook summary in Markdown
- `docs/LABELING_GUIDE.md`
- `docs/BENCHMARK_SUBMISSIONS.md`
- `docs/examples/benchmark-label-template.jsonl`
- `docs/examples/benchmark-prediction-template.jsonl`
- `docs/examples/benchmark-submission-template.json`

## Recommended reproducibility loop

1. Run `python scripts/validate_repo.py --strict` in a prepared local environment.
2. Regenerate demo benchmark artifacts with `python scripts/write_demo_benchmark.py`.
3. Compare benchmark deltas before changing thresholds or rationale families.
4. When sharing results publicly, generate the external benchmark bundle and validate the submission JSON.

## Human-factors checks

- Can reviewers understand why a case was flagged within roughly 10 seconds?
- Does the UI avoid presenting a score as a diagnosis?
- Are uncertainty, negation, and recommendation language visible?
- Do the published benchmark casebook entries explain what the reviewer should notice, not just whether the model was numerically right?
- Are trial matches and hybrid factors presented as review support instead of automated decisions?

## Near-term evaluation work

- expand beyond the current 10-case synthetic/demo casebook into de-identified retrospective sets
- compare more structured-import edge cases under realistic site variability
- use reviewer feedback and import audit outcomes to refine benchmarking priorities
- keep public benchmark artifacts aligned with the current hybrid baseline and supported workflows
