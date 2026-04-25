# Safety and compliance

## Intended use

Research-first workflow-support software for human review of radiology report text and related pilot operations.

## Explicitly not intended for

- autonomous diagnosis
- treatment recommendation
- patient self-service interpretation
- unsupervised clinical deployment
- claims of validated clinical decision support

## Safety controls

- research-only framing in the API and web product
- evidence-based explainability for each flag
- human reviewer action required for escalation or closure decisions
- durable review-action and import-run audit surfaces
- configurable thresholds and deterministic rationale codes
- no opaque model-only decision path replacing the explainable baseline

## Privacy posture

- use synthetic or de-identified data in development and public examples
- do not keep PHI in the repository
- store secrets in environment variables
- default to local-safe development settings, with documented pilot auth modes for controlled environments

## Pilot and auth posture

The current implementation supports:

- mock auth for local development
- trusted-proxy auth for controlled pilot packaging
- header-based actor forwarding for controlled pilot packaging
- site-scope-aware access and import behavior

These modes support research and demonstration workflows. They are not a substitute for institution-specific governance, enterprise IAM review, or production deployment controls.

## Compliance notes

This repository does not claim regulatory clearance, clinical validation, or production readiness for general hospital deployment.

Contributors should avoid:

- language implying approved clinical use
- examples that contain PHI
- documentation that presents scores or trial matches as decisions instead of review support

## Responsible open source guidance

- document dataset provenance clearly
- keep examples and tests de-identified
- disclose limitations and workflow assumptions
- publish benchmark methods, not inflated performance claims

## Autoresearch posture

Pancreatic Signal v2 ships an opt-in autoresearch lab subsystem
([docs/AUTORESEARCH.md](AUTORESEARCH.md)) inspired by
[karpathy/autoresearch](https://github.com/karpathy/autoresearch). The
following safety constraints are enforced by the schema, the experiment
driver, and the API:

- **Single edit surface.** The autoresearch agent is permitted to modify
  exactly one file: `data/ontologies/pancreatic_signal_rules.json`. Any
  proposal that touches another path is recorded as `decision = "off_surface"`
  and discarded.
- **No live writes.** The autoresearch loop never writes to the case store,
  audit log, imports tables, or any production data path. It writes only to
  `autoresearch/runs/<id>/` (append-only) and a temporary candidate ontology.
- **No Python source mutation in v2.0.** Editing Python source is explicitly
  out of scope for the agent and deferred to v2.2.
- **Human-gated promotion.** A "kept" candidate is not adopted by the live
  triage engine until a human runs `make autoresearch-promote RUN=<id>` (or
  invokes the admin-only `POST /api/v1/autoresearch/promote/{id}` endpoint).
  Promotion writes a provenance record at
  `autoresearch/runs/<id>/promotion.json`.
- **Rollback is one command.** `make autoresearch-rollback` restores the
  frozen baseline at `autoresearch/baseline/pancreatic_signal_rules.json`
  into the live ontology path.
- **Schema-enforced guardrails.** The candidate ontology is validated by
  `OntologyConfig` (`extra="forbid"`) before any evaluation runs. Recall
  floors, threshold ordering, no-silent-deletion, and a deterministic eval
  check are enforced by `scripts/run_autoresearch_experiment.py`.
- **Pilot/clinical positioning unchanged.** Autoresearch does not change the
  product's research-only positioning: triage remains explainable, every
  flag retains its rationale, and no autonomous clinical decision is
  introduced.
