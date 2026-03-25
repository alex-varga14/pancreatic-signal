# Release Runbook

This runbook is the shortest path from a merged branch to a credible research-first public checkpoint.

It is not a clinical deployment checklist. It is the operator path for making the repo's proof, validation, and pilot evidence easy to audit.

## 1. Confirm Release Intent

Before you tag or announce anything, confirm the release is still framed as:

- research-use workflow software
- explainable and benchmarkable
- human-review dependent
- non-clinical in its claims

If the release narrative drifts from those boundaries, stop and fix the messaging first.

## 2. Refresh The Core Proof Surface

Run:

```bash
make validate-strict
make benchmark-demo
```

If the checked-in public proof should move with the release, also run:

```bash
make refresh-demo-proof
```

Record:

- the validation date
- the `make validate-strict` summary
- the current API test count
- whether the published benchmark snapshot changed

## 3. Decide Whether Pilot Smoke Evidence Must Be Refreshed

You should refresh pilot evidence when the release changes any of the following:

- import behavior
- auth or site-scope behavior
- import-run audit visibility
- pilot overlay wiring
- hosted smoke workflow behavior

If none of those changed, note that the prior hosted and local evidence is being carried forward intentionally.

## 4. Capture Hosted Smoke Evidence

The hosted workflow is:

- [`.github/workflows/pilot-smoke.yml`](../.github/workflows/pilot-smoke.yml)

The minimum hosted evidence path is:

1. Manually dispatch `Pilot Smoke` with `smoke_scope=fhir-success-only`.
2. Download or inspect:
   - `pilot-smoke.log`
   - `pilot-smoke-summary.json`
   - `pilot-smoke-summary.md`
3. Build a bundled hosted evidence record from the downloaded summary artifacts:
   - `make pilot-smoke-evidence SUMMARY_DIR=/path/to/downloaded/pilot-smoke-artifacts HL7_DECISION=pending`
   - This writes `pilot-smoke-evidence.json` and `pilot-smoke-evidence.md` next to the downloaded artifacts unless you override `OUT_DIR`, `OUT_JSON`, or `OUT_MARKDOWN`.
4. Record the exact run date, run URL, duration, outcome, and visible-case summary in:
   - [docs/CODEX_HANDOFF.md](./CODEX_HANDOFF.md)
   - [CHANGELOG.md](../CHANGELOG.md) if the run materially changes release confidence

Historical failed workflow executions without jobs or uploaded artifacts do not count as hosted evidence. Treat the first usable hosted checkpoint as the first green run that actually produces `pilot-smoke-summary.json` and `pilot-smoke-summary.md`.

If you are making the HL7 hosting decision for Phase 6B, also dispatch:

1. `smoke_scope=hl7-success-only`
2. compare its duration and stability to the FHIR-only hosted path
3. rerun `make pilot-smoke-evidence SUMMARY_DIR=/path/to/downloaded/pilot-smoke-artifacts HL7_DECISION=keep-manual` or `HL7_DECISION=promote-default`
4. record whether HL7 should stay manual or join the default hosted matrix

## 5. Refresh Local Manual Evidence When Needed

The hosted workflow is intentionally narrower than the full operator matrix.

If your change touched failure-path or visibility behavior, rerun the relevant local overlay smokes from [docs/DEPLOYMENT.md](./DEPLOYMENT.md), especially:

- shared-visibility
- failed-run shared-visibility
- structured adapter failed-run shared-visibility
- audit-visibility
- structured adapter audit-visibility
- structured adapter site-rejection

Record only the paths that were actually rerun. Do not imply broader coverage than what was executed.

## 6. Update Release-Facing Docs

Before opening or merging the release-facing PR, make sure these stay aligned:

- [README.md](../README.md)
- [docs/QUICKSTART.md](./QUICKSTART.md)
- [docs/DEPLOYMENT.md](./DEPLOYMENT.md)
- [docs/API_SPEC.md](./API_SPEC.md)
- [docs/RELEASE_READINESS.md](./RELEASE_READINESS.md)
- [docs/CODEX_HANDOFF.md](./CODEX_HANDOFF.md)
- [CHANGELOG.md](../CHANGELOG.md)

## 7. Draft Release Notes

Use:

- [docs/RELEASE_NOTES_TEMPLATE.md](./RELEASE_NOTES_TEMPLATE.md)

Fill in:

- what the release enables
- what remains out of scope
- exact validation date and headline results
- exact hosted smoke evidence or the explicit reason it is still pending
- the best setup path for a new collaborator
- the highest-priority next slice after release

## 8. Minimum Credible Release Evidence

Treat a release candidate as credible only if all of the following are true:

- `make validate-strict` is green
- the benchmark proof surface is still reproducible
- the hosted/manual smoke boundary is explicitly documented
- the latest hosted FHIR evidence is either recorded or clearly marked pending
- any still-manual HL7 hosting decision is stated plainly
- the docs do not reference missing files or stale setup paths

## 9. Current Post-6C Reality

As of the current Phase 6 state:

- repo-side interoperability hardening is already in place
- the highest-value remaining work is hosted smoke evidence capture for Phase 6A and 6B
- release-facing docs should help contributors understand that boundary without private context
