# Labeling Guide

This guide defines the label schema used by `data/examples/report_labels.jsonl` and the public benchmark pack.

## Label file format

Each line is one JSON object with these fields:

- `report_id`
- `case_id`
- `suspicious_pancreatic_malignancy`
- `high_risk_pancreatic_abnormality`
- `action_worthy_followup`
- `should_escalate`
- `notes`

See the minimal template in [`docs/examples/benchmark-label-template.jsonl`](./examples/benchmark-label-template.jsonl). To run the new comparable external evaluation helper, pair that label file with a score file that follows [`docs/examples/benchmark-prediction-template.jsonl`](./examples/benchmark-prediction-template.jsonl).

## How the benchmark interprets labels

The current evaluation logic derives `should_flag` as the logical OR of:

- `suspicious_pancreatic_malignancy`
- `high_risk_pancreatic_abnormality`
- `action_worthy_followup`
- `should_escalate`

That means a case can still be benchmark-positive even when it is not labeled as overt malignancy.

Example:
- a side-branch IPMN with a clear follow-up recommendation can be `action_worthy_followup=true`
- an explicitly benign pancreas with no follow-up recommendation should keep all four fields `false`

## Field definitions

### `suspicious_pancreatic_malignancy`

Set to `true` when the report describes wording consistent with likely pancreatic malignancy or a suspicious pancreatic lesion.

Typical examples:
- suspicious pancreatic mass
- pancreatic head lesion concerning for neoplasm
- abrupt duct cutoff with suspicious morphology

Do not set this to `true` for:
- clearly negated lesions
- stable benign cyst language alone
- routine pancreatitis language without suspicious morphology

### `high_risk_pancreatic_abnormality`

Set to `true` when the report contains a pancreatic abnormality that is not explicit malignancy but still represents a high-risk pancreatic signal.

Typical examples:
- double-duct sign
- focal atrophy with ductal abnormality
- indeterminate lesion with worrisome features
- cystic lesion descriptors that should trigger closer review

### `action_worthy_followup`

Set to `true` when the report recommends follow-up or downstream workup that should meaningfully surface in review, even if the malignancy label remains `false`.

Typical examples:
- recommend EUS
- recommend biopsy or tissue sampling
- recommend short-interval pancreatic imaging follow-up

This field is important because operational workflow value often comes from closing the loop on follow-up recommendations, not only from obvious cancers.

### `should_escalate`

Set to `true` when the case should rise above a routine flagged queue and be treated as escalation-worthy by a navigator or reviewer.

Typical examples:
- explicit likely PDAC
- combined mass plus duct cutoff plus urgent tissue recommendation
- language that strongly suggests rapid coordination

## Recommended adjudication workflow

1. Read the full report text, not only the impression.
2. Label the four boolean fields independently.
3. Add a short note describing why the case was labeled that way.
4. Resolve disagreements by citing the phrase that drove the decision.
5. Keep borderline follow-up cases in the dataset instead of deleting them.

## Error bucket rubric

Use these buckets when reviewing misses or when summarizing benchmark failures:

- `negation_failure`
  Positive language was actually negated.
- `historical_not_current`
  Prior or resolved disease was interpreted as current.
- `incidental_cyst_overcall`
  Benign or low-risk cyst language was overcalled.
- `pancreatitis_confounder`
  Inflammatory or pancreatitis language confused the triage logic.
- `secondary_signs_missed`
  The case depended on combinations such as duct dilation, cutoff, or focal atrophy.
- `recommendation_language_missed`
  The important signal was the follow-up recommendation rather than lesion wording.
- `uncommon_wording`
  The language was real but phrased outside common pattern families.

## Labeling principles

- Prefer explicit notes over implicit assumptions.
- Do not encode PHI in notes or examples.
- Keep the benchmark research-first and reproducible.
- Document disagreement policy if multiple reviewers label the same set.
