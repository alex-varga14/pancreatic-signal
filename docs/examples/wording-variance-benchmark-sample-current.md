# External Benchmark Snapshot

- Generated at: 2026-03-27T06:49:08.782172Z
- Dataset: deidentified-wording-variance-challenge-sample (challenge)
- De-identified: True
- Labels: `docs/examples/wording-variance-benchmark-sample-labels.jsonl`
- Predictions: `docs/examples/wording-variance-benchmark-sample-predictions.jsonl`
- Manifest: `docs/examples/wording-variance-benchmark-sample-manifest.json`
- Threshold: 0.35
- Top-k: 4

## Dataset Framing

- Dataset description: Checked-in wording-variance challenge pack used to keep softer suspicion language, optional follow-up recommendations, and inflammatory confounders visible in the public proof surface.
- Labeling policy: This deidentified repository sample emphasizes reviewer-visible pancreatic concern, follow-up language, and confounder handling rather than autonomous diagnostic claims. Labels were shaped to preserve the ambiguity a reviewer would still need to inspect.
- Notes: Repository challenge pack for public proof only. This is not a clinical validation dataset.

## Dataset Coverage

- Reports in casebook: 9
- Positive labels: 6
- Escalation labels: 4
- Benchmark buckets: 5
- `explicit malignancy`: 2 case(s), 2 positive, 2 escalation-tagged — Reports with direct lesion or malignant-process wording that should remain easy to justify in a reviewed queue.
- `follow-up only`: 2 case(s), 2 positive, 0 escalation-tagged — Operationally important pancreatic follow-up recommendations that can sound optional enough to miss.
- `implicit concern`: 2 case(s), 2 positive, 2 escalation-tagged — Cases driven by focal fullness, duct change, or hedged occult-lesion language instead of a direct mass declaration.
- `negative control`: 2 case(s), 0 positive, 0 escalation-tagged — Clearly nonsuspicious pancreatic reports that should stay out of the flagged queue.
- `pancreatitis confounder`: 1 case(s), 0 positive, 0 escalation-tagged — Specificity checks where inflammatory duct prominence risks being overcalled as a suspicious pancreatic signal.

## Cohort Coverage

- `MR surveillance callbacks`: 2 case(s), 2 positive, 1 flagged, 1 missed positive — Surveillance MRI cases centered on cyst follow-up language, interval wording, and optional-sounding reimaging recommendations.
- `community CT wording review`: 3 case(s), 2 positive, 3 flagged, 0 missed positive — Front-door CT cases where softer phrasing and inflammatory change can blur the line between a true pancreatic cue and a confounder.
- `navigator adjudication queue`: 4 case(s), 2 positive, 2 flagged, 0 missed positive — Navigator-style review cases that mix high-acuity lesion language, equivocal focal fullness, and clearly benign negatives.

## Summary

| Mode | Precision | Recall | F1 | Flagged | Top-k Precision | Top-k Sensitivity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| External | 0.8333 | 0.8333 | 0.8333 | 6 | 1.0000 | 0.6667 |

- Positives: 6 of 9
- Reviewer yield at top-4: 1.0000
- Top flagged case IDs: C-WORD-001, C-WORD-009, C-WORD-002, C-WORD-006
- Missed positive case IDs: C-WORD-007
- False negative buckets: recommendation_language_missed=1

## Top-k Queue Preview

- External top-4: C-WORD-001 (community CT wording review, explicit malignancy, true_positive, 0.9100) -> C-WORD-009 (navigator adjudication queue, explicit malignancy, true_positive, 0.7100) -> C-WORD-002 (community CT wording review, implicit concern, true_positive, 0.6400) -> C-WORD-006 (navigator adjudication queue, implicit concern, true_positive, 0.5800)

## Threshold Sweep

| Threshold | Precision | Recall | F1 | Flagged | Top-k Precision | Top-k Sensitivity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.20 | 0.8571 | 1.0000 | 0.9231 | 7 | 1.0000 | 0.6667 |
| 0.30 | 0.8333 | 0.8333 | 0.8333 | 6 | 1.0000 | 0.6667 |
| 0.40 | 1.0000 | 0.6667 | 0.8000 | 4 | 1.0000 | 0.6667 |
| 0.50 | 1.0000 | 0.6667 | 0.8000 | 4 | 1.0000 | 0.6667 |
| 0.60 | 1.0000 | 0.5000 | 0.6667 | 3 | 1.0000 | 0.6667 |

## Recommended Operating Point

- External: threshold 0.20, F1 0.9231, recall 1.0000, flagged 7
- Rationale: Selected threshold 0.20 because it maximizes F1 (0.92) while preserving recall 1.00 with 7 flagged case(s).

## Submission Draft

- Submission name: `external-deidentified-wording-variance-challenge-sample`
- Project: Pancreatic Signal
- Submission JSON: `docs/examples/wording-variance-benchmark-sample-current-submission.json`
- Artifact paths: docs/examples/wording-variance-benchmark-sample-current.json, docs/examples/wording-variance-benchmark-sample-current.md

## Reviewer Casebook

### C-WORD-001 — explicit malignancy

- Report: `R-WORD-001`
- Cohort: community CT wording review
- Report excerpt: CT abdomen with contrast: Ill-defined hypoattenuating lesion at the pancreatic tail with upstream duct caliber change. Impression: infiltrative pancreatic neoplasm is suspected; EUS-guided tissue sampling is recommended.
- Reviewer focus: Keep softer but still explicit neoplasm suspicion linked to the tissue recommendation.
- Label note: Softer explicit neoplasm phrasing with tissue recommendation and duct caliber change.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: PDAC_EXPLICIT_SUSPICION, PANCREATIC_MASS, DUCT_DILATION, FOLLOWUP_RECOMMENDED
- External: true_positive at 0.9100 with rationale cues PDAC_EXPLICIT_SUSPICION, PANCREATIC_MASS, DUCT_DILATION, FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-WORD-002 — implicit concern

- Report: `R-WORD-002`
- Cohort: community CT wording review
- Report excerpt: CT pancreas protocol: Mild loss of normal lobulation at the pancreatic neck with distal duct prominence. Impression: occult pancreatic malignancy is not excluded; dedicated pancreas protocol CT is recommended.
- Reviewer focus: Surface softer not-excluded wording when it rides with focal pancreatic morphology.
- Label note: Subtle contour change and distal duct prominence with occult malignancy not excluded.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: DUCT_DILATION, FOLLOWUP_RECOMMENDED
- External: true_positive at 0.6400 with rationale cues DUCT_DILATION, FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-WORD-003 — follow-up only

- Report: `R-WORD-003`
- Cohort: MR surveillance callbacks
- Report excerpt: MRI abdomen: Branch-duct IPMN at the pancreatic body shows mild interval septal thickening without enhancing nodularity. Impression: follow-up pancreas MRI in 6 months is recommended.
- Reviewer focus: Keep pancreatic surveillance instructions reviewable even when cancer wording is absent.
- Label note: Branch-duct cyst surveillance case with interval septal thickening and a clear MRI follow-up recommendation.
- Expected positive: `True` | Expected escalation: `False`
- Expected rationale cues: FOLLOWUP_RECOMMENDED
- External: true_positive at 0.3900 with rationale cues FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-WORD-004 — pancreatitis confounder

- Report: `R-WORD-004`
- Cohort: community CT wording review
- Report excerpt: CT abdomen: Acute-on-chronic pancreatitis with mild main duct prominence and peripancreatic inflammatory change. No focal pancreatic mass is identified.
- Reviewer focus: Avoid turning inflammatory duct prominence into a false alarm when mass language is explicitly denied.
- Label note: Acute-on-chronic pancreatitis with transient duct prominence and an explicit denial of a focal mass.
- Expected positive: `False` | Expected escalation: `False`
- Expected rationale cues: none
- External: false_positive at 0.3700 with rationale cues DUCT_DILATION
- Reviewed false-negative bucket: none recorded

### C-WORD-005 — negative control

- Report: `R-WORD-005`
- Cohort: navigator adjudication queue
- Report excerpt: MRI abdomen: Pancreas is normal in contour and signal without ductal dilatation, focal lesion, or cystic change.
- Reviewer focus: Keep clean normal surveillance reads out of the queue.
- Label note: Clean MRI negative control with a normal pancreas and no recommendation language.
- Expected positive: `False` | Expected escalation: `False`
- Expected rationale cues: none
- External: true_negative at 0.0500 with rationale cues none
- Reviewed false-negative bucket: none recorded

### C-WORD-006 — implicit concern

- Report: `R-WORD-006`
- Cohort: navigator adjudication queue
- Report excerpt: CT abdomen and pelvis: Focal fullness at the pancreatic head with abrupt termination of an adjacent side branch. Impression: an occult pancreatic lesion remains a concern; GI evaluation and endoscopic correlation are recommended.
- Reviewer focus: Flag focal fullness plus abrupt ductal change even when the report hedges on naming a mass.
- Label note: Focal pancreatic head fullness with abrupt side-branch termination and GI workup advice.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: PANCREATIC_MASS, DUCT_CUTOFF, FOLLOWUP_RECOMMENDED
- External: true_positive at 0.5800 with rationale cues PANCREATIC_MASS, DUCT_CUTOFF, FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded

### C-WORD-007 — follow-up only

- Report: `R-WORD-007`
- Cohort: MR surveillance callbacks
- Report excerpt: MRI pancreas surveillance: Small clustered uncinate cysts are unchanged. Impression: consider repeat pancreas MRI in 12 months to document continued stability.
- Reviewer focus: Make softer optional-sounding surveillance wording visible enough for review.
- Label note: Optional-sounding surveillance recommendation for stable uncinate cyst cluster that is easy to underrank.
- Expected positive: `True` | Expected escalation: `False`
- Expected rationale cues: FOLLOWUP_RECOMMENDED
- External: missed_positive at 0.2200 with rationale cues FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: recommendation_language_missed

### C-WORD-008 — negative control

- Report: `R-WORD-008`
- Cohort: navigator adjudication queue
- Report excerpt: CT abdomen: Mild fatty replacement of the pancreas without ductal dilatation, focal lesion, or peripancreatic stranding.
- Reviewer focus: Do not escalate incidental pancreatic fatty change.
- Label note: Incidental fatty pancreatic change without lesion or follow-up recommendation.
- Expected positive: `False` | Expected escalation: `False`
- Expected rationale cues: none
- External: true_negative at 0.1200 with rationale cues none
- Reviewed false-negative bucket: none recorded

### C-WORD-009 — explicit malignancy

- Report: `R-WORD-009`
- Cohort: navigator adjudication queue
- Report excerpt: CT abdomen and pelvis: Hypoenhancing lesion at the pancreatic neck with mild SMV abutment. Impression: malignant pancreatic process is favored; urgent tissue diagnosis is advised.
- Reviewer focus: Keep high-acuity lesion language and urgent workup recommendation near the top of the queue.
- Label note: High-acuity neck lesion with malignant process favored and urgent biopsy guidance.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: PDAC_EXPLICIT_SUSPICION, PANCREATIC_MASS, FOLLOWUP_RECOMMENDED
- External: true_positive at 0.7100 with rationale cues PDAC_EXPLICIT_SUSPICION, PANCREATIC_MASS, FOLLOWUP_RECOMMENDED
- Reviewed false-negative bucket: none recorded
