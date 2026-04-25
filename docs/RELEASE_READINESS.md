# Release Readiness

This checklist is for a research-first open-source release, not a clinical deployment claim.

## Release Intent

Before tagging a `1.0`, confirm the release is being framed as:

- research-use workflow software
- explainable and benchmarkable
- human-review dependent
- non-clinical and non-regulatory in its claims

Do not tag a release that blurs those boundaries.

## Product Readiness

- deterministic triage remains the primary explainability path
- reviewer workflow works end to end
- imports work across generic report, FHIR, and HL7 paths, including supported text-backed FHIR `presentedForm` attachments
- import-run audit summaries and detail views are available
- de-identified research surfaces still behave as documented
- current handoff docs match the actual implementation state

## Validation Readiness

- `make validate-strict` passes in the release environment
- GitHub Actions PR validation is green for the release branch or merge commit when applicable
- Hosted GitHub Actions pilot smoke is green for the release branch or release candidate when applicable; the current recorded baseline is FHIR run `#23563902873` plus HL7 trial `#23564057337` on 2026-03-25
- if a hosted smoke workflow was only added recently, its first GitHub-hosted run is either green or explicitly called out as pending; for `Pilot Smoke`, the recorded March 25, 2026 green runs are now the baseline until a newer release-candidate rerun supersedes them
- hosted smoke summaries are captured from `pilot-smoke-summary.json` and `pilot-smoke-summary.md` when those artifacts exist
- when multiple hosted summary artifacts are downloaded, they can be consolidated into `pilot-smoke-evidence.json` and `pilot-smoke-evidence.md`
- failed historical workflow executions without jobs or uploaded artifacts are not treated as hosted evidence
- the handoff and deployment docs accurately distinguish hosted base plus report-path and structured adapter site-rejection smoke coverage from the broader manual structured-failure and visibility matrix
- latest API, web, and evaluation results are captured in the release notes or handoff
- relevant pilot smoke targets have been rerun recently enough to be credible for the release
- successful and failed import-run shared-visibility expectations, structured adapter site-scope rejection paths, and structured adapter audit-visibility denial paths remain covered by the current smoke matrix
- any validation that remains intentionally manual, including the broader failure-path and visibility-specific overlay smokes, is called out explicitly
- any skipped smoke paths are explicitly documented

## Documentation Readiness

- [README.md](../README.md) accurately describes current capabilities and limits
- [CHANGELOG.md](../CHANGELOG.md) includes the release summary
- [docs/RELEASE_RUNBOOK.md](./RELEASE_RUNBOOK.md) matches the actual release-evidence flow
- [docs/DEPLOYMENT.md](./DEPLOYMENT.md) matches the current overlay and smoke matrix
- [docs/API_SPEC.md](./API_SPEC.md) matches the current import, auth, and audit behavior
- [docs/SAFETY_AND_COMPLIANCE.md](./SAFETY_AND_COMPLIANCE.md) remains aligned with release messaging
- [docs/RELEASE_NOTES_TEMPLATE.md](./RELEASE_NOTES_TEMPLATE.md) still reflects the evidence you actually want maintainers to publish
- [docs/CODEX_HANDOFF.md](./CODEX_HANDOFF.md) is current enough for the next implementation phase

## Open-Source Readiness

- [CONTRIBUTING.md](../CONTRIBUTING.md) reflects current contribution expectations
- [SECURITY.md](../SECURITY.md) provides a responsible reporting path
- [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) is present and discoverable
- sample data remains synthetic or otherwise safe for publication
- no secrets, PHI, or environment-specific credentials are present in tracked files

## Autoresearch Readiness (v2+)

The autoresearch lab subsystem is opt-in and must not block a release of the
core product. Treat the following as additional gates only when the release
notes explicitly call autoresearch out as part of the release:

- [`autoresearch/program.md`](../autoresearch/program.md) reflects the intended
  primary metric, recall floors, and edit-surface limits for the release
- [`autoresearch/baseline/pancreatic_signal_rules.json`](../autoresearch/baseline/pancreatic_signal_rules.json)
  matches the live ontology that ships with the release (or is updated and
  the change is documented in the release notes)
- `make autoresearch-once CANDIDATE=data/ontologies/pancreatic_signal_rules.json`
  succeeds against the released ontology with `decision = "kept"` or
  `discarded_no_improvement` (a `discarded_guardrail` outcome blocks the
  release)
- the `/api/v1/autoresearch/*` routes return `200` and the `/autoresearch`
  web surface renders the run history and leaderboard in the release
  environment
- promotion remains gated by the `admin` role in the release auth posture and
  is documented as such in [`docs/SAFETY_AND_COMPLIANCE.md`](./SAFETY_AND_COMPLIANCE.md)
- `make autoresearch-rollback` is verified to restore the live ontology from
  the frozen baseline before tagging
- any kept run that has been promoted into the live ontology is referenced in
  the release notes by `run_id`, with a link to the corresponding
  `autoresearch/runs/<id>/` artifacts

## Release Notes Checklist

Include:

- what the release enables for researchers and pilot collaborators
- what is still explicitly out of scope
- the exact validation date and headline results
- the exact hosted smoke artifact path or the explicit reason hosted evidence is still pending
- the most important setup path for first-time users
- the highest-priority next implementation slice after release

Use [docs/RELEASE_NOTES_TEMPLATE.md](./RELEASE_NOTES_TEMPLATE.md) rather than drafting this ad hoc.

## Recommended Final Gate

Treat the release as ready only if the maintainers can answer "yes" to both questions:

1. Would a new outside collaborator understand what this project is, what it is not, and how to run it?
2. Would a careful reviewer see evidence of transparency, safety boundaries, and reproducible validation rather than hype?
