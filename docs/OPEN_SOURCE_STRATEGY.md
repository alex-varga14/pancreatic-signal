# Open-Source Strategy

## Why Open Source

The goal is to create a transparent, reusable pancreatic oncology workflow layer that researchers, hospitals, and software collaborators can inspect, adapt, benchmark, and critique without depending on closed logic or private operational knowledge.

## Recommended License

Apache-2.0

Why this still fits:

- permissive for academic and commercial collaborators
- explicit patent grant
- compatible with ecosystem growth around adapters, evaluation, and workflow tooling

## What `1.0` Should Represent

A strong `1.0` for this repository is not "finished medicine." It is:

- a stable research-first workflow platform
- transparent rule-based triage with evidence and rationale visibility
- reproducible evaluation and export paths
- usable pilot packaging for non-production demonstrations
- enough documentation that new collaborators can contribute without private onboarding

It is not:

- clinical validation
- unsupervised deployment guidance
- a substitute for institutional governance or radiologist review
- a claim that interoperability coverage is complete

## Community Value Proposition

This project is most helpful to the larger open-source community when it offers:

- an explainable baseline that others can benchmark against
- realistic workflow surfaces instead of isolated NLP scripts
- import adapters that help teams meet existing hospital data where it is
- safety-forward examples of review, audit, scope control, and de-identification
- a place where research groups can improve rules, benchmarks, and workflow ergonomics in the open

## Contribution Model

- benchmark-oriented PRs are encouraged
- rule or ontology changes should include tests
- deployment and interoperability changes should include docs updates
- UI changes should preserve explainability and audit visibility
- handoff quality matters; keep [docs/CODEX_HANDOFF.md](docs/CODEX_HANDOFF.md) current when the implementation state meaningfully changes

## Near-Term Community Priorities

The highest-value collaboration areas after the current pilot hardening work are:

1. record hosted pilot smoke evidence and make the hosted-versus-manual boundary explicit
2. strengthen benchmark datasets, labeling guidance, and error analysis
3. expand deployment guidance for real-world pilot constraints
4. deepen reviewer ergonomics and feedback loops without compromising explainability
5. refine the existing trial-matching and abstraction layer instead of replacing it with opaque matching

## Open-Source Guardrails

- keep the project research-first and honest about limitations
- do not normalize PHI in examples or tests
- prefer explainable behavior over opaque accuracy claims
- publish benchmark methods and error buckets, not inflated marketing language
- make external comparison packages easy to validate and hard to misrepresent
- treat docs, onboarding, and contributor clarity as product features
