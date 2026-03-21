# Security Policy

## Scope

Pancreatic Signal is research-use workflow software, but security and privacy issues still matter. We especially want reports about:

- auth or authorization bypass
- site-scope or audit-visibility leaks
- de-identification failures
- PHI or secrets exposure in the repo or sample data
- unsafe default deployment settings
- import parsing bugs that could lead to data exposure or service compromise

## How To Report

Please avoid opening a public issue for a sensitive security problem.

Preferred path:

1. Use the repository host's private security or advisory reporting feature if it is available.
2. If no private reporting path is available, contact the maintainers through a private channel before public disclosure.
3. If you only have public issue access, open a minimal issue requesting a private contact path and do not include exploit details, secrets, payloads, or patient-like data.

## What To Include

Please include:

- a short description of the issue
- affected component or file paths
- impact and likely severity
- reproduction steps or payloads when safe to share privately
- any mitigation ideas you already tested

## Disclosure Expectations

- We prefer coordinated disclosure.
- Please give maintainers a reasonable chance to investigate and ship a fix before publishing exploit details.
- Never include PHI, secrets, or live credentials in a report.

## Out Of Scope

The following are generally not security issues by themselves unless they also create a confidentiality, integrity, or access-control problem:

- false positives or false negatives in triage logic
- missing clinical features
- product-positioning disagreements
- feature requests for new integrations

Those should go through the normal issue or documentation workflow instead.
