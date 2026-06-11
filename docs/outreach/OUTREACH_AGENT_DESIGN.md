# Outreach Agent Design

Maintainer tooling design for a human-gated agent that helps find and contact educators, researchers, and clinical-informatics professionals who might use Pancreatic Signal or want a feature from it.

This document is intentionally public: the process it describes is consent-respecting and human-reviewed, and anyone contacted should be able to read exactly how the outreach works.

> **Hard rule:** prospect lists, contact details, conversation logs, and any other personal data live in a separate **private** workspace, never in this repository.

## 1. Goals and non-goals

**Goals**

- Find people whose public work suggests Pancreatic Signal is genuinely relevant to them
- Send a small number of individually relevant, honest messages
- Route interest into durable public funnels (use-case interest issues, Discussions)
- Learn which audiences and value propositions resonate, to guide the roadmap

**Non-goals**

- Mass email. Volume is capped by design (see §6)
- Fully autonomous sending. A human approves every message before it leaves
- Growth hacking, engagement bait, or anything that would embarrass the project if quoted publicly

## 2. Guardrails (non-negotiable)

1. **Claims compliance.** Every draft inherits [SAFETY_AND_COMPLIANCE.md](../SAFETY_AND_COMPLIANCE.md) verbatim in the drafting prompt. The agent must never describe the project as detecting or diagnosing cancer, being clinically validated, or replacing radiologist review. Banned-phrase linting runs on every draft before it reaches the review queue.
2. **Human approval per message.** The agent drafts; the maintainer reads, edits, and sends. No auto-send in any phase currently planned.
3. **Consent and law.** Outreach must satisfy the strictest plausible regime among CAN-SPAM, CASL, and GDPR: truthful sender identity, a working unsubscribe/opt-out path, immediate and permanent suppression on request, and a lawful basis (legitimate interest in individualized professional correspondence about their published work — which means every message must actually be individualized).
4. **Sourcing limits.** Contact details come only from places where the person chose to publish them professionally (paper correspondence addresses, faculty pages, GitHub profiles, conference bios). No purchased lists, no scraped bulk databases, no guessing email patterns.
5. **One follow-up maximum**, no sooner than 10 days, then permanent suppression. Any reply that isn't an explicit yes is treated as opt-out.
6. **Transparency on request.** If anyone asks whether tooling was involved, the answer is yes and this document is the reference.

## 3. Audience segments and hooks

| Segment | Hook | One-pager | Primary ask |
|---|---|---|---|
| Researchers (clinical NLP, pancreatic cancer, cancer surveillance) | Reproducible explainable-triage benchmark + citable artifact | [FOR_RESEARCHERS.md](FOR_RESEARCHERS.md) | Try the benchmark on a retrospective dataset; tell us what's missing |
| Educators (health informatics, clinical NLP, biomedical data science) | Complete synthetic-data teaching stack; lab-module ideas included | [FOR_EDUCATORS.md](FOR_EDUCATORS.md) | Pilot a course module; request module-sized features |
| Informatics / interoperability professionals | Working FHIR + HL7 import sandbox with audit-grade run records | [FOR_INFORMATICS_PROFESSIONALS.md](FOR_INFORMATICS_PROFESSIONALS.md) | Evaluate the adapters; file interop gaps |

## 4. Pipeline architecture

```
discover → qualify → draft → human review → send (manual) → track → learn
```

**Discover.** Weekly agent run over public sources: Europe PMC / PubMed queries (pancreatic cancer NLP, radiology report NLP, incidental findings surveillance), GitHub activity on adjacent topics (clinical-nlp, fhir, radiology), university course pages that publish health-informatics syllabi, recent conference programs (AMIA, MedInfo, SIIM). Output: candidate records with a *relevance rationale* — one sentence on why this specific person plausibly cares, citing their specific work. No rationale, no candidate.

**Qualify.** The maintainer skims candidates and marks accept/reject. Rejected sources of repeated noise get added to discovery exclusions.

**Draft.** For accepted candidates the agent produces a ≤150-word email: one sentence referencing their specific public work (the genuine reason for contact), one sentence on the matching hook, a link to the relevant one-pager and repo, one concrete low-friction ask, and an explicit "tell me to stop and I won't write again" line. System prompt = segment template + SAFETY_AND_COMPLIANCE constraints + banned-phrase list.

**Review queue.** Drafts land as files in the private workspace (`queue/<candidate-id>.md` with frontmatter: name, segment, source-of-contact URL, rationale). Maintainer edits or deletes, then sends manually from their own email account. Sending manually keeps a human legally and practically the sender of record.

**Track.** A single ledger (private spreadsheet or JSONL): candidate, segment, date contacted, response status (none / opt-out / reply / interested / converted), follow-up date if any. Suppression list is permanent and checked at discovery time, so suppressed people never even re-enter the pipeline.

**Learn.** Monthly: response and conversion rates by segment and hook; feed conclusions into the roadmap and revise the one-pagers.

## 5. Reply funnels (must exist before the first message)

- **Use-case interest issue template** — `.github/ISSUE_TEMPLATE/use_case_interest.yml` (done)
- **GitHub Discussions** with a "Use cases & interest" category (enable category after going public)
- **Maintainer email** for people who won't use GitHub — whatever address the maintainer sends from
- Optional later: a scheduling link for "yes, let's talk" replies

## 6. Phases and caps

| Phase | Scope | Cap | Exit criterion |
|---|---|---|---|
| 0 — Pilot | 10–15 hand-picked candidates the maintainer already half-knows of; agent only drafts | n/a | ≥3 replies and message tone validated |
| 1 — Assisted | Agent discovers and drafts; maintainer qualifies and sends | ≤10 sends/week | Funnel and tracking proven over ~6 weeks |
| 2 — Steady state | Same as phase 1, more sources | ≤20 sends/week | Ongoing; revisit quarterly |

Auto-sending is out of scope for all phases and would require its own legal review before being reconsidered.

## 7. Implementation sketch

Private repo `pancreatic-signal-outreach` (never public):

```
outreach/
├── config/
│   ├── segments.yaml          # hooks, templates, banned phrases per segment
│   └── sources.yaml           # discovery queries and exclusions
├── pipeline/
│   ├── discover.py            # Europe PMC / GitHub / web queries → candidates.jsonl
│   ├── draft.py               # Claude API drafting with guardrail prompt
│   └── lint_claims.py         # banned-phrase + claims check, blocks queue entry
├── queue/                     # drafts awaiting human review (gitignored)
├── ledger.jsonl               # contact + outcome tracking (gitignored)
└── suppression.txt            # permanent opt-out list (gitignored, backed up)
```

- Drafting model: current Claude model via the API; temperature low; the draft prompt includes the candidate's cited work snippet, segment template, and the full guardrail block
- `lint_claims.py` is deterministic (regex + phrase list), mirroring how this project prefers explainable gates over model judgment
- Discovery reuses patterns from `apps/api/app/services/research_intel_connectors.py` (Europe PMC querying already exists there)

## 8. Metrics that matter

- Replies per 10 sends (target: ≥2 in phase 1 — if lower, the targeting or message is wrong; stop and revise rather than send more)
- Use-case issues or Discussions opened by contacted people
- Feature requests traceable to outreach (label them `via-outreach`)
- Opt-out rate (>10% means stop and rethink)

## 9. What blocks the first send today

1. Repo must be public (links in messages must work)
2. v0.10.0 release tagged so the repo looks finished on arrival
3. Discussions "Use cases & interest" category created
4. A handful of seeded `good first issue` items
5. Maintainer decides the send-from email address
6. Phase-0 candidate shortlist (maintainer-picked)
