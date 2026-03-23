# Evaluation plan

## Evaluation philosophy

The first goal is not headline AUROC. It is practical triage usefulness:
- does the system surface the right cases early in the queue?
- are the reasons understandable?
- does it reduce reviewer search burden?

## Datasets
- demo synthetic dataset in this repo
- future de-identified retrospective labeled report sets
- institution-specific validation sets later

## Ground truth strategy
Each report should eventually be labeled for:
- suspicious pancreatic malignancy present? yes/no
- high-risk pancreatic abnormality present? yes/no
- action-worthy follow-up recommendation present? yes/no
- flag should have been escalated? yes/no

## Metrics

### Core
- precision
- recall
- F1
- sensitivity at top-k
- precision at top-k
- reviewer yield
- false negative count by rationale family

### Operational
- average cases reviewed to find one true action-worthy signal
- estimated review-time savings
- threshold-volume curve

## Error analysis buckets
- negated finding interpreted as positive
- historical finding interpreted as current
- incidental cystic lesion overcalled
- pancreatitis / inflammatory confounder
- secondary signs missed
- recommendation language missed
- uncommon wording

## Benchmark procedure
1. Run batch inference on labeled data.
2. Save outputs and thresholds.
3. Produce confusion matrix and queue metrics.
4. Review top false positives and false negatives.
5. Update ontology / rules.
6. Re-run and compare deltas.

Current repo helpers for the demo dataset:
- `python scripts/run_demo_eval.py --compare --json`
- `python scripts/run_demo_eval.py --sweep --json`
- `python scripts/write_demo_benchmark.py`
- `make refresh-demo-proof`
- `make validate-benchmark-submission SUBMISSION=docs/examples/benchmark-submission-template.json`
- `python scripts/validate_repo.py --strict`

Published demo proof files:
- `docs/examples/demo-benchmark-current.json`
- `docs/examples/demo-benchmark-current.md`

Public benchmark pack:
- `docs/LABELING_GUIDE.md`
- `docs/BENCHMARK_SUBMISSIONS.md`
- `docs/examples/benchmark-label-template.jsonl`
- `docs/examples/benchmark-submission-template.json`

Recommended reproducibility loop:
1. Run `python scripts/validate_repo.py --strict` in a fully prepared local environment.
2. Generate benchmark artifacts with `python scripts/write_demo_benchmark.py`.
3. Save the JSON and Markdown snapshot alongside any rule or threshold changes.
4. Compare the new snapshot against the previous run before changing operating thresholds.

## Human factors checks
- Can reviewers understand why a case was flagged within 10 seconds?
- Does the UI avoid presenting a score as a diagnosis?
- Are uncertainty and negation visible?

## Future evaluation
- site-shift performance
- hybrid model calibration
- prospective workflow analysis
