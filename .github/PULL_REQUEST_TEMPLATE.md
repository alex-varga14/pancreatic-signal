# Summary

<!-- What does this change and why? Link related issues. -->

## Validation

<!-- Check what you ran. `make validate-strict` is the pre-merge gate. -->

- [ ] `make validate-strict` passes locally
- [ ] New or changed behavior is covered by tests
- [ ] Docs updated where behavior changed (API_SPEC, DEPLOYMENT, README, etc.)

## Safety posture

- [ ] No PHI, real patient data, or secrets in code, fixtures, or docs
- [ ] No clinical-validation or regulatory claims introduced
- [ ] Deterministic, explainable triage path is preserved (no opaque decision-making in its place)
