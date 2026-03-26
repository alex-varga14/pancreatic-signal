# External Benchmark Snapshot

- Generated at: 2026-03-26T04:49:06.513673Z
- Dataset: deidentified-retrospective-sample (validation)
- De-identified: True
- Labels: `docs/examples/retrospective-benchmark-sample-labels.jsonl`
- Predictions: `docs/examples/retrospective-benchmark-sample-predictions.jsonl`
- Threshold: 0.30
- Top-k: 4

## Dataset Coverage

- Reports in casebook: 7
- Positive labels: 5
- Escalation labels: 3
- Benchmark buckets: 5
- `explicit malignancy`: 2 case(s), 2 positive, 2 escalation-tagged
- `follow-up only`: 2 case(s), 2 positive, 0 escalation-tagged
- `negative control`: 1 case(s), 0 positive, 0 escalation-tagged
- `pancreatitis confounder`: 1 case(s), 0 positive, 0 escalation-tagged
- `secondary signs`: 1 case(s), 1 positive, 1 escalation-tagged

## Summary

| Mode | Precision | Recall | F1 | Flagged | Top-k Precision | Top-k Sensitivity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| External | 1.0000 | 0.8000 | 0.8889 | 4 | 1.0000 | 0.8000 |

- Positives: 5 of 7
- Reviewer yield at top-4: 1.0000
- Top flagged case IDs: C-RETRO-001, C-RETRO-006, C-RETRO-002, C-RETRO-003
- Missed positive case IDs: C-RETRO-007
- False negative buckets: recommendation_language_missed=1

## Top-k Queue Preview

- External top-4: C-RETRO-001 (explicit malignancy, true_positive, 0.9400) -> C-RETRO-006 (explicit malignancy, true_positive, 0.7900) -> C-RETRO-002 (secondary signs, true_positive, 0.6800) -> C-RETRO-003 (follow-up only, true_positive, 0.3100)

## Threshold Sweep

| Threshold | Precision | Recall | F1 | Flagged | Top-k Precision | Top-k Sensitivity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.20 | 0.8000 | 0.8000 | 0.8000 | 5 | 1.0000 | 0.8000 |
| 0.30 | 1.0000 | 0.8000 | 0.8889 | 4 | 1.0000 | 0.8000 |
| 0.40 | 1.0000 | 0.6000 | 0.7500 | 3 | 1.0000 | 0.8000 |
| 0.50 | 1.0000 | 0.6000 | 0.7500 | 3 | 1.0000 | 0.8000 |
| 0.60 | 1.0000 | 0.6000 | 0.7500 | 3 | 1.0000 | 0.8000 |

## Recommended Operating Point

- External: threshold 0.30, F1 0.8889, recall 0.8000, flagged 4
- Rationale: Selected threshold 0.30 because it maximizes F1 (0.89) while preserving recall 0.80 with 4 flagged case(s).

## Submission Draft

- Submission name: `external-deidentified-retrospective-sample`
- Project: Pancreatic Signal
- Submission JSON: `docs/examples/retrospective-benchmark-sample-current-submission.json`
- Artifact paths: docs/examples/retrospective-benchmark-sample-current.json, docs/examples/retrospective-benchmark-sample-current.md

## Reviewer Casebook

### C-RETRO-001 — explicit malignancy

- Report: `R-RETRO-001`
- Report excerpt: CT abdomen with contrast: Ill-defined pancreatic head mass with abrupt cutoff of the pancreatic duct and upstream biliary dilatation. Impression: Findings highly concerning for pancreatic adenocarcinoma; endoscopic tissue sampling recommended.
- Reviewer focus: Confirm the mass, duct cutoff, and same-report escalation language remain visible together after de-identification.
- Label note: Pancreatic head mass with abrupt duct cutoff and same-report tissue recommendation.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: PDAC_EXPLICIT_SUSPICION, PANCREATIC_MASS, DUCT_CUTOFF, FOLLOWUP_RECOMMENDED
- External: true_positive at 0.9400 with rationale cues PDAC_EXPLICIT_SUSPICION, PANCREATIC_MASS, DUCT_CUTOFF, FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-RETRO-002 — secondary signs

- Report: `R-RETRO-002`
- Report excerpt: MRI/MRCP: Double duct sign is present with distal pancreatic atrophy. No discretely measurable mass is seen; recommend EUS to exclude occult pancreatic malignancy.
- Reviewer focus: Escalate the obstructive secondary-sign cluster even though the report stops short of naming a definite mass.
- Label note: Double-duct obstruction with distal atrophy and EUS recommendation but no discretely measurable mass.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: DOUBLE_DUCT_SIGN, FOCAL_ATROPHY, FOLLOWUP_RECOMMENDED
- External: true_positive at 0.6800 with rationale cues DOUBLE_DUCT_SIGN, FOCAL_ATROPHY, FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-RETRO-003 — follow-up only

- Report: `R-RETRO-003`
- Report excerpt: Pancreas protocol MRI: Stable 1.8 cm side-branch IPMN at the pancreatic neck without enhancing mural nodularity. Impression: Follow-up pancreas MRI in 6 months recommended.
- Reviewer focus: Keep non-malignant but action-worthy cyst surveillance recommendations in the queue.
- Label note: Follow-up-worthy side-branch cyst surveillance case that should stay visible to a reviewer.
- Expected positive: `True` | Expected escalation: `False`
- Expected rationale cues: FOLLOWUP_RECOMMENDED
- External: true_positive at 0.3100 with rationale cues FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-RETRO-004 — pancreatitis confounder

- Report: `R-RETRO-004`
- Report excerpt: CT abdomen: Peripancreatic edema and fluid track along the pancreatic tail, compatible with acute pancreatitis. No focal pancreatic mass or abrupt duct cutoff identified.
- Reviewer focus: Preserve specificity when inflammatory change is present but suspicious pancreatic morphology is explicitly denied.
- Label note: Inflammatory pancreatitis confounder with explicit negation of a mass or duct cutoff.
- Expected positive: `False` | Expected escalation: `False`
- Expected rationale cues: none
- External: true_negative at 0.2900 with rationale cues none
- Reviewed false-negative bucket: none recorded

### C-RETRO-005 — negative control

- Report: `R-RETRO-005`
- Report excerpt: CT abdomen and pelvis: Pancreas enhances normally. No focal pancreatic lesion, no ductal dilatation, and no peripancreatic inflammatory change.
- Reviewer focus: Keep clearly normal pancreatic reports out of the flagged queue.
- Label note: Clean negative control with normal pancreas and no follow-up recommendation.
- Expected positive: `False` | Expected escalation: `False`
- Expected rationale cues: none
- External: true_negative at 0.0400 with rationale cues none
- Reviewed false-negative bucket: none recorded

### C-RETRO-006 — explicit malignancy

- Report: `R-RETRO-006`
- Report excerpt: Pancreas protocol CT: Focal hypoenhancement in the uncinate process with interruption of the downstream pancreatic duct raises concern for an underlying neoplastic process. Tissue diagnosis is advised.
- Reviewer focus: Do not miss less formulaic neoplastic wording when it still pairs a focal abnormality with duct interruption and biopsy advice.
- Label note: Less formulaic malignancy wording with uncinate hypoenhancement, duct interruption, and biopsy recommendation.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: PANCREATIC_MASS, DUCT_CUTOFF, FOLLOWUP_RECOMMENDED
- External: true_positive at 0.7900 with rationale cues PANCREATIC_MASS, DUCT_CUTOFF, FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-RETRO-007 — follow-up only

- Report: `R-RETRO-007`
- Report excerpt: MRI abdomen: Clustered pancreatic tail cysts are again seen, the largest slightly increased in size. Impression: Likely branch duct IPMN; short-interval MR follow-up suggested.
- Reviewer focus: Surface interval-growth surveillance recommendations even when malignancy language is absent.
- Label note: Follow-up-only cyst case with interval growth language that is easy to underrank.
- Expected positive: `True` | Expected escalation: `False`
- Expected rationale cues: FOLLOWUP_RECOMMENDED
- External: missed_positive at 0.1700 with rationale cues FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: recommendation_language_missed
