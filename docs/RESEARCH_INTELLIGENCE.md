# Research Intelligence

Pancreatic Signal now has a second primary pillar beside explainable radiology triage: a cited pancreatic oncology watchtower for documents, digests, opportunities, and case-facing research briefs.

Execution companion:

- [RESEARCH_INTELLIGENCE_EXECUTION_PLAN.md](./RESEARCH_INTELLIGENCE_EXECUTION_PLAN.md)

## Purpose

Research Intelligence exists to:

- organize pancreatic oncology signals from literature, trials, guidance, regulatory updates, and open-source activity
- turn those signals into durable artifacts instead of one-off chat output
- help contributors spot benchmark gaps, rule gaps, trial-catalog updates, and tooling opportunities
- inform case review with cited research briefs without changing case scores automatically

## What Ships Today

The current implementation includes:

- a new API namespace at `/api/v1/research-intel/*`
- a new web workspace at `/research-intel`
- seeded catalogs in `data/research/` for sources, topics, a lightweight graph, and sample documents
- persisted records for sources, runs, run items, documents, evidence, topics, digests, and opportunities
- manual ingest and digest scripts plus Make targets
- digest artifacts written under `artifacts/research-intel/`
- case-level research briefs linked from the existing case detail page
- discovery-ingest source health, document provenance, and novelty scoring
- fixture-backed connector feeds for reproducible validation plus opt-in live connector scaffolding
- graph-backed entity resolution plus a `/research-intel/graph` workspace for active node and edge inspection

Current status:

- the first slice is manual-triggered and now supports discovery-ingest modes
- public read endpoints are open for OSS exploration
- run execution and opportunity promotion require authenticated operator roles

## Local Workflow

Seed the watchtower and generate a digest:

```bash
make research-intel-refresh
```

Or run the two phases independently:

```bash
make research-intel-ingest
make research-intel-digest
```

For the reproducible discovery-ingest path:

```bash
make research-intel-discovery-fixture
```

For opt-in live connector attempts on supported sources:

```bash
make research-intel-discovery-live
```

Then explore:

- `/research-intel` for dashboard and run health
- `/research-intel/documents` for normalized documents, citations, and topic tags
- `/research-intel/graph` for graph entities, edges, and active node heat
- `/research-intel/digests` for council-backed digest output
- `/research-intel/opportunities` for human-gated contribution proposals

## Pipeline

The current workflow follows five explicit phases.

### 1. Collect

- load the source catalog from `data/research/sources.json`
- select fixture-backed or live-discovery pancreatic oncology documents
- normalize identifiers and source metadata
- track connector mode, source health, and provenance

### 2. Structure

- map documents onto topic watchlists from `data/research/topics.json`
- extract cited evidence spans and claim text
- compute lightweight relevance scores and topic heat

### 3. Deliberate

- persist stage 1 independent opinions
- persist stage 1 open questions, evidence gaps, confidence labels, and proposed opportunity types
- persist stage 2 ranking, critique, peer review, and confidence adjustments
- persist stage 3 chairman synthesis with overall confidence, next experiments, and promotion guardrails
- record disagreement instead of hiding it

### 4. Publish

- create digest records
- write JSON and Markdown artifacts under `artifacts/research-intel/`
- keep claims citation-backed

### 5. Act

- generate structured opportunities from high-signal digest output
- attach typed action specs with objectives, evidence bundles, measurable outcomes, and downstream artifact hints
- support human-gated promotion into docs drafts, benchmark tasks, or GitHub-issue style artifacts

## Seeded Catalogs

The first foundation slice ships with:

- `6` source definitions
- `7` topic watchlists
- `7` lightweight graph nodes
- `7` seeded pancreatic oncology documents
- `6` discovery fixture feeds for reproducible connector runs

Those assets establish the domain model and the reproducible discovery-ingest path before broader live source polling is turned on.

## Phase 1 Discovery Status

Phase 1 is now in progress with these capabilities:

- fixture-backed connector ingestion is available through `auto` and `fixture` modes
- source health is persisted in the source registry state
- document provenance and novelty are stored and exposed through the API
- opt-in live connector code paths exist for Europe PMC and ClinicalTrials.gov, while the remaining sources stay fixture-backed until their live contracts are hardened

## Phase 2 Knowledge Graph Status

Phase 2 is now underway with these capabilities:

- the pancreatic oncology graph now includes typed entities for disease, biomarkers, procedures, cohorts, workflow concepts, and research artifacts
- graph-backed entity resolution runs during document normalization
- graph entities now help reinforce topic assignment and evidence extraction
- a dedicated graph surface exposes active nodes, edge relationships, and document-backed entity heat

## Phase 3 Council Status

Phase 3 is now underway with these capabilities:

- stage 1 opinions now carry primary topics, confidence labels, key claims, open questions, and evidence gaps
- stage 2 rankings now include explicit peer critiques, challenge targets, preferred actions, and confidence adjustments
- stage 3 synthesis now records overall confidence, evidence gaps, open questions, next experiments, and promotion guardrails
- persisted council payloads remain backward-compatible with older digest versions

## Phase 4 Discovery-To-Action Status

Phase 4 is now underway with these capabilities:

- opportunities now persist typed action payloads instead of loose promotion hints
- each opportunity carries a discovery objective, why-now rationale, discovery question, and measurable outcomes
- each opportunity also carries a cited evidence bundle, open questions, evidence gaps, next experiments, and promotion guardrails
- digest runs now write contributor-ready opportunity JSON and Markdown artifacts under `artifacts/research-intel/opportunities/`
- promotion artifacts now preserve the same structured discovery-to-action context instead of collapsing into shallow summaries

## Opportunity Types

The current opportunity taxonomy is fixed and explicit:

- `rule_gap`
- `benchmark_gap`
- `trial_catalog_gap`
- `case_brief`
- `community_project`
- `external_tooling`

## Triage Integration Boundary

Research Intelligence informs the existing triage product in three ways only:

- case briefs that connect case rationale or trial context to current topics and cited documents
- benchmark growth ideas such as wording variance, confounders, and follow-up patterns
- rule and trial-catalog proposals that still require human review plus tests before merge

It does not:

- rewrite case scores
- auto-close or re-prioritize cases in reviewer workflow
- act as autonomous diagnosis or treatment guidance

## Design Influences

The implementation direction borrows selectively from several open-source research-agent ideas while staying grounded in this repository's explainability and audit requirements.

- `SciAgentsDiscovery`: graph-seeded discovery and domain-aware expansion shaped the lightweight pancreatic ontology and topic graph
- `AgentLaboratory`: phased collect-to-publish workflow shaped the durable artifact pipeline
- `llm-council`: independent opinion, ranking, and chairman synthesis shaped the council payload
- `Kosmos`: validation-first and sandbox-oriented thinking shaped the artifact and experiment boundaries
- `autoresearch`: ratchet-style improvement shaped the expectation that proposals should become measurable benchmark or rule work
- `quantum-agentics` and the `openclaw` standby-agent idea: influenced the future operating model for schedulers and named agents without introducing those runtime dependencies today

## Guardrails

- research-use software only
- cited outputs over uncited synthesis
- human-gated promotion over autonomous action
- no autonomous payment, subscription procurement, or crypto treasury execution in the current product
- no automatic mutation of triage scores or reviewer state

## Next Slices

- add live curated connectors on top of the seeded catalog
- turn council deliberation into stronger multi-run comparison and calibration
- deepen opportunity promotion into issue-ready and benchmark-ready contributor workflows
- add sandboxed benchmark and rule experiment runners for promoted opportunities
- document donation governance and paid-source procurement policy before any funding automation is considered
