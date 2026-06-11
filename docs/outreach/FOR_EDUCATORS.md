# Pancreatic Signal For Educators

A complete, safe-to-teach-with clinical informatics codebase: explainable clinical NLP, healthcare interoperability, and human-in-the-loop review workflow — all on synthetic data.

> Research-use workflow software. All bundled data is synthetic; nothing in the repo touches real patients.

## Why it works in a classroom

- **No PHI, no IRB friction.** Every report, case, and benchmark in the repo is synthetic. Students can run the full stack locally with Docker or plain Python/Node.
- **Explainability is inspectable, not claimed.** The triage engine is a deterministic rule system in one JSON file (`data/ontologies/pancreatic_signal_rules.json`) — students can read every pattern, negation rule, and score weight, change them, and watch evidence-highlighted results change.
- **Real interoperability surface.** Working FHIR `DiagnosticReport` and HL7 v2 ORU import paths with persisted audit records — concrete material for health-data-standards courses, including realistic failure buckets (parse errors, unsupported payloads, site-scope rejections).
- **Evaluation as a first-class topic.** Precision/recall/top-k benchmarking with stable error buckets (negation failure, wording variance, confounders) makes a ready-made lab on why clinical NLP evaluation is hard.
- **Safety posture worth teaching.** The repo models how research software should bound its claims: human-review-required workflow, non-clinical framing, documented limitations ([SAFETY_AND_COMPLIANCE.md](../SAFETY_AND_COMPLIANCE.md)).

## Course-module ideas

1. **Clinical NLP lab:** students extend the rule ontology to catch a wording variant, then measure the benchmark delta.
2. **Interoperability lab:** students craft FHIR and HL7 payloads, import them, and trace the audit trail.
3. **Human-factors discussion:** review the worklist UI and debate what reviewers need to trust a flag.
4. **Software engineering case study:** a tested, CI-gated, documented open-source repo students can submit real PRs to.

## Get started

```bash
git clone https://github.com/alex-varga14/pancreatic-signal
cd pancreatic-signal
docker compose up --build   # full stack at localhost:3000
```

Teaching with it, or want a module-sized artifact that doesn't exist yet? Open a [use-case interest issue](https://github.com/alex-varga14/pancreatic-signal/issues/new/choose) — curriculum-driven feature requests are welcome.
