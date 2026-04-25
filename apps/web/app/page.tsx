import Link from "next/link";
import {
  getDemoBenchmarkSnapshot,
  getPublishedExternalBenchmarkEntries,
  PUBLISHED_DEMO_PROOF_PATH,
  PUBLISHED_EXTERNAL_BENCHMARK_REGISTRY_PATH,
} from "../lib/demo-proof";
import styles from "./marketing.module.css";

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatDelta(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${Math.round(value * 100)} pts`;
}

function formatGeneratedAt(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default async function HomePage() {
  const demoProof = await getDemoBenchmarkSnapshot();
  const externalBenchmarkEntries = await getPublishedExternalBenchmarkEntries();
  const configuredExternalBenchmarkEntries = externalBenchmarkEntries.length;
  const availableExternalBenchmarkEntries = externalBenchmarkEntries.filter((entry) => entry.snapshot !== null);
  const missingExternalBenchmarkEntries =
    configuredExternalBenchmarkEntries - availableExternalBenchmarkEntries.length;
  const primaryExternalEntry = availableExternalBenchmarkEntries[0] ?? null;
  const primaryExternalProof = primaryExternalEntry?.snapshot ?? null;
  const datasetSummary = demoProof?.dataset_summary ?? null;
  const comparison = demoProof?.comparison ?? null;
  const sweep = demoProof?.sweep ?? null;
  const externalSummary = primaryExternalProof?.dataset_summary ?? null;
  const externalEvaluation = primaryExternalProof?.evaluation ?? null;

  return (
    <main className={styles.page}>
      <div className={styles.shell}>
        <section className={styles.hero}>
          <p className={styles.eyebrow}>Open Pancreatic Oncology Discovery System</p>
          <h1 className={styles.title}>Turn pancreatic oncology signals into cited, actionable work.</h1>
          <p className={styles.subtitle}>
            Pancreatic Signal is an open-source research-intelligence platform for pancreatic oncology. It organizes
            literature, trials, guidance, and workflow gaps into cited digests, graph-backed topics, and human-gated
            opportunities, then connects that discovery loop to applied surfaces like explainable report triage, benchmark
            growth, and case briefs.
          </p>

          <div className={styles.chipRow}>
            <span className={styles.chip}>Cited discovery engine</span>
            <span className={styles.chip}>Human-gated opportunity lab</span>
            <span className={styles.chip}>Explainable triage surface</span>
            <span className={styles.chip}>Benchmark and casebook proof</span>
            <span className={styles.chip}>CSV, JSONL, FHIR, and HL7</span>
          </div>

          <div className={styles.ctaRow}>
            <Link href="/research-intel" className={styles.primaryLink}>
              Open Research Intelligence
            </Link>
            <Link href="/proof" className={styles.secondaryLink}>
              Open Benchmark Proof
            </Link>
            <Link href="/cases" className={styles.secondaryLink}>
              Open Triage Surface
            </Link>
            <Link href="/imports" className={styles.secondaryLink}>
              Open Import Workspace
            </Link>
            <Link href="/about" className={styles.ghostLink}>
              Read The Boundaries
            </Link>
          </div>

          {comparison && sweep && datasetSummary ? (
            <div className={styles.heroProof}>
              <p className={styles.heroProofLabel}>Current Applied-Surface Proof</p>
              <p className={styles.heroProofMetric}>
                Demo snapshot: rules recall <strong>{formatPercent(comparison.rules.recall)}</strong>, hybrid recall{" "}
                <strong>{formatPercent(comparison.hybrid.recall)}</strong>, with a hybrid recall lift of{" "}
                <strong>{formatDelta(comparison.recall_delta)}</strong>.
              </p>
              <p className={styles.heroProofMetric}>
                Demo thresholds: rules <strong>{sweep.rules_recommendation.recommended_threshold.toFixed(2)}</strong> and hybrid{" "}
                <strong>{sweep.hybrid_recommendation.recommended_threshold.toFixed(2)}</strong>.
              </p>
              <p className={styles.heroProofMetric}>
                Demo casebook covers <strong>{datasetSummary.report_count}</strong> labeled reports across{" "}
                <strong>{datasetSummary.bucket_counts.length}</strong> benchmark buckets.
              </p>
              {externalEvaluation && externalSummary && primaryExternalEntry ? (
                <p className={styles.heroProofMetric}>
                  Published external packs: <strong>{availableExternalBenchmarkEntries.length}</strong> live from{" "}
                  <strong>{configuredExternalBenchmarkEntries}</strong> configured, with side-by-side comparison now on{" "}
                  <strong>/proof</strong>.{" "}
                  {primaryExternalEntry.descriptor.label}: external recall <strong>{formatPercent(externalEvaluation.recall)}</strong> and F1{" "}
                  <strong>{formatPercent(externalEvaluation.f1)}</strong> across{" "}
                  <strong>{externalSummary.report_count}</strong> checked-in reports in{" "}
                  <strong>{externalSummary.cohort_counts?.length ?? 0}</strong> cohorts.
                </p>
              ) : null}
              {missingExternalBenchmarkEntries > 0 ? (
                <p className={styles.heroProofMetric}>
                  Registry gaps: <strong>{missingExternalBenchmarkEntries}</strong> configured external pack
                  {missingExternalBenchmarkEntries > 1 ? "s are" : " is"} still missing checked-in snapshot artifacts.
                </p>
              ) : null}
              <p className={styles.heroProofMetric}>
                Published proof sources: <span className={styles.inlineCode}>{PUBLISHED_DEMO_PROOF_PATH}</span> and the
                external registry <span className={styles.inlineCode}>{PUBLISHED_EXTERNAL_BENCHMARK_REGISTRY_PATH}</span>.
              </p>
            </div>
          ) : null}
        </section>

        {comparison && sweep ? (
          <section className={`${styles.section} ${styles.grid} ${styles.gridFour}`}>
            <article className={styles.card}>
              <p className={styles.statLabel}>Rules Recall</p>
              <p className={styles.statValue}>{formatPercent(comparison.rules.recall)}</p>
              <p className={styles.statNote}>Deterministic baseline on the current synthetic demo dataset.</p>
            </article>
            <article className={styles.card}>
              <p className={styles.statLabel}>Hybrid Recall</p>
              <p className={styles.statValue}>{formatPercent(comparison.hybrid.recall)}</p>
              <p className={styles.statNote}>Explainable uplift without removing rationale codes or evidence spans.</p>
            </article>
            <article className={styles.card}>
              <p className={styles.statLabel}>Hybrid F1 Delta</p>
              <p className={styles.statValue}>{formatDelta(comparison.f1_delta)}</p>
              <p className={styles.statNote}>
                Newly surfaced cases: {comparison.newly_flagged_cases.join(", ") || "none"}.
              </p>
            </article>
            <article className={styles.card}>
              <p className={styles.statLabel}>Published Snapshot</p>
              <p className={styles.statValue}>{formatGeneratedAt(demoProof!.generated_at)}</p>
              <p className={styles.statNote}>Refresh with <span className={styles.inlineCode}>make refresh-demo-proof</span>.</p>
            </article>
          </section>
        ) : null}

        {externalEvaluation && externalSummary && primaryExternalEntry ? (
          <section className={`${styles.section} ${styles.grid} ${styles.gridFour}`}>
            <article className={styles.card}>
              <p className={styles.statLabel}>Registry Coverage</p>
              <p className={styles.statValue}>
                {availableExternalBenchmarkEntries.length}/{configuredExternalBenchmarkEntries}
              </p>
              <p className={styles.statNote}>
                Published external benchmark packs with checked-in snapshots versus total registry entries.
              </p>
            </article>
            <article className={styles.card}>
              <p className={styles.statLabel}>Primary Recall</p>
              <p className={styles.statValue}>{formatPercent(externalEvaluation.recall)}</p>
              <p className={styles.statNote}>{primaryExternalEntry.descriptor.label} at the current operating point.</p>
            </article>
            <article className={styles.card}>
              <p className={styles.statLabel}>Primary F1</p>
              <p className={styles.statValue}>{formatPercent(externalEvaluation.f1)}</p>
              <p className={styles.statNote}>Reviewer-facing external proof summary, not just the synthetic demo.</p>
            </article>
            <article className={styles.card}>
              <p className={styles.statLabel}>Primary Misses</p>
              <p className={styles.statValue}>{externalEvaluation.false_negatives}</p>
              <p className={styles.statNote}>Intentional misses stay visible for reviewer debate and future dataset growth.</p>
            </article>
          </section>
        ) : null}

        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <div>
              <p className={styles.eyebrow}>Why It Sticks</p>
              <h2 className={styles.sectionTitle}>A discovery engine that still ships useful workflow surfaces.</h2>
              <p className={styles.sectionText}>
                The wedge is not a vague “medical AI” claim. It is a public pancreatic oncology discovery loop that yields
                inspectable artifacts, measurable next steps, and downstream tools that stay grounded in evidence and human
                review.
              </p>
            </div>
          </div>

          <div className={`${styles.grid} ${styles.gridThree}`}>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Discovery artifacts, not just summaries</h3>
              <p className={styles.cardText}>
                Research runs become cited documents, graph activity, council deliberation, opportunity specs, and safe
                experiment artifacts that others can audit and build on.
              </p>
            </article>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Applied surfaces stay explainable</h3>
              <p className={styles.cardText}>
                Triage, case briefs, and trial upkeep remain downstream applications of the discovery engine, with evidence
                spans, rationale codes, and human review kept visible.
              </p>
            </article>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Open backlog with measurable next steps</h3>
              <p className={styles.cardText}>
                Opportunities carry cited evidence, open questions, measurable outcomes, and keep-or-discard experiment
                gates so contributors know what to test or build next.
              </p>
            </article>
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.codePanel}>
            <p className={styles.codeLabel}>Fastest First Run</p>
            <h2 className={styles.codeTitle}>Boot the discovery loop before you touch a line of code.</h2>
            <p className={styles.codeText}>
              Outside collaborators should be able to validate the stack, generate cited research artifacts, inspect the
              benchmark proof, and explore the applied workflow surfaces without a private walkthrough.
            </p>
            <pre className={styles.codeBlock}>
{`make validate-strict
make research-intel-refresh
make benchmark-demo
make benchmark-external-sample
make refresh-external-sample-proof
docker compose up --build`}
            </pre>
            <p className={styles.codeText}>
              Discovery artifacts land in <span className={styles.inlineCode}>artifacts/research-intel</span>, while
              benchmark artifacts land in <span className={styles.inlineCode}>artifacts/benchmarks</span>. The published
              proof used by this site lives at <span className={styles.inlineCode}>{PUBLISHED_DEMO_PROOF_PATH}</span> and
              the external registry <span className={styles.inlineCode}>{PUBLISHED_EXTERNAL_BENCHMARK_REGISTRY_PATH}</span>.
            </p>
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <div>
              <p className={styles.eyebrow}>Explore</p>
              <h2 className={styles.sectionTitle}>Start with the surface that matches your question.</h2>
            </div>
          </div>

          <div className={`${styles.grid} ${styles.gridFour}`}>
            <Link href="/research-intel" className={styles.card}>
              <h3 className={styles.routeCardTitle}>
                Research intelligence
                <span className={styles.inlineCode}>/research-intel</span>
              </h3>
              <p className={styles.cardText}>
                Explore the pancreatic oncology watchtower: document stream, topic heat, graph activity, digests, and the
                discovery backlog that shapes what the project does next.
              </p>
              <p className={styles.routeMeta}>Best first stop for discovery work</p>
            </Link>
            <Link href="/proof" className={styles.card}>
              <h3 className={styles.routeCardTitle}>
                Benchmark proof
                <span className={styles.inlineCode}>/proof</span>
              </h3>
              <p className={styles.cardText}>
                Review the checked-in demo comparison, compare published external benchmark packs side by side, and inspect
                the exact commands used to reproduce each proof story.
              </p>
              <p className={styles.routeMeta}>Best first stop for outside collaborators</p>
            </Link>
            <Link href="/cases" className={styles.card}>
              <h3 className={styles.routeCardTitle}>
                Explainable triage surface
                <span className={styles.inlineCode}>/cases</span>
              </h3>
              <p className={styles.cardText}>
                Inspect evidence spans, rationale codes, hybrid review signals, and the case-detail workflow used as one
                downstream application of the discovery engine.
              </p>
              <p className={styles.routeMeta}>Best for product and workflow review</p>
            </Link>
            <Link href="/imports" className={styles.card}>
              <h3 className={styles.routeCardTitle}>
                Import workspace
                <span className={styles.inlineCode}>/imports</span>
              </h3>
              <p className={styles.cardText}>
                Exercise CSV, JSONL, FHIR DiagnosticReport, and HL7 ORU paths with persisted audit records and stable failure
                buckets.
              </p>
              <p className={styles.routeMeta}>Best for interoperability review</p>
            </Link>
            <Link href="/autoresearch" className={styles.card}>
              <h3 className={styles.routeCardTitle}>
                Autoresearch lab
                <span className={styles.inlineCode}>/autoresearch</span>
              </h3>
              <p className={styles.cardText}>
                Browse the append-only run log, inspect candidate ontology diffs and evaluation snapshots, and promote kept
                candidates into the live triage rules.
              </p>
              <p className={styles.routeMeta}>Opt-in lab subsystem · admin gated promotion</p>
            </Link>
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.warningCard}>
            <h3 className={styles.warningTitle}>Guardrails that should stay visible</h3>
            <p className={styles.warningText}>
              Pancreatic Signal is research-use discovery software. It should stay citation-backed, human-gated, explicit
              about uncertainty, honest about limitations, and resistant to “autonomous diagnosis” framing even as the
              scientific-discovery story gets stronger.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
