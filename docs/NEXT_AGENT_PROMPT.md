# Next Agent Prompt

Use this as the starting prompt for the next coding agent:

```text
Analyze the repo, then read /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/CODEX_HANDOFF.md, /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/PHASES.md, /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/API_SPEC.md, /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/DEPLOYMENT.md, /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/README.md, and /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/RELEASE_READINESS.md.

Proceed with the next recommended slice from the handoff: CI-backed validation automation for pull requests.

Constraints:
- Preserve deterministic explainability and the existing backend plus web import flow.
- Do not regress auth, site scoping, research-safe de-identification, reviewer workflow behavior, the import metadata preservation path, the import-run audit surfaces, the `/imports` workspace, the generic `/imports/reports` smoke path, the generic failed-shared-visibility smoke path, the structured failed-shared-visibility smoke path, the structured adapter site-rejection smoke path, the structured adapter audit-visibility smoke path, the header-demo shared-visibility, adapter-shared-visibility, FHIR/HL7, site-rejection, parse-validation, adapter-failure, and audit-visibility smoke paths, the proxy-demo shared-visibility, adapter-shared-visibility, FHIR/HL7, site-rejection, parse-validation, adapter-failure, and audit-visibility smoke paths, or the proxy/header pilot packaging.
- Keep capability gating aligned with `/api/v1/auth/me`.
- Prefer additive smoke coverage and docs work over new runtime abstractions.
- Keep the repo's release-facing narrative honest: if behavior or validation state changes, update the handoff and any affected release-facing docs in the same change set.

Target outcome:
- Add CI validation that runs `make validate-strict` on pull requests and the default branch.
- Keep the repo's local and hosted validation story aligned and clearly documented.
- Document what still requires manual live overlay validation outside CI.

Expected work:
- Add a checked-in GitHub Actions workflow rather than inventing a second validation entrypoint.
- Reuse `make validate-strict` so local and CI validation stay aligned.
- Update the relevant docs after implementation, especially if CI changes the release or contributor narrative.
- Update the relevant docs after implementation.
- If release posture or validation evidence changes materially, update /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/CHANGELOG.md and /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/RELEASE_READINESS.md too.
- Run `make validate-strict` at the end.
- If you run live validation, boot the relevant overlay first and record whether the smoke passed end to end.

When you finish, update /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/CODEX_HANDOFF.md so the next handoff reflects the new state instead of repeating this prompt.
```
