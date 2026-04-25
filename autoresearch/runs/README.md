# Autoresearch run log

Each subdirectory under `autoresearch/runs/` represents a single experiment
iteration emitted by `scripts/run_autoresearch_experiment.py` (invoked
directly via `make autoresearch-once` or indirectly by
`scripts/run_autoresearch_loop.py`).

The directory naming convention is the ISO-8601 UTC timestamp of the run
start, e.g. `2026-04-25T14-22-09Z`. Each run directory contains:

| File                  | Purpose                                                                |
|-----------------------|------------------------------------------------------------------------|
| `proposal.json`       | Candidate ontology JSON proposed by the agent (or human).              |
| `proposal_meta.json`  | Optional agent-supplied metadata (intent, behavior_change, etc.).      |
| `notes.md`            | Optional reviewer-readable rationale written by the agent.             |
| `diff.json`           | Structured diff of the candidate vs. the frozen baseline ontology.     |
| `eval.json`           | Evaluation snapshot (rules + hybrid demo, external sample).            |
| `decision.json`       | `kept`, `discarded_*`, or `agent_failed`, with guardrail outcomes.     |
| `promotion.json`      | Written only when the run is promoted via `make autoresearch-promote`. |

This directory is **append-only**. Existing runs must not be rewritten so
that the leaderboard surfaced by the API and frontend is reproducible.
