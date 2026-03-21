# Contributing

Thanks for helping improve Pancreatic Signal.

This project is intended to be useful to researchers, navigators, reviewers, and engineering collaborators who care about explainable pancreatic-report triage. We welcome code, documentation, evaluation, deployment, and interoperability improvements as long as they preserve the repo's research-first and safety-first posture.

## Before You Start

- Read [README.md](README.md) for the current product framing.
- Read [docs/SAFETY_AND_COMPLIANCE.md](docs/SAFETY_AND_COMPLIANCE.md) before making product or deployment claims.
- If you are changing behavior, read the relevant source-of-truth docs such as [docs/API_SPEC.md](docs/API_SPEC.md), [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md), and [docs/CODEX_HANDOFF.md](docs/CODEX_HANDOFF.md).

## Contribution Priorities

High-value contributions include:

- triage-rule quality, explainability, and evidence-span accuracy
- retrospective evaluation quality and benchmark reproducibility
- import interoperability across report, FHIR, and HL7 inputs
- reviewer workflow polish that does not reduce auditability
- pilot deployment ergonomics, smoke coverage, and documentation
- research-safe de-identification and export handling

## Ground Rules

- Do not introduce opaque decision-making in place of the deterministic triage path.
- Do not make clinical-validation or regulatory claims in code, UI, docs, or PR text.
- Do not commit PHI, secrets, or real patient data.
- Keep API behavior decoupled from specific UI assumptions.
- Prefer small, well-tested changes over broad speculative rewrites.

## Local Setup

### API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Web

```bash
cd apps/web
npm install
```

## Validation Expectations

Run the strongest check your environment supports before handoff or PR submission:

```bash
make validate
make validate-strict
```

If you touch import, auth, or pilot wiring, also consider the relevant smoke target from [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Documentation Expectations

When behavior changes, update the docs in the same change set.

Common examples:

- API surface changes: update [docs/API_SPEC.md](docs/API_SPEC.md)
- deployment or smoke changes: update [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- public project framing changes: update [README.md](README.md)
- release-facing milestones or cut lines: update [CHANGELOG.md](CHANGELOG.md) and [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md)
- agent checkpoint changes: update [docs/CODEX_HANDOFF.md](docs/CODEX_HANDOFF.md) and, when needed, [docs/NEXT_AGENT_PROMPT.md](docs/NEXT_AGENT_PROMPT.md)

## Pull Request Guidance

Aim for PRs that clearly answer:

- what changed
- why it matters
- what tests or smoke checks were run
- what docs were updated
- what risks or follow-up work remain

For rule changes, include tests and evidence-aware reasoning.
For deployment changes, include the exact command paths you validated.

## Questions And Collaboration

If a change has hidden tradeoffs, document the assumption instead of burying it. This repository is designed to be easy to hand off between collaborators and agents, so clarity is part of the contribution quality bar.
