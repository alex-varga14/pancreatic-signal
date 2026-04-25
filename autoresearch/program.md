# Pancreatic Signal autoresearch program

This document is the **research org instruction** read by an external coding
agent (Cursor / Claude Code / Codex CLI) when it is invoked by
`scripts/run_autoresearch_loop.py`. It is the only file the human research
operator edits to redirect the loop. The agent then proposes a candidate
ontology and the deterministic experiment driver decides whether it is kept,
discarded, or promoted.

This subsystem is inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch).
Mapping:

| karpathy/autoresearch       | pancreatic-signal                                         |
|-----------------------------|-----------------------------------------------------------|
| `program.md` (research org) | `autoresearch/program.md` (this file)                     |
| `train.py` (agent edits)    | `data/ontologies/pancreatic_signal_rules.json` (only file) |
| `prepare.py` (data, fixed)  | `apps/api/app/services/evaluation.py` (read-only)         |
| `val_bpb` (primary metric)  | `f1_at_top_k` on the demo benchmark                       |

The system is **rules-only** in v2.0. The agent must not edit Python source,
schemas, the evaluation pipeline, the imports adapters, or the live database.

---

## 1. Objective

Improve **F1 at top-K** on the bundled demo benchmark
(`apps/api/data/demo_dataset.json`) under the rules score mode while keeping
the published external retrospective sample
(`docs/examples/retrospective-benchmark-sample-*`) at or above its current
recall floor.

Concretely, a candidate ontology is **better than baseline** iff:

1. `rules.f1_at_top_k(K=3, threshold=0.3)` strictly improves vs. baseline.
2. Tiebreak: `rules.recall_at_top_k(K=3, threshold=0.3)` does not regress.
3. External sample `recall` does not drop more than `0.02` absolute.
4. All guardrails in §3 hold.

The agent should not optimize hybrid-only metrics. Hybrid is reported for
visibility but is not a target of this loop in v2.0.

---

## 2. Edit surface

The agent **must edit exactly one file**:

```
data/ontologies/pancreatic_signal_rules.json
```

Permitted edits:

- Add, remove, or rewrite **patterns** within an existing family.
- Add new families with a new unique `code`, `label`, `weight`, and `patterns`.
- Adjust family `weight` values within `[0.0, 1.0]`.
- Add or remove entries in `negations` and `uncertainty`.
- Adjust `thresholds.medium` / `thresholds.high` / `thresholds.critical` within
  `[0.0, 1.0]` while preserving `medium <= high <= critical`.
- Adjust the `scoring` block (`method`, `max_score`, `round_digits`,
  `global_weight`).

Forbidden edits (will be rejected by `OntologyConfig` schema validation):

- Removing required top-level keys (`version`, `families`, `thresholds`).
- Introducing additional top-level keys (the schema is `extra="forbid"`).
- Duplicating a family `code`.
- Setting any weight or threshold outside `[0.0, 1.0]`.
- Changing `scoring.method` to anything other than `additive`, `max`, or
  `weighted_sum`.

The agent **must not** modify any other file in the repo. Any proposal that
touches another path is discarded by the loop with `decision = "off_surface"`.

---

## 3. Guardrails

A candidate is **kept** only if all of the following hold. Failures are logged
in `autoresearch/runs/<id>/decision.json`.

1. **Schema validation**: `OntologyConfig.model_validate` succeeds on the
   candidate ontology JSON.
2. **No silent rationale code deletion**: every `code` present in the baseline
   `families[]` must still be present in the candidate, unless the proposal
   explicitly sets `proposal.behavior_change = true` and lists removed codes
   in `proposal.removed_family_codes`.
3. **Recall floor on external sample**: candidate
   `external.rules.recall` must be >= `baseline.external.rules.recall - 0.02`.
4. **Demo recall floor**: candidate `rules.recall_at_top_k(K=3)` must be
   >= `baseline.rules.recall_at_top_k(K=3) - 0.02`.
5. **Determinism**: the experiment driver runs the demo eval twice; scores
   must match byte-for-byte.
6. **Threshold ordering**: `thresholds.medium <= thresholds.high <= thresholds.critical`.
7. **No regex blow-up**: the experiment driver imposes a soft per-family limit
   of `200` patterns and rejects ontologies that exceed it.

A candidate that satisfies all guardrails **and** beats baseline F1 (per §1)
is marked `decision = "kept"`. A candidate that satisfies guardrails but does
not improve F1 is `decision = "discarded_no_improvement"`. A candidate that
fails any guardrail is `decision = "discarded_guardrail"` with a `reason`
field.

Kept candidates are **not** automatically promoted into the live triage
engine. Promotion is a separate human action (`make autoresearch-promote
RUN=<id>` or the admin-only API endpoint).

---

## 4. Proposal contract

When invoked, the external agent CLI must:

1. Read this file and the current baseline at
   `autoresearch/baseline/pancreatic_signal_rules.json`.
2. Read the latest run summaries under `autoresearch/runs/` to avoid
   re-proposing identical changes.
3. Write its candidate ontology to the path supplied by the orchestrator via
   `--out-ontology` (the loop creates a fresh `runs/<ts>/proposal.json`).
4. Write a short rationale to the path supplied via `--out-notes`
   (`runs/<ts>/notes.md`). The rationale should explain which patterns were
   added/removed and why, in terms a clinician reviewer can follow.
5. Optionally write a metadata blob to `--out-meta`
   (`runs/<ts>/proposal_meta.json`) with the keys:
   - `behavior_change`: `bool`
   - `removed_family_codes`: `[str]`
   - `intent`: free-form string (e.g. `"reduce false positives on chronic pancreatitis"`)

The agent **must exit non-zero** if it cannot produce a valid candidate.
The orchestrator treats non-zero exit as `decision = "agent_failed"`.

---

## 5. Operating points

The experiment driver evaluates at the same operating points as the published
proof surface:

- Demo benchmark: `threshold = 0.3`, `top_k = 3`.
- External retrospective sample: `threshold = 0.3`, `top_k = 5`.

The agent should not assume any other operating point will be evaluated. If
calibration at a different threshold is desired, that is out of scope for
v2.0 and should be raised as a `notes.md` recommendation, not as a tuning
target.

---

## 6. Out of scope (v2.0)

- Editing Python source (deferred to v2.2).
- Editing `apps/api/app/services/evaluation.py` or any benchmark fixture.
- Adding new datasets. Use the existing demo dataset, retrospective sample,
  and wording-variance sample.
- Hybrid-mode tuning. The hybrid layer is reported for visibility only.
- Hosted continuous autoresearch. The loop is run by humans, locally or
  overnight on a workstation.

---

## 7. Operating notes for human research operators

- Edit this file to redirect the agent (e.g., raise the recall floor, switch
  the primary metric to `precision_at_top_k`). The schema and driver still
  enforce the rule-only edit surface.
- Inspect `autoresearch/runs/<id>/diff.json` before promoting. The
  `families[]` diff is computed against the frozen baseline, not against the
  current live ontology, so reviewers can always see the cumulative drift.
- `make autoresearch-rollback` restores `data/ontologies/pancreatic_signal_rules.json`
  from `autoresearch/baseline/`. Use this any time the live triage engine
  starts behaving unexpectedly after a promotion.
