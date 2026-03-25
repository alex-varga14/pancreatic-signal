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
