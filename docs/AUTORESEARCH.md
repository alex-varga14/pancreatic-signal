# Autoresearch (opt-in lab subsystem)

> Pancreatic Signal v2 introduces an opt-in autonomous research subsystem
> inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch).
> The product itself — triage, imports, and the worklist — remains the primary
> surface and is not affected by autoresearch unless a human explicitly
> promotes a candidate ontology.

## Why this exists

The deterministic triage engine is rule-driven. Most of the day-to-day
"research" work — proposing new patterns, retiring noisy ones, tuning weights
and thresholds — is mechanical and bounded. Autoresearch automates that loop
while keeping a hard wall around what the agent is allowed to touch.

In one sentence: **an external coding agent edits one JSON file, a fixed
evaluator scores it, and a human decides whether to promote it.**

## Three-file mental model

| karpathy/autoresearch         | pancreatic-signal                                                |
|-------------------------------|------------------------------------------------------------------|
| `program.md` (research org)   | [`autoresearch/program.md`](../autoresearch/program.md)          |
| `train.py` (the file edited)  | [`data/ontologies/pancreatic_signal_rules.json`](../data/ontologies/pancreatic_signal_rules.json) |
| `prepare.py` (fixed pipeline) | [`apps/api/app/services/evaluation.py`](../apps/api/app/services/evaluation.py) |
| `val_bpb` (primary metric)    | `f1_at_top_k` on the demo benchmark                              |

The agent reads `program.md` and the frozen baseline ontology, proposes a new
ontology, and exits. The deterministic experiment driver does everything else.

## The loop

```
human edits autoresearch/program.md
        │
        ▼
scripts/run_autoresearch_loop.py (orchestrator)
        │
        ├──► invokes external agent CLI (Cursor / Claude Code / Codex CLI)
        │       │
        │       ▼
        │    candidate proposal.json
        │
        ▼
scripts/run_autoresearch_experiment.py (driver)
        │
        ├── schema validation
        ├── diff vs. frozen baseline
        ├── demo eval (rules + hybrid)
        ├── external sample snapshot lookup
        ├── determinism check
        └── guardrails
                │
                ▼
        autoresearch/runs/<ts>/
          ├── proposal.json
          ├── proposal_meta.json (optional)
          ├── notes.md (optional)
          ├── diff.json
          ├── eval.json
          └── decision.json   <- "kept" | "discarded_no_improvement"
                                  | "discarded_guardrail" | "agent_failed"
        │
        ▼
human runs `make autoresearch-promote RUN=<id>`
        │
        ▼
data/ontologies/pancreatic_signal_rules.json (live)
```

The run log under `autoresearch/runs/` is **append-only**. Nothing in the
loop deletes or rewrites past iterations. That makes every change to the live
ontology fully auditable: each promotion has a corresponding `runs/<id>/`
folder with the exact proposal, diff, eval, and decision that justified it.

## What the agent is allowed to edit

`autoresearch/program.md` §2 is authoritative. In short:

- The agent edits exactly one file: `data/ontologies/pancreatic_signal_rules.json`.
- It may add, remove, or rewrite **patterns**, families, negations, and
  uncertainty markers, and adjust weights and thresholds within `[0, 1]`.
- It may not modify Python source, schemas, the evaluation pipeline, the
  imports adapters, or the database. The schema is `extra="forbid"`, so any
  drift in JSON shape is rejected before the candidate is ever scored.

If a proposal touches any other path the orchestrator records `decision = "off_surface"`
and the candidate is discarded.

## Primary metric and guardrails

The primary metric is `f1_at_top_k(K=3, threshold=0.3)` on the bundled demo
benchmark in rules score mode. A candidate is **kept** iff:

1. F1 strictly improves vs. the frozen baseline.
2. `recall_at_top_k(K=3)` does not regress on the demo benchmark.
3. External retrospective sample recall does not drop more than `0.02` absolute.
4. All guardrails in `autoresearch/program.md` §3 pass:
   - schema validation (`OntologyConfig.model_validate`),
   - no silent rationale code deletion (must opt in via `behavior_change`),
   - threshold ordering (`medium <= high <= critical`),
   - per-family pattern budget (≤ 200 by default),
   - byte-identical determinism check (eval run twice, scores must match).

A "kept" candidate is **not** automatically promoted. Promotion is always a
separate human action.

## Plugging in a coding agent

The orchestrator invokes any CLI that obeys the proposal contract in
`program.md` §4. The CLI gets four arguments:

```
$AGENT_CMD \
  --program autoresearch/program.md \
  --baseline autoresearch/baseline/pancreatic_signal_rules.json \
  --runs-root autoresearch/runs \
  --out-ontology autoresearch/runs/<ts>/proposal.json \
  --out-meta autoresearch/runs/<ts>/proposal_meta.json \
  --out-notes autoresearch/runs/<ts>/notes.md
```

You can wire this to any of:

- **Cursor CLI / Background Agent** — point `AGENT_CMD` at a small wrapper
  script that opens the project in Cursor and lets the agent edit
  `proposal.json` directly.
- **Claude Code CLI** — wrapper that passes `program.md` and the baseline as
  context and asks Claude to write the candidate ontology to the supplied path.
- **Codex / OpenAI CLI** — same shape, different binary.
- **Manual edits** — skip `make autoresearch-loop` entirely and use
  `make autoresearch-once CANDIDATE=path/to/edited_rules.json` to evaluate a
  hand-edited ontology against the same guardrails.

Make targets:

```bash
make autoresearch-once CANDIDATE=path/to/candidate.json   # one experiment, no agent
make autoresearch-loop ITERATIONS=5 AGENT_CMD="my-agent"  # N iterations
make autoresearch-promote RUN=<run-id>                    # human gates promotion
make autoresearch-rollback                                # restore baseline
```

## Reading the run log

Each `autoresearch/runs/<id>/` folder contains:

| File                  | Purpose                                                                 |
|-----------------------|-------------------------------------------------------------------------|
| `proposal.json`       | Exact ontology JSON the agent produced.                                |
| `proposal_meta.json`  | Optional agent-supplied metadata: `behavior_change`, `intent`, etc.    |
| `notes.md`            | Optional clinician-readable rationale for the change.                  |
| `diff.json`           | Structured diff vs. the frozen baseline (added/removed families, weight changes). |
| `eval.json`           | Demo benchmark rules+hybrid scores, external sample snapshot, determinism check. |
| `decision.json`       | Final keep/discard verdict, primary metric values, guardrail results.  |
| `promotion.json`      | Present only if the run was later promoted by a human.                 |

The same data is also exposed read-only at `/api/v1/autoresearch/runs` and
visualized at `/autoresearch` in the web app, with diff and evaluation
viewers and a capability-gated promote button.

## Promotion and rollback

Promotion is a copy from `autoresearch/runs/<id>/proposal.json` to
`data/ontologies/pancreatic_signal_rules.json`, plus a `promotion.json`
provenance record written next to the proposal and an audit log entry. The
promote endpoint requires the `admin` role (see
`docs/SAFETY_AND_COMPLIANCE.md`).

`make autoresearch-rollback` restores the live ontology from
`autoresearch/baseline/pancreatic_signal_rules.json`. Use it any time the
live triage engine starts behaving unexpectedly after a promotion.

## What is *not* autoresearch

- **The triage engine is not autonomous.** Triage uses whatever
  `data/ontologies/pancreatic_signal_rules.json` says today. If no human ever
  promotes a candidate, the engine never changes.
- **Imports, the worklist, the API, and reviewer feedback** are not part of
  autoresearch. They are the primary product surfaces and are unaffected.
- **There is no hosted, always-on autoresearch in v2.0.** The loop is run by
  humans, locally or overnight on a workstation. Hosted CI orchestration is
  explicitly out of scope.

## Out of scope for v2.0

- The agent editing Python source (deferred to v2.2).
- Editing the evaluation pipeline or benchmark fixtures.
- Adding new benchmark datasets.
- Hybrid-mode tuning (the hybrid layer is reported for visibility only).
- Continuous CI autoresearch.
