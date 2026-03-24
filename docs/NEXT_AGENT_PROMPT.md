# Next Agent Prompt

Use this as the starting prompt for the next coding agent:

```text
Analyze the repo, then read /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/CODEX_HANDOFF.md, /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/PHASES.md, /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/API_SPEC.md, /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/DEPLOYMENT.md, /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/OPEN_SOURCE_STRATEGY.md, /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/README.md, and /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/RELEASE_READINESS.md.

Proceed with the next recommended slice from the handoff: HL7 subcomponent-aware metadata extraction from composite fields.

Constraints:
- Preserve deterministic explainability and the existing import plus reviewer workflow.
- Do not regress auth, site scoping, research-safe de-identification, reviewer workflow behavior, the import metadata preservation path, the import-run audit surfaces, the `/imports` workspace, the checked-in hosted base plus report-path and structured adapter site-rejection smoke workflow, the current pilot smoke matrix, the `/proof` page, the checked-in demo benchmark snapshot, the public benchmark submission pack, or the external evaluation bundle writer.
- Keep interoperability changes additive and explainable; do not introduce a new ingestion family, a second persistence path, or opaque inference.
- Prefer parser, fixture, and docs work over new runtime abstractions.
- Keep the repo's release-facing narrative honest: if behavior or validation state changes, update the handoff and any affected release-facing docs in the same change set.

Target outcome:
- Add at least one meaningful subcomponent-heavy HL7 ORU coverage path driven by `MSH-2` subcomponent handling.
- Preserve import metadata, audit visibility, and site-scope semantics across that subcomponent-aware path.
- Document any new parser expectations introduced by the change.
- Do not add a new adapter family or change the benchmark/public-proof surfaces in this slice unless required to keep docs honest.

Expected work:
- Reuse the existing HL7 import service and tests where possible: `apps/api/app/services/hl7_imports.py`, `apps/api/tests/test_imports.py`, `apps/api/tests/test_import_runs.py`, and the current smoke helper.
- Keep any new adapter behavior traceable to tests and docs rather than configuration magic hidden from contributors.
- Prefer a small subcomponent-aware helper over a parser rewrite, and keep the finding versus impression section assembly behavior understandable.
- Update the relevant docs after implementation, especially if delimiter handling changes the contributor or deployment narrative.
- If release posture or validation evidence changes materially, update /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/CHANGELOG.md and /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/RELEASE_READINESS.md too.
- Run `make validate-strict` at the end.
- If you run live pilot validation, record exactly which overlay or smoke target ran and what passed end to end.

When you finish, update /Users/alexvarga/Coding/personal/POCs/pancan/pancreatic-signal/docs/CODEX_HANDOFF.md so the next handoff reflects the new state instead of repeating this prompt.
```
