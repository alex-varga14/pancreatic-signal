# Demo Benchmark Snapshot

- Generated at: 2026-03-23T05:42:57.019090Z
- Reports: `data/examples/reports.jsonl`
- Labels: `data/examples/report_labels.jsonl`
- Comparison threshold: 0.30
- Top-k: 3

## Comparison

| Mode | Precision | Recall | F1 | Flagged | Top-k Precision | Top-k Sensitivity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Rules | 1.0000 | 0.6667 | 0.8000 | 2 | 0.6667 | 0.6667 |
| Hybrid | 1.0000 | 1.0000 | 1.0000 | 3 | 1.0000 | 1.0000 |

- Hybrid deltas at threshold 0.30: precision +0.0000, recall +0.3333, F1 +0.2000, flagged +1
- Newly flagged by hybrid: C-005
- Resolved false negatives: C-005

## Threshold Sweep

| Threshold | Rules F1 | Hybrid F1 | Rules Recall | Hybrid Recall | Rules Flagged | Hybrid Flagged |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.20 | 0.8000 | 1.0000 | 0.6667 | 1.0000 | 2 | 3 |
| 0.30 | 0.8000 | 1.0000 | 0.6667 | 1.0000 | 2 | 3 |
| 0.40 | 0.8000 | 1.0000 | 0.6667 | 1.0000 | 2 | 3 |
| 0.50 | 0.8000 | 0.8000 | 0.6667 | 0.6667 | 2 | 2 |
| 0.60 | 0.5000 | 0.8000 | 0.3333 | 0.6667 | 1 | 2 |

## Recommended Operating Points

- Rules: threshold 0.20, F1 0.8000, recall 0.6667, flagged 2
- Rules rationale: Selected threshold 0.20 because it maximizes F1 (0.80) while preserving recall 0.67 with 2 flagged case(s).
- Hybrid: threshold 0.20, F1 1.0000, recall 1.0000, flagged 3
- Hybrid rationale: Selected threshold 0.20 because it maximizes F1 (1.00) while preserving recall 1.00 with 3 flagged case(s).
