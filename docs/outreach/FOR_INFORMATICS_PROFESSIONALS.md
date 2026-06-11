# Pancreatic Signal For Clinical Informatics And Interoperability Professionals

An open-source sandbox for report-pipeline integration patterns: FHIR and HL7 ingestion, audit-grade import runs, site-scoped access, and explainable downstream triage — deployable locally in minutes.

> Research-use workflow software for evaluation, demonstration, and pilot-style exploration under your institution's governance. Not a production clinical system and not regulatory-cleared.

## What's implemented (not planned — implemented)

- **FHIR `DiagnosticReport` ingestion** including inline `Reference.identifier` metadata preservation and text-like `presentedForm` attachment decoding (plain text and XHTML narratives)
- **HL7 v2 ORU ingestion** with base64 `ED` decode, custom `MSH-2` separator handling, escape-sequence normalization, repeated `OBX-5` merging, and subcomponent-aware metadata extraction
- **CSV / JSON / JSONL report imports** for simpler feeds
- **Persisted import-run audit records** with stable failure buckets (`parse_error`, `unsupported_payload`, `validation_error`, `site_scope_rejection`) and cross-actor visibility rules you can verify yourself
- **Pluggable pilot auth modes:** mock auth for local work, trusted-proxy and header-based identity forwarding overlays for controlled demo environments
- **A smoke matrix that proves it:** ~25 make targets covering success, failure, shared-visibility, and site-rejection paths against real built images, plus hosted CI smoke runs

## Why evaluate it

- Every import outcome is auditable: who imported, what failed, which bucket, what's visible to whom
- Deterministic triage downstream means integration testing has stable expected outputs
- Apache-2.0 — adapt the adapters, keep your changes, or contribute them back
- Honest boundary-setting: docs distinguish what's automated, what's manual, and what's out of scope

## Get started

```bash
git clone https://github.com/alex-varga14/pancreatic-signal
cd pancreatic-signal
make pilot-proxy-demo-up && make pilot-proxy-demo-fhir-smoke
```

Full overlay and smoke matrix: [DEPLOYMENT.md](../DEPLOYMENT.md). Interop gaps you'd need filled (other resource types, other HL7 segments, IHE profiles)? Open a [use-case interest issue](https://github.com/alex-varga14/pancreatic-signal/issues/new/choose).
