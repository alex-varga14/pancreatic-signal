# Research Intelligence Governance

This document defines the operating boundary for paid-source access, donation-funded operations, and source procurement in the research-intel watchtower.

## Purpose

Research Intelligence is meant to stay open, cited, and human-auditable even as it grows into a standing pancreatic oncology discovery system. That means source access, spending, and promotion decisions must stay reviewable and policy-bound.

## Current Policy

- public and openly accessible sources are the default
- registration-gated or institution-gated sources may be modeled in metadata, but access still requires human approval
- no autonomous payment, crypto treasury execution, subscription purchase, or procurement workflow is implemented in product code
- donations may fund source access or infrastructure only through explicit human-operated decisions
- every promoted artifact must remain citation-backed even when some upstream sources are paid or restricted

## Source Access Classes

Use these classes when onboarding or reviewing a source:

1. `public_open`
   No account or payment required. Safe default for the watchtower.
2. `registration_required`
   Human-created account required, but no paid procurement.
3. `paid_subscription`
   Requires explicit budget approval and named human owner.
4. `institution_restricted`
   Access depends on institutional agreement, license, or reviewer affiliation.

## Procurement Rules

- a source may be proposed by the watchtower, but never purchased by it
- paid-source proposals must include expected value, trust level, access class, and fallback public alternatives
- procurement decisions require a human maintainer to approve, record the source owner, and document renewal expectations
- if a paid source expires or becomes unavailable, the watchtower should degrade gracefully rather than silently switching to uncited synthesis

## Donation Rules

- donations fund infrastructure, source access, and contributor operations only through human review
- no automated wallet execution, smart-contract spending, or subscription renewal is in scope
- if donations are used for a source, the repo should document what capability that source unlocks and what public fallback exists
- governance notes should be updated before any recurring financial commitment is introduced

## Promotion Rules

- paid or restricted sources do not lower the citation bar
- promotion remains human-gated even when confidence is high
- any downstream benchmark, rule, or trial artifact must be reproducible without exposing restricted source text
- when a restricted source motivates follow-up work, the promoted artifact should capture the public summary, open question, and measurable next step without leaking licensed content

## Run And Audit Expectations

- source metadata should record access class and funding need when relevant
- run artifacts should record which source ids were used, but not embed restricted text beyond allowed metadata
- contributor packets should note when a proposal depends on access the broader community may not have

## Future Work

- add explicit funding-need metadata to source records
- add operator-visible governance summaries in the web workspace if paid sources are introduced
- publish a lightweight public governance note alongside any donation-supported source expansion
