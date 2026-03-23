import Link from "next/link";
import { getDemoBenchmarkSnapshot, PUBLISHED_DEMO_PROOF_PATH } from "../../lib/demo-proof";
import styles from "../marketing.module.css";

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatDelta(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(1)} pts`;
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

export default async function ProofPage() {
  const snapshot = await getDemoBenchmarkSnapshot();

  if (!snapshot) {
    return (
      <main className={styles.page}>
        <div className={styles.shell}>
          <section className={styles.warningCard}>
            <h1 className={styles.warningTitle}>Published benchmark snapshot not found</h1>
            <p className={styles.warningText}>
              Generate the checked-in proof artifact with <span className={styles.inlineCode}>make refresh-demo-proof</span>,
              then reload this page.
            </p>
          </section>
        </div>
      </main>
    );
  }

  const { comparison, sweep } = snapshot;

  return (
    <main className={styles.page}>
      <div className={styles.shell}>
        <section className={styles.hero}>
          <p className={styles.eyebrow}>Benchmark Proof</p>
          <h1 className={styles.title}>A reproducible proof surface, not a hand-wavy claim.</h1>
          <p className={styles.subtitle}>
            This page renders the current checked-in demo benchmark snapshot. It exists so new collaborators can see concrete
            evaluation deltas, recommended thresholds, and the commands required to reproduce them.
          </p>
          <div className={styles.ctaRow}>
            <Link href="/" className={styles.secondaryLink}>
              Back Home
            </Link>
            <Link href="/cases" className={styles.primaryLink}>
              Open Worklist
            </Link>
          </div>
        </section>

        <section className={`${styles.section} ${styles.grid} ${styles.gridFour}`}>
          <article className={styles.card}>
            <p className={styles.statLabel}>Rules F1</p>
            <p className={styles.statValue}>{formatPercent(comparison.rules.f1)}</p>
            <p className={styles.statNote}>Baseline deterministic score at threshold {comparison.threshold.toFixed(2)}.</p>
          </article>
          <article className={styles.card}>
            <p className={styles.statLabel}>Hybrid F1</p>
            <p className={styles.statValue}>{formatPercent(comparison.hybrid.f1)}</p>
            <p className={styles.statNote}>Explainable hybrid score at the same operating point.</p>
          </article>
          <article className={styles.card}>
            <p className={styles.statLabel}>Recall Lift</p>
            <p className={styles.statValue}>{formatDelta(comparison.recall_delta)}</p>
            <p className={styles.statNote}>Resolved false negatives: {comparison.resolved_false_negatives.join(", ") || "none"}.</p>
          </article>
          <article className={styles.card}>
            <p className={styles.statLabel}>Published</p>
            <p className={styles.statValue}>{formatGeneratedAt(snapshot.generated_at)}</p>
            <p className={styles.statNote}>Snapshot file: <span className={styles.inlineCode}>{PUBLISHED_DEMO_PROOF_PATH}</span>.</p>
          </article>
        </section>

        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <div>
              <p className={styles.eyebrow}>Comparison</p>
              <h2 className={styles.sectionTitle}>Rules and hybrid side by side.</h2>
              <p className={styles.sectionText}>
                The demo benchmark is about triage usefulness, not vanity metrics. These numbers come from the checked-in
                synthetic dataset and label file referenced below.
              </p>
            </div>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Mode</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1</th>
                  <th>Flagged</th>
                  <th>Top-{comparison.top_k} Precision</th>
                  <th>Top-{comparison.top_k} Sensitivity</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Rules</td>
                  <td>{formatPercent(comparison.rules.precision)}</td>
                  <td>{formatPercent(comparison.rules.recall)}</td>
                  <td>{formatPercent(comparison.rules.f1)}</td>
                  <td>{comparison.rules.flagged}</td>
                  <td>{formatPercent(comparison.rules.precision_at_top_k)}</td>
                  <td>{formatPercent(comparison.rules.sensitivity_at_top_k)}</td>
                </tr>
                <tr>
                  <td>Hybrid</td>
                  <td>{formatPercent(comparison.hybrid.precision)}</td>
                  <td>{formatPercent(comparison.hybrid.recall)}</td>
                  <td>{formatPercent(comparison.hybrid.f1)}</td>
                  <td>{comparison.hybrid.flagged}</td>
                  <td>{formatPercent(comparison.hybrid.precision_at_top_k)}</td>
                  <td>{formatPercent(comparison.hybrid.sensitivity_at_top_k)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section className={styles.section}>
          <div className={`${styles.grid} ${styles.gridThree}`}>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Newly surfaced by hybrid</h3>
              <p className={styles.cardText}>{comparison.newly_flagged_cases.join(", ") || "none"}</p>
            </article>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Recommended rules threshold</h3>
              <p className={styles.cardText}>
                {sweep.rules_recommendation.recommended_threshold.toFixed(2)} with {formatPercent(sweep.rules_recommendation.recall)} recall
                and {formatPercent(sweep.rules_recommendation.f1)} F1.
              </p>
            </article>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Recommended hybrid threshold</h3>
              <p className={styles.cardText}>
                {sweep.hybrid_recommendation.recommended_threshold.toFixed(2)} with {formatPercent(sweep.hybrid_recommendation.recall)} recall
                and {formatPercent(sweep.hybrid_recommendation.f1)} F1.
              </p>
            </article>
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <div>
              <p className={styles.eyebrow}>Threshold Sweep</p>
              <h2 className={styles.sectionTitle}>Operating points should be explicit.</h2>
            </div>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Threshold</th>
                  <th>Rules F1</th>
                  <th>Hybrid F1</th>
                  <th>Rules Recall</th>
                  <th>Hybrid Recall</th>
                  <th>Flagged Delta</th>
                </tr>
              </thead>
              <tbody>
                {sweep.points.map((point) => (
                  <tr key={point.threshold}>
                    <td>{point.threshold.toFixed(2)}</td>
                    <td>{formatPercent(point.rules_f1)}</td>
                    <td>{formatPercent(point.hybrid_f1)}</td>
                    <td>{formatPercent(point.rules_recall)}</td>
                    <td>{formatPercent(point.hybrid_recall)}</td>
                    <td>{point.flagged_delta >= 0 ? "+" : ""}{point.flagged_delta}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.codePanel}>
            <p className={styles.codeLabel}>Reproduce This</p>
            <h2 className={styles.codeTitle}>The benchmark story should survive a clean checkout.</h2>
            <pre className={styles.codeBlock}>
{`make validate-strict
make benchmark-demo
make refresh-demo-proof
python scripts/run_demo_eval.py --compare --json`}
            </pre>
            <p className={styles.codeText}>
              Dataset paths: <span className={styles.inlineCode}>{snapshot.dataset.reports_path}</span> and{" "}
              <span className={styles.inlineCode}>{snapshot.dataset.labels_path}</span>.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
