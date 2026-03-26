# Demo Benchmark Snapshot

- Generated at: 2026-03-26T04:20:28.913152Z
- Reports: `data/examples/reports.jsonl`
- Labels: `data/examples/report_labels.jsonl`
- Comparison threshold: 0.30
- Top-k: 3

## Dataset Coverage

- Reports in casebook: 10
- Positive labels: 7
- Escalation labels: 5
- Benchmark buckets: 5
- `explicit malignancy`: 2 case(s), 2 positive, 2 escalation-tagged
- `follow-up only`: 2 case(s), 2 positive, 0 escalation-tagged
- `negative control`: 1 case(s), 0 positive, 0 escalation-tagged
- `pancreatitis confounder`: 2 case(s), 0 positive, 0 escalation-tagged
- `secondary signs`: 3 case(s), 3 positive, 3 escalation-tagged

## Comparison

| Mode | Precision | Recall | F1 | Flagged | Top-k Precision | Top-k Sensitivity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Rules | 1.0000 | 0.7143 | 0.8333 | 5 | 1.0000 | 0.4286 |
| Hybrid | 1.0000 | 1.0000 | 1.0000 | 7 | 1.0000 | 0.4286 |

- Hybrid deltas at threshold 0.30: precision +0.0000, recall +0.2857, F1 +0.1667, flagged +2
- Newly flagged by hybrid: C-005, C-008
- Resolved false negatives: C-005, C-008

## Top-k Queue Preview

- Rules top-3: C-001 (explicit malignancy, true_positive, 1.0000) -> C-010 (secondary signs, true_positive, 0.8700) -> C-003 (secondary signs, true_positive, 0.5300)
- Hybrid top-3: C-001 (explicit malignancy, true_positive, 1.0000) -> C-010 (secondary signs, true_positive, 1.0000) -> C-003 (secondary signs, true_positive, 0.9010)

## Threshold Sweep

| Threshold | Rules F1 | Hybrid F1 | Rules Recall | Hybrid Recall | Rules Flagged | Hybrid Flagged |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.20 | 0.8333 | 1.0000 | 0.7143 | 1.0000 | 5 | 7 |
| 0.30 | 0.8333 | 1.0000 | 0.7143 | 1.0000 | 5 | 7 |
| 0.40 | 0.8333 | 1.0000 | 0.7143 | 1.0000 | 5 | 7 |
| 0.50 | 0.7273 | 0.9231 | 0.5714 | 0.8571 | 4 | 6 |
| 0.60 | 0.4444 | 0.9231 | 0.2857 | 0.8571 | 2 | 6 |

## Recommended Operating Points

- Rules: threshold 0.20, F1 0.8333, recall 0.7143, flagged 5
- Rules rationale: Selected threshold 0.20 because it maximizes F1 (0.83) while preserving recall 0.71 with 5 flagged case(s).
- Hybrid: threshold 0.20, F1 1.0000, recall 1.0000, flagged 7
- Hybrid rationale: Selected threshold 0.20 because it maximizes F1 (1.00) while preserving recall 1.00 with 7 flagged case(s).

## Reviewer Casebook

### C-001 — explicit malignancy

- Report: `R-001`
- Reviewer focus: Confirm the pancreatic head lesion, duct cutoff, and same-report escalation language stay visible together.
- Label note: Explicit lesion, duct cutoff, and EUS/tissue sampling recommendation.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: PDAC_EXPLICIT_SUSPICION, PANCREATIC_MASS, DUCT_CUTOFF, FOLLOWUP_RECOMMENDED
- Rules: true_positive at 1.0000 with rationale cues PDAC_EXPLICIT_SUSPICION, PANCREATIC_MASS, DUCT_CUTOFF, FOLLOWUP_RECOMMENDED
- Hybrid: true_positive at 1.0000 with rationale cues PDAC_EXPLICIT_SUSPICION, PANCREATIC_MASS, DUCT_CUTOFF, FOLLOWUP_RECOMMENDED
- Hybrid lift: +0.0000

### C-002 — pancreatitis confounder

- Report: `R-002`
- Reviewer focus: Avoid overcalling inflammatory change when the report explicitly says no discrete pancreatic mass.
- Label note: Pancreatitis without a discrete mass.
- Expected positive: `False` | Expected escalation: `False`
- Expected rationale cues: none
- Rules: true_negative at 0.0000 with rationale cues none
- Hybrid: true_negative at 0.0000 with rationale cues none
- Hybrid lift: +0.0000

### C-003 — secondary signs

- Report: `R-003`
- Reviewer focus: Treat double duct sign plus focal atrophy as escalation-worthy even without a measurable mass.
- Label note: Double duct sign, focal atrophy, and EUS recommendation.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: DOUBLE_DUCT_SIGN, FOCAL_ATROPHY
- Rules: true_positive at 0.5300 with rationale cues DOUBLE_DUCT_SIGN, FOCAL_ATROPHY
- Hybrid: true_positive at 0.9010 with rationale cues DOUBLE_DUCT_SIGN, FOCAL_ATROPHY
- Hybrid lift: +0.3710

### C-004 — negative control

- Report: `R-004`
- Reviewer focus: Preserve specificity when the pancreas is described as unremarkable and there is no follow-up recommendation.
- Label note: Normal pancreas and no acute abnormality.
- Expected positive: `False` | Expected escalation: `False`
- Expected rationale cues: none
- Rules: true_negative at 0.0000 with rationale cues none
- Hybrid: true_negative at 0.0000 with rationale cues none
- Hybrid lift: +0.0000

### C-005 — follow-up only

- Report: `R-005`
- Reviewer focus: Keep action-worthy cyst surveillance recommendations reviewable even when malignancy language is absent.
- Label note: Side-branch IPMN follow-up recommendation should still be reviewable.
- Expected positive: `True` | Expected escalation: `False`
- Expected rationale cues: FOLLOWUP_RECOMMENDED
- Rules: missed_positive at 0.0000 with rationale cues none
- Hybrid: true_positive at 0.4400 with rationale cues none
- Hybrid lift: +0.4400

### C-006 — explicit malignancy

- Report: `R-006`
- Reviewer focus: Do not miss malignancy wording variance when the report couples double-duct obstruction with an immediate EUS/tissue-sampling recommendation.
- Label note: Double-duct obstruction plus worrisome malignancy wording with same-report tissue confirmation recommendation.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: DOUBLE_DUCT_SIGN, FOLLOWUP_RECOMMENDED
- Rules: true_positive at 0.4900 with rationale cues DOUBLE_DUCT_SIGN, FOLLOWUP_RECOMMENDED
- Hybrid: true_positive at 0.7200 with rationale cues DOUBLE_DUCT_SIGN, FOLLOWUP_RECOMMENDED
- Hybrid lift: +0.2300

### C-007 — secondary signs

- Report: `R-007`
- Reviewer focus: Escalate duct dilation plus distal atrophy even when the report frames the lesion as occult rather than measurable.
- Label note: Main duct dilation, distal atrophy, and EUS recommendation without a named mass.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: DUCT_DILATION, FOCAL_ATROPHY, FOLLOWUP_RECOMMENDED
- Rules: true_positive at 0.5200 with rationale cues DUCT_DILATION, FOCAL_ATROPHY, FOLLOWUP_RECOMMENDED
- Hybrid: true_positive at 0.8630 with rationale cues DUCT_DILATION, FOCAL_ATROPHY, FOLLOWUP_RECOMMENDED
- Hybrid lift: +0.3430

### C-008 — follow-up only

- Report: `R-008`
- Reviewer focus: Keep follow-up-worthy pancreatic cyst recommendations visible even when only interval surveillance language is explicit.
- Label note: Pancreatic cyst surveillance recommendation should remain reviewable in the benchmark queue.
- Expected positive: `True` | Expected escalation: `False`
- Expected rationale cues: FOLLOWUP_RECOMMENDED
- Rules: missed_positive at 0.1400 with rationale cues FOLLOWUP_RECOMMENDED
- Hybrid: true_positive at 0.6290 with rationale cues FOLLOWUP_RECOMMENDED
- Hybrid lift: +0.4890

### C-009 — pancreatitis confounder

- Report: `R-009`
- Reviewer focus: Protect specificity when chronic pancreatitis language coexists with explicit negation of pancreatic mass and obstruction.
- Label note: Chronic pancreatitis with explicit negation of mass and ductal interruption.
- Expected positive: `False` | Expected escalation: `False`
- Expected rationale cues: none
- Rules: true_negative at 0.0000 with rationale cues none
- Hybrid: true_negative at 0.0000 with rationale cues none
- Hybrid lift: +0.0000

### C-010 — secondary signs

- Report: `R-010`
- Reviewer focus: Treat clustered obstructive secondary signs plus biopsy recommendation as reviewer-priority even before explicit malignancy wording appears.
- Label note: Obstructive pattern cluster with duct cutoff, duct prominence, adjacent atrophy, and biopsy recommendation.
- Expected positive: `True` | Expected escalation: `True`
- Expected rationale cues: DUCT_CUTOFF, DUCT_DILATION, FOCAL_ATROPHY, FOLLOWUP_RECOMMENDED
- Rules: true_positive at 0.8700 with rationale cues DUCT_DILATION, DUCT_CUTOFF, FOCAL_ATROPHY, FOLLOWUP_RECOMMENDED
- Hybrid: true_positive at 1.0000 with rationale cues DUCT_DILATION, DUCT_CUTOFF, FOCAL_ATROPHY, FOLLOWUP_RECOMMENDED
- Hybrid lift: +0.1300
