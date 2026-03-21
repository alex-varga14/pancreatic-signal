# Next Agent Prompt

Use this as the starting prompt for the next coding agent:

```text
Analyze the repo, then read /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/CODEX_HANDOFF.md, /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/PHASES.md, /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/API_SPEC.md, /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/DEPLOYMENT.md, /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/README.md, and /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/RELEASE_READINESS.md.

Proceed with the next recommended slice from the handoff: live failed-run shared-visibility smoke coverage for non-site failures.

Constraints:
- Preserve deterministic explainability and the existing backend plus web import flow.
- Do not regress auth, site scoping, research-safe de-identification, reviewer workflow behavior, the import metadata preservation path, the import-run audit surfaces, the `/imports` workspace, the generic `/imports/reports` smoke path, the header-demo shared-visibility, adapter-shared-visibility, FHIR/HL7, site-rejection, parse-validation, adapter-failure, and audit-visibility smoke paths, the proxy-demo shared-visibility, adapter-shared-visibility, FHIR/HL7, site-rejection, parse-validation, adapter-failure, and audit-visibility smoke paths, or the proxy/header pilot packaging.
- Keep capability gating aligned with `/api/v1/auth/me`.
- Prefer additive smoke coverage and docs work over new runtime abstractions.
- Keep the repo's release-facing narrative honest: if behavior or validation state changes, update the handoff and any affected release-facing docs in the same change set.

Target outcome:
- Add a live smoke path that exercises at least one persisted failed import run for a non-site failure bucket and its shared-visibility behavior under a current pilot overlay.
- Confirm the smoke still reaches the existing web surfaces, including `/imports`.
- Document how to run that failed-run shared-visibility smoke against the current pilot overlays.

Expected work:
- Extend the current smoke helper with a narrowly scoped failed-run shared-visibility mode or add a tightly scoped sibling script.
- Reuse the existing failure import endpoints and audit routes rather than inventing a second verification path.
- Add verification coverage appropriate to the changed smoke path.
- Update the relevant docs after implementation.
- If release posture or validation evidence changes materially, update /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/CHANGELOG.md and /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/RELEASE_READINESS.md too.
- Run `make validate-strict` at the end.
- If you run live validation, boot the relevant overlay first and record whether the smoke passed end to end.

When you finish, update /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/CODEX_HANDOFF.md so the next handoff reflects the new state instead of repeating this prompt.
```
