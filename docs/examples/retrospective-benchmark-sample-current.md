# External Benchmark Snapshot

- Generated at: 2026-03-27T06:05:36.583179Z
- Dataset: deidentified-retrospective-multicohort-sample (validation)
- De-identified: True
- Labels: `docs/examples/retrospective-benchmark-sample-labels.jsonl`
- Predictions: `docs/examples/retrospective-benchmark-sample-predictions.jsonl`
- Manifest: `docs/examples/retrospective-benchmark-sample-manifest.json`
- Threshold: 0.30
- Top-k: 5

## Dataset Framing

- Dataset description: Checked-in retrospective-style benchmark sample used to show how a less-synthetic collaborator pack can preserve the same reviewer-facing proof shape as the demo benchmark.
- Labeling policy: This sample remains deidentified and intentionally bounded for repository use. Labels emphasize reviewer-visible pancreatic risk, actionable follow-up, and escalation cues rather than autonomous diagnostic claims.
- Notes: Repository sample for public proof only. This is not a clinical validation dataset.

## Dataset Coverage

- Reports in casebook: 12
- Positive labels: 8
- Escalation labels: 5
- Benchmark buckets: 5
- `explicit malignancy`: 3 case(s), 3 positive, 3 escalation-tagged — Reports with overt lesion or malignancy wording that should stay easy to justify in a reviewed queue.
- `follow-up only`: 3 case(s), 3 positive, 0 escalation-tagged — Cases where the operational signal is pancreatic follow-up or workup language rather than explicit malignancy wording.
- `negative control`: 2 case(s), 0 positive, 0 escalation-tagged — Clearly nonsuspicious pancreatic reports that should stay out of the flagged worklist.
- `pancreatitis confounder`: 2 case(s), 0 positive, 0 escalation-tagged — Specificity checks where inflammatory language can look worrisome without supporting suspicious morphology.
- `secondary signs`: 2 case(s), 2 positive, 2 escalation-tagged — Cases driven by ductal obstruction, atrophy, or related pancreatic risk cues without always naming a mass.

## Cohort Coverage

- `community CT intake`: 4 case(s), 2 positive, 2 flagged, 0 missed positive — Front-door abdomen CT intake cases that mix overt lesions, secondary-sign patterns, and negative controls.
- `referral pancreas review`: 4 case(s), 2 positive, 3 flagged, 0 missed positive — Navigator-style referral review cases that keep reviewer-facing excerpts and confounders visible in the same proof shape.
- `tertiary MRI workup`: 4 case(s), 4 positive, 3 flagged, 1 missed positive — Referral MRI workup cases with richer pancreatic follow-up cues and one intentional follow-up-only miss.

## Summary

| Mode | Precision | Recall | F1 | Flagged | Top-k Precision | Top-k Sensitivity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| External | 0.8750 | 0.8750 | 0.8750 | 8 | 1.0000 | 0.6250 |

- Positives: 8 of 12
- Reviewer yield at top-5: 1.0000
- Top flagged case IDs: C-RETRO-001, C-RETRO-006, C-RETRO-012, C-RETRO-002, C-RETRO-008
- Missed positive case IDs: C-RETRO-007
- False negative buckets: recommendation_language_missed=1

## Top-k Queue Preview

- External top-5: C-RETRO-001 (community CT intake, explicit malignancy, true_positive, 0.9400) -> C-RETRO-006 (community CT intake, explicit malignancy, true_positive, 0.7900) -> C-RETRO-012 (referral pancreas review, explicit malignancy, true_positive, 0.7400) -> C-RETRO-002 (tertiary MRI workup, secondary signs, true_positive, 0.6800) -> C-RETRO-008 (referral pancreas review, secondary signs, true_positive, 0.5700)

## Threshold Sweep

| Threshold | Precision | Recall | F1 | Flagged | Top-k Precision | Top-k Sensitivity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.20 | 0.7778 | 0.8750 | 0.8235 | 9 | 1.0000 | 0.6250 |
| 0.30 | 0.8750 | 0.8750 | 0.8750 | 8 | 1.0000 | 0.6250 |
| 0.40 | 1.0000 | 0.6250 | 0.7692 | 5 | 1.0000 | 0.6250 |
| 0.50 | 1.0000 | 0.6250 | 0.7692 | 5 | 1.0000 | 0.6250 |
| 0.60 | 1.0000 | 0.5000 | 0.6667 | 4 | 1.0000 | 0.6250 |

## Recommended Operating Point

- External: threshold 0.30, F1 0.8750, recall 0.8750, flagged 8
- Rationale: Selected threshold 0.30 because it maximizes F1 (0.88) while preserving recall 0.88 with 8 flagged case(s).

## Submission Draft

- Submission name: `external-deidentified-retrospective-multicohort-sample`
- Project: Pancreatic Signal
- Submission JSON: `docs/examples/retrospective-benchmark-sample-current-submission.json`
- Artifact paths: docs/examples/retrospective-benchmark-sample-current.json, docs/examples/retrospective-benchmark-sample-current.md

## Reviewer Casebook

### C-RETRO-001 — explicit malignancy

- Report: `R-RETRO-001`
- Cohort: community CT intake
- Report excerpt: CT abdomen with contrast: Ill-defined pancreatic head mass with abrupt cutoff of the pancreatic duct and upstream biliary dilatation. Impression: Findings highly concerning for pancreatic adenocarcinoma; endoscopic tissue sampling recommended.
- Reviewer focus: Confirm the mass, duct cutoff, and same-report escalation language remain visible together after de-identification.
- Label note: Pancreatic head mass with abrupt duct cutoff and same-report tissue recommendation.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: PDAC_EXPLICIT_SUSPICION, PANCREATIC_MASS, DUCT_CUTOFF, FOLLOWUP_RECOMMENDED
- External: true_positive at 0.9400 with rationale cues PDAC_EXPLICIT_SUSPICION, PANCREATIC_MASS, DUCT_CUTOFF, FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-RETRO-002 — secondary signs

- Report: `R-RETRO-002`
- Cohort: tertiary MRI workup
- Report excerpt: MRI/MRCP: Double duct sign is present with distal pancreatic atrophy. No discretely measurable mass is seen; recommend EUS to exclude occult pancreatic malignancy.
- Reviewer focus: Escalate the obstructive secondary-sign cluster even though the report stops short of naming a definite mass.
- Label note: Double-duct obstruction with distal atrophy and EUS recommendation but no discretely measurable mass.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: DOUBLE_DUCT_SIGN, FOCAL_ATROPHY, FOLLOWUP_RECOMMENDED
- External: true_positive at 0.6800 with rationale cues DOUBLE_DUCT_SIGN, FOCAL_ATROPHY, FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-RETRO-003 — follow-up only

- Report: `R-RETRO-003`
- Cohort: tertiary MRI workup
- Report excerpt: Pancreas protocol MRI: Stable 1.8 cm side-branch IPMN at the pancreatic neck without enhancing mural nodularity. Impression: Follow-up pancreas MRI in 6 months recommended.
- Reviewer focus: Keep non-malignant but action-worthy cyst surveillance recommendations in the queue.
- Label note: Follow-up-worthy side-branch cyst surveillance case that should stay visible to a reviewer.
- Expected positive: `True` | Expected escalation: `False`
- Expected rationale cues: FOLLOWUP_RECOMMENDED
- External: true_positive at 0.3100 with rationale cues FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-RETRO-004 — pancreatitis confounder

- Report: `R-RETRO-004`
- Cohort: community CT intake
- Report excerpt: CT abdomen: Peripancreatic edema and fluid track along the pancreatic tail, compatible with acute pancreatitis. No focal pancreatic mass or abrupt duct cutoff identified.
- Reviewer focus: Preserve specificity when inflammatory change is present but suspicious pancreatic morphology is explicitly denied.
- Label note: Inflammatory pancreatitis confounder with explicit negation of a mass or duct cutoff.
- Expected positive: `False` | Expected escalation: `False`
- Expected rationale cues: none
- External: true_negative at 0.2900 with rationale cues none
- Reviewed false-negative bucket: none recorded

### C-RETRO-005 — negative control

- Report: `R-RETRO-005`
- Cohort: referral pancreas review
- Report excerpt: CT abdomen and pelvis: Pancreas enhances normally. No focal pancreatic lesion, no ductal dilatation, and no peripancreatic inflammatory change.
- Reviewer focus: Keep clearly normal pancreatic reports out of the flagged queue.
- Label note: Clean negative control with normal pancreas and no follow-up recommendation.
- Expected positive: `False` | Expected escalation: `False`
- Expected rationale cues: none
- External: true_negative at 0.0400 with rationale cues none
- Reviewed false-negative bucket: none recorded

### C-RETRO-006 — explicit malignancy

- Report: `R-RETRO-006`
- Cohort: community CT intake
- Report excerpt: Pancreas protocol CT: Focal hypoenhancement in the uncinate process with interruption of the downstream pancreatic duct raises concern for an underlying neoplastic process. Tissue diagnosis is advised.
- Reviewer focus: Do not miss less formulaic neoplastic wording when it still pairs a focal abnormality with duct interruption and biopsy advice.
- Label note: Less formulaic malignancy wording with uncinate hypoenhancement, duct interruption, and biopsy recommendation.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: PANCREATIC_MASS, DUCT_CUTOFF, FOLLOWUP_RECOMMENDED
- External: true_positive at 0.7900 with rationale cues PANCREATIC_MASS, DUCT_CUTOFF, FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-RETRO-007 — follow-up only

- Report: `R-RETRO-007`
- Cohort: tertiary MRI workup
- Report excerpt: MRI abdomen: Clustered pancreatic tail cysts are again seen, the largest slightly increased in size. Impression: Likely branch duct IPMN; short-interval MR follow-up suggested.
- Reviewer focus: Surface interval-growth surveillance recommendations even when malignancy language is absent.
- Label note: Follow-up-only cyst case with interval growth language that is easy to underrank.
- Expected positive: `True` | Expected escalation: `False`
- Expected rationale cues: FOLLOWUP_RECOMMENDED
- External: missed_positive at 0.1700 with rationale cues FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: recommendation_language_missed

### C-RETRO-008 — secondary signs

- Report: `R-RETRO-008`
- Cohort: referral pancreas review
- Report excerpt: CT pancreas protocol: Mild prominence of the main pancreatic duct with focal distal body atrophy and subtle fullness near the neck. Impression: occult pancreatic lesion remains a concern; recommend EUS correlation.
- Reviewer focus: Keep subtle obstructive-pattern CT findings visible when the report only hints at an occult lesion.
- Label note: Subtle ductal prominence plus focal atrophy with EUS recommendation despite no discrete mass callout.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: DUCT_DILATION, FOCAL_ATROPHY, FOLLOWUP_RECOMMENDED
- External: true_positive at 0.5700 with rationale cues DUCT_DILATION, FOCAL_ATROPHY, FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-RETRO-009 — follow-up only

- Report: `R-RETRO-009`
- Cohort: tertiary MRI workup
- Report excerpt: MRI pancreas surveillance: Multiloculated 2.1 cm cyst in the uncinate process with thin septations but no nodular enhancement. Impression: interval follow-up MRI in 6 months recommended.
- Reviewer focus: Surface structured surveillance language even when the report stays firmly in benign cyst follow-up framing.
- Label note: Surveillance MRI recommendation for a slowly enlarging uncinate cyst should remain reviewable.
- Expected positive: `True` | Expected escalation: `False`
- Expected rationale cues: FOLLOWUP_RECOMMENDED
- External: true_positive at 0.3300 with rationale cues FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-RETRO-010 — pancreatitis confounder

- Report: `R-RETRO-010`
- Cohort: referral pancreas review
- Report excerpt: CT abdomen: Chronic pancreatitis with scattered pancreatic calcifications and mild ductal irregularity. No focal pancreatic mass is identified; recommend clinical follow-up if symptoms persist.
- Reviewer focus: Review whether chronic inflammatory duct irregularity is being overcalled as a pancreatic triage signal.
- Label note: Chronic pancreatitis confounder with duct irregularity but no focal lesion; useful for visible false-positive review.
- Expected positive: `False` | Expected escalation: `False`
- Expected rationale cues: none
- External: false_positive at 0.3400 with rationale cues DUCT_DILATION
- Reviewed false-negative bucket: none recorded

### C-RETRO-011 — negative control

- Report: `R-RETRO-011`
- Cohort: community CT intake
- Report excerpt: Portal venous phase CT: Pancreas is homogeneous without ductal dilatation, focal lesion, or peripancreatic inflammatory change.
- Reviewer focus: Keep straightforward normal CT intake studies out of the queue.
- Label note: Clean CT negative control with an explicitly normal pancreas.
- Expected positive: `False` | Expected escalation: `False`
- Expected rationale cues: none
- External: true_negative at 0.0700 with rationale cues none
- Reviewed false-negative bucket: none recorded

### C-RETRO-012 — explicit malignancy

- Report: `R-RETRO-012`
- Cohort: referral pancreas review
- Report excerpt: CT abdomen and pelvis: Hypoenhancing 2.4 cm lesion at the pancreatic neck with upstream duct dilatation and abutment of the SMV. Impression: pancreatic neoplasm is favored; urgent tissue sampling is advised.
- Reviewer focus: Keep explicit lesion language, ductal obstruction, and urgent tissue follow-up tightly linked for reviewers.
- Label note: Hypoenhancing pancreatic neck lesion with upstream duct dilatation and urgent tissue recommendation.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: PDAC_EXPLICIT_SUSPICION, PANCREATIC_MASS, DUCT_DILATION, FOLLOWUP_RECOMMENDED
- External: true_positive at 0.7400 with rationale cues PDAC_EXPLICIT_SUSPICION, PANCREATIC_MASS, DUCT_DILATION, FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded
