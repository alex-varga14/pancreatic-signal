# Safety and compliance

## Intended use
Research and workflow-support software for human review.

## Explicitly not intended for
- autonomous diagnosis
- treatment recommendation
- patient self-service interpretation
- unsupervised production clinical deployment

## Safety controls
- research-only label in API and UI
- evidence-based explainability for each flag
- reviewer action required for escalation
- full audit logs
- configurable thresholds
- no hidden model-only decisions in MVP

## Privacy posture
- use de-identified or synthetic data in development
- no PHI in repo
- secrets in environment variables
- local-only defaults

## Compliance notes
This repository is not a claim of regulatory clearance.
Contributors should avoid product language implying approved clinical use.

## Responsible open source guidance
- document dataset provenance clearly
- avoid shipping PHI-containing examples
- disclose limitations
- publish benchmark methods, not inflated claims
