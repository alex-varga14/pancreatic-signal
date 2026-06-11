# Pancreatic Signal For Researchers

Open-source (Apache-2.0), citable pancreatic oncology research software with a reproducible benchmark path and a cited literature-monitoring core.

> Research-use workflow software. Not clinical decision support, not validated for diagnosis, and not a regulatory-cleared device.

## What you can do with it

- **Benchmark explainable triage rules retrospectively.** Deterministic, rule-based flagging of CT/MRI abdomen report text with evidence spans and rationale codes for every flag. Run the demo benchmark in minutes (`make benchmark-demo`) or package your own labeled retrospective dataset with the documented label schema ([LABELING_GUIDE.md](../LABELING_GUIDE.md)) and submission format ([BENCHMARK_SUBMISSIONS.md](../BENCHMARK_SUBMISSIONS.md)).
- **Compare against published proof packs.** The repo ships checked-in external benchmark packs and a public `/proof` page rendering side-by-side comparisons, so your results are comparable to a stable baseline.
- **Monitor pancreatic oncology literature with citations.** The research-intelligence watchtower ingests Europe PMC, ClinicalTrials.gov, NCI, and FDA feeds into cited digests, a topic graph, and human-gated opportunity proposals — every claim traceable to a source document.
- **Study negation and wording-variance failure modes.** Stable error buckets (negation failure, wording variance, incidental cysts, pancreatitis confounders) are part of the evaluation contract, including a wording-variance challenge pack.

## Why it is research-friendly

- Fully deterministic scoring — runs are reproducible bit-for-bit, no opaque model in the decision path
- `CITATION.cff` included; cite the repository directly in publications
- Synthetic demo data only; de-identification utilities and research-safe views for working with your own data under your governance
- 165-test API suite and a strict validation gate (`make validate-strict`) so you can verify the platform before trusting results from it

## Get started

```bash
git clone https://github.com/alex-varga14/pancreatic-signal
cd pancreatic-signal
make validate-strict && make benchmark-demo
```

Open a [use-case interest issue](https://github.com/alex-varga14/pancreatic-signal/issues/new/choose) to discuss a dataset, collaboration, or missing capability.
