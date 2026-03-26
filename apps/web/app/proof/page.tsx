import Link from "next/link";
import {
  getDemoBenchmarkSnapshot,
  PUBLISHED_DEMO_PROOF_PATH,
  type DemoBenchmarkCaseMode,
  type DemoBenchmarkQueueEntry,
} from "../../lib/demo-proof";
import styles from "../marketing.module.css";

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatDelta(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(1)} pts`;
}

function formatScore(value: number): string {
  return value.toFixed(2);
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

function formatOutcomeLabel(value: string): string {
  switch (value) {
    case "true_positive":
      return "True positive";
    case "false_positive":
      return "False positive";
    case "missed_positive":
      return "Missed positive";
    case "true_negative":
      return "True negative";
    default:
      return value;
  }
}

function formatCodeList(values: string[]): string {
  return values.length ? values.join(", ") : "none";
}

function renderModeSummary(mode: DemoBenchmarkCaseMode): string {
  return `${formatOutcomeLabel(mode.outcome)} at ${formatScore(mode.score)} with cues ${formatCodeList(mode.rationale_codes)}`;
}

function renderQueueSummary(entry: DemoBenchmarkQueueEntry): string {
  return `${entry.case_id} • ${entry.benchmark_bucket || "unbucketed"} • ${formatOutcomeLabel(entry.outcome)}`;
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

  const { comparison, dataset_summary: datasetSummary, queue_preview: queuePreview, sweep, casebook } = snapshot;

  return (
    <main className={styles.page}>
      <div className={styles.shell}>
        <section className={styles.hero}>
          <p className={styles.eyebrow}>Benchmark Proof</p>
          <h1 className={styles.title}>A reproducible proof surface, not a hand-wavy claim.</h1>
          <p className={styles.subtitle}>
            This page renders the current checked-in demo benchmark snapshot. It exists so new collaborators can see concrete
            evaluation deltas, queue behavior, reviewer-facing benchmark cases, and the commands required to reproduce them.
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
              <p className={styles.eyebrow}>Dataset Coverage</p>
              <h2 className={styles.sectionTitle}>The proof surface now shows what kinds of cases it covers.</h2>
              <p className={styles.sectionText}>
                This is still a small synthetic set, but it now carries explicit benchmark buckets and reviewer cues so the
                proof page reads like a casebook rather than only a metric summary.
              </p>
            </div>
          </div>

          <div className={`${styles.grid} ${styles.gridFour}`}>
            <article className={styles.card}>
              <p className={styles.statLabel}>Reports</p>
              <p className={styles.statValue}>{datasetSummary.report_count}</p>
              <p className={styles.statNote}>Total labeled benchmark cases in the published casebook.</p>
            </article>
            <article className={styles.card}>
              <p className={styles.statLabel}>Positive Labels</p>
              <p className={styles.statValue}>{datasetSummary.positive_count}</p>
              <p className={styles.statNote}>Cases that should still surface for human review.</p>
            </article>
            <article className={styles.card}>
              <p className={styles.statLabel}>Escalations</p>
              <p className={styles.statValue}>{datasetSummary.escalation_count}</p>
              <p className={styles.statNote}>Cases expected to warrant escalation, not just passive follow-up.</p>
            </article>
            <article className={styles.card}>
              <p className={styles.statLabel}>Buckets</p>
              <p className={styles.statValue}>{datasetSummary.bucket_counts.length}</p>
              <p className={styles.statNote}>Benchmark buckets represented in the current demo snapshot.</p>
            </article>
          </div>

          <div className={styles.chipRow}>
            {datasetSummary.bucket_counts.map((bucket) => (
              <span key={bucket.bucket} className={styles.chip}>
                {bucket.bucket}: {bucket.case_count}
              </span>
            ))}
          </div>
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
              <p className={styles.eyebrow}>Queue Preview</p>
              <h2 className={styles.sectionTitle}>Reviewer-visible ranking matters as much as aggregate metrics.</h2>
              <p className={styles.sectionText}>
                These are the current top-{queuePreview.top_k} queues for rules and hybrid scoring, which makes it easy to
                see when hybrid is surfacing a follow-up-worthy case that rules leave behind.
              </p>
            </div>
          </div>

          <div className={`${styles.grid} ${styles.gridTwo}`}>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Rules Queue</h3>
              <div className={styles.queueList}>
                {queuePreview.rules.map((entry) => (
                  <div key={`rules-${entry.case_id}`} className={styles.queueItem}>
                    <div>
                      <p className={styles.queueItemTitle}>{renderQueueSummary(entry)}</p>
                      <p className={styles.queueItemMeta}>{entry.report_id}</p>
                    </div>
                    <p className={styles.queueItemScore}>{formatScore(entry.score)}</p>
                  </div>
                ))}
              </div>
            </article>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Hybrid Queue</h3>
              <div className={styles.queueList}>
                {queuePreview.hybrid.map((entry) => (
                  <div key={`hybrid-${entry.case_id}`} className={styles.queueItem}>
                    <div>
                      <p className={styles.queueItemTitle}>{renderQueueSummary(entry)}</p>
                      <p className={styles.queueItemMeta}>{entry.report_id}</p>
                    </div>
                    <p className={styles.queueItemScore}>{formatScore(entry.score)}</p>
                  </div>
                ))}
              </div>
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
          <div className={styles.sectionHeader}>
            <div>
              <p className={styles.eyebrow}>Reviewer Casebook</p>
              <h2 className={styles.sectionTitle}>Each benchmark case now carries a reviewer cue, not just a label.</h2>
              <p className={styles.sectionText}>
                This is the layer that turns the benchmark from a scoreboard into an explainable proof surface. You can see
                what kind of case each example represents, what the reviewer should notice, and how rules versus hybrid
                treat it.
              </p>
            </div>
          </div>

          <div className={styles.casebookGrid}>
            {casebook.map((entry) => (
              <article key={entry.case_id} className={styles.casebookCard}>
                <div className={styles.casebookHeader}>
                  <div>
                    <p className={styles.casebookMeta}>{entry.report_id}</p>
                    <h3 className={styles.cardTitle}>{entry.case_id}</h3>
                  </div>
                  <span className={styles.casebookTag}>{entry.benchmark_bucket || "unbucketed"}</span>
                </div>

                <p className={styles.casebookFocus}>{entry.reviewer_focus || "No reviewer cue recorded."}</p>
                <p className={styles.casebookMeta}>{entry.label_notes || "No label note recorded."}</p>

                <div className={styles.miniChipRow}>
                  <span className={styles.miniChip}>Expected positive: {String(entry.expected_positive)}</span>
                  <span className={styles.miniChip}>Expected escalation: {String(entry.expected_escalation)}</span>
                  <span className={styles.miniChip}>Hybrid lift: {entry.hybrid_lift >= 0 ? "+" : ""}{entry.hybrid_lift.toFixed(2)}</span>
                </div>

                <p className={styles.casebookMeta}>
                  Expected rationale cues: <span className={styles.inlineCode}>{formatCodeList(entry.expected_rationale_codes)}</span>
                </p>

                <div className={styles.resultGrid}>
                  <div className={styles.resultCard}>
                    <p className={styles.resultLabel}>Rules</p>
                    <p className={styles.resultValue}>{formatOutcomeLabel(entry.rules.outcome)}</p>
                    <p className={styles.resultText}>{renderModeSummary(entry.rules)}</p>
                  </div>
                  <div className={styles.resultCard}>
                    <p className={styles.resultLabel}>Hybrid</p>
                    <p className={styles.resultValue}>{formatOutcomeLabel(entry.hybrid.outcome)}</p>
                    <p className={styles.resultText}>{renderModeSummary(entry.hybrid)}</p>
                  </div>
                </div>
              </article>
            ))}
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
