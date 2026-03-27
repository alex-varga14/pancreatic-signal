import Link from "next/link";
import {
  getDemoBenchmarkSnapshot,
  getRetrospectiveBenchmarkSnapshot,
  PUBLISHED_DEMO_PROOF_PATH,
  PUBLISHED_RETROSPECTIVE_SAMPLE_PROOF_PATH,
  type DemoBenchmarkCaseMode,
  type ExternalBenchmarkCaseMode,
  type PublishedBenchmarkQueueEntry,
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

function formatBooleanLabel(value: boolean): string {
  return value ? "yes" : "no";
}

function formatFalseNegativeBuckets(buckets: Record<string, number>): string {
  const entries = Object.entries(buckets);
  return entries.length ? entries.map(([bucket, count]) => `${bucket}: ${count}`).join(", ") : "none";
}

function renderModeSummary(mode: DemoBenchmarkCaseMode): string {
  return `${formatOutcomeLabel(mode.outcome)} at ${formatScore(mode.score)} with cues ${formatCodeList(mode.rationale_codes)}`;
}

function renderExternalModeSummary(mode: ExternalBenchmarkCaseMode): string {
  const missBucket = mode.false_negative_bucket ? `; miss bucket ${mode.false_negative_bucket}` : "";
  return `${formatOutcomeLabel(mode.outcome)} at ${formatScore(mode.score)} with cues ${formatCodeList(mode.rationale_codes)}${missBucket}`;
}

function renderQueueSummary(entry: PublishedBenchmarkQueueEntry): string {
  const parts = [entry.case_id];
  if (entry.cohort) {
    parts.push(entry.cohort);
  }
  parts.push(entry.benchmark_bucket || "unbucketed", formatOutcomeLabel(entry.outcome));
  return parts.join(" • ");
}

export default async function ProofPage() {
  const demoSnapshot = await getDemoBenchmarkSnapshot();
  const retrospectiveSnapshot = await getRetrospectiveBenchmarkSnapshot();

  if (!demoSnapshot && !retrospectiveSnapshot) {
    return (
      <main className={styles.page}>
        <div className={styles.shell}>
          <section className={styles.warningCard}>
            <h1 className={styles.warningTitle}>Published benchmark snapshots not found</h1>
            <p className={styles.warningText}>
              Generate the checked-in proof artifacts with <span className={styles.inlineCode}>make refresh-demo-proof</span> and{" "}
              <span className={styles.inlineCode}>make refresh-external-sample-proof</span>, then reload this page.
            </p>
          </section>
        </div>
      </main>
    );
  }

  const missingArtifacts = [
    !demoSnapshot ? PUBLISHED_DEMO_PROOF_PATH : null,
    !retrospectiveSnapshot ? PUBLISHED_RETROSPECTIVE_SAMPLE_PROOF_PATH : null,
  ].filter((value): value is string => Boolean(value));
  const retrospectiveCohortNotes =
    retrospectiveSnapshot?.dataset_summary.cohort_counts?.filter((item) => Boolean(item.description)) ?? [];
  const retrospectiveBucketNotes =
    retrospectiveSnapshot?.dataset_summary.bucket_counts.filter((item) => Boolean(item.description)) ?? [];

  return (
    <main className={styles.page}>
      <div className={styles.shell}>
        <section className={styles.hero}>
          <p className={styles.eyebrow}>Benchmark Proof</p>
          <h1 className={styles.title}>A reproducible proof surface, not a hand-wavy claim.</h1>
          <p className={styles.subtitle}>
            This page renders two checked-in benchmark stories: the synthetic demo comparison and the deidentified
            retrospective-style external sample. It exists so collaborators can inspect concrete evaluation deltas, queue
            behavior, reviewer-facing casebooks, and the exact commands needed to reproduce them.
          </p>
          <div className={styles.chipRow}>
            <span className={styles.chip}>Synthetic demo comparison</span>
            <span className={styles.chip}>Deidentified retrospective sample</span>
            <span className={styles.chip}>Reproducible reviewer casebooks</span>
          </div>
          <div className={styles.ctaRow}>
            <Link href="/" className={styles.secondaryLink}>
              Back Home
            </Link>
            <Link href="/cases" className={styles.primaryLink}>
              Open Worklist
            </Link>
          </div>
        </section>

        {missingArtifacts.length ? (
          <section className={styles.section}>
            <div className={styles.warningCard}>
              <h2 className={styles.warningTitle}>One published proof artifact is missing</h2>
              <p className={styles.warningText}>
                Missing artifact{missingArtifacts.length > 1 ? "s" : ""}:{" "}
                <span className={styles.inlineCode}>{missingArtifacts.join(", ")}</span>. Regenerate the demo proof with{" "}
                <span className={styles.inlineCode}>make refresh-demo-proof</span> and the retrospective sample with{" "}
                <span className={styles.inlineCode}>make refresh-external-sample-proof</span>.
              </p>
            </div>
          </section>
        ) : null}

        {demoSnapshot ? (
          <>
            <section className={`${styles.section} ${styles.grid} ${styles.gridFour}`}>
              <article className={styles.card}>
                <p className={styles.statLabel}>Rules F1</p>
                <p className={styles.statValue}>{formatPercent(demoSnapshot.comparison.rules.f1)}</p>
                <p className={styles.statNote}>
                  Baseline deterministic score at threshold {demoSnapshot.comparison.threshold.toFixed(2)}.
                </p>
              </article>
              <article className={styles.card}>
                <p className={styles.statLabel}>Hybrid F1</p>
                <p className={styles.statValue}>{formatPercent(demoSnapshot.comparison.hybrid.f1)}</p>
                <p className={styles.statNote}>Explainable hybrid score at the same operating point.</p>
              </article>
              <article className={styles.card}>
                <p className={styles.statLabel}>Recall Lift</p>
                <p className={styles.statValue}>{formatDelta(demoSnapshot.comparison.recall_delta)}</p>
                <p className={styles.statNote}>
                  Resolved false negatives: {demoSnapshot.comparison.resolved_false_negatives.join(", ") || "none"}.
                </p>
              </article>
              <article className={styles.card}>
                <p className={styles.statLabel}>Published</p>
                <p className={styles.statValue}>{formatGeneratedAt(demoSnapshot.generated_at)}</p>
                <p className={styles.statNote}>
                  Snapshot file: <span className={styles.inlineCode}>{PUBLISHED_DEMO_PROOF_PATH}</span>.
                </p>
              </article>
            </section>

            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <div>
                  <p className={styles.eyebrow}>Demo Coverage</p>
                  <h2 className={styles.sectionTitle}>The synthetic proof still shows what kinds of cases it covers.</h2>
                  <p className={styles.sectionText}>
                    This is the intentionally controlled demo casebook. It stays useful because the checked-in corpus now
                    includes benchmark buckets and reviewer cues instead of only a flat metric summary.
                  </p>
                </div>
              </div>

              <div className={`${styles.grid} ${styles.gridFour}`}>
                <article className={styles.card}>
                  <p className={styles.statLabel}>Reports</p>
                  <p className={styles.statValue}>{demoSnapshot.dataset_summary.report_count}</p>
                  <p className={styles.statNote}>Total labeled benchmark cases in the published demo casebook.</p>
                </article>
                <article className={styles.card}>
                  <p className={styles.statLabel}>Positive Labels</p>
                  <p className={styles.statValue}>{demoSnapshot.dataset_summary.positive_count}</p>
                  <p className={styles.statNote}>Cases that should still surface for human review.</p>
                </article>
                <article className={styles.card}>
                  <p className={styles.statLabel}>Escalations</p>
                  <p className={styles.statValue}>{demoSnapshot.dataset_summary.escalation_count}</p>
                  <p className={styles.statNote}>Cases expected to warrant escalation, not just passive follow-up.</p>
                </article>
                <article className={styles.card}>
                  <p className={styles.statLabel}>Buckets</p>
                  <p className={styles.statValue}>{demoSnapshot.dataset_summary.bucket_counts.length}</p>
                  <p className={styles.statNote}>Benchmark buckets represented in the current demo snapshot.</p>
                </article>
              </div>

              <div className={styles.chipRow}>
                {demoSnapshot.dataset_summary.bucket_counts.map((bucket) => (
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
                      <th>Top-{demoSnapshot.comparison.top_k} Precision</th>
                      <th>Top-{demoSnapshot.comparison.top_k} Sensitivity</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Rules</td>
                      <td>{formatPercent(demoSnapshot.comparison.rules.precision)}</td>
                      <td>{formatPercent(demoSnapshot.comparison.rules.recall)}</td>
                      <td>{formatPercent(demoSnapshot.comparison.rules.f1)}</td>
                      <td>{demoSnapshot.comparison.rules.flagged}</td>
                      <td>{formatPercent(demoSnapshot.comparison.rules.precision_at_top_k)}</td>
                      <td>{formatPercent(demoSnapshot.comparison.rules.sensitivity_at_top_k)}</td>
                    </tr>
                    <tr>
                      <td>Hybrid</td>
                      <td>{formatPercent(demoSnapshot.comparison.hybrid.precision)}</td>
                      <td>{formatPercent(demoSnapshot.comparison.hybrid.recall)}</td>
                      <td>{formatPercent(demoSnapshot.comparison.hybrid.f1)}</td>
                      <td>{demoSnapshot.comparison.hybrid.flagged}</td>
                      <td>{formatPercent(demoSnapshot.comparison.hybrid.precision_at_top_k)}</td>
                      <td>{formatPercent(demoSnapshot.comparison.hybrid.sensitivity_at_top_k)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <section className={styles.section}>
              <div className={`${styles.grid} ${styles.gridThree}`}>
                <article className={styles.card}>
                  <h3 className={styles.cardTitle}>Newly surfaced by hybrid</h3>
                  <p className={styles.cardText}>{demoSnapshot.comparison.newly_flagged_cases.join(", ") || "none"}</p>
                </article>
                <article className={styles.card}>
                  <h3 className={styles.cardTitle}>Recommended rules threshold</h3>
                  <p className={styles.cardText}>
                    {demoSnapshot.sweep.rules_recommendation.recommended_threshold.toFixed(2)} with{" "}
                    {formatPercent(demoSnapshot.sweep.rules_recommendation.recall)} recall and{" "}
                    {formatPercent(demoSnapshot.sweep.rules_recommendation.f1)} F1.
                  </p>
                </article>
                <article className={styles.card}>
                  <h3 className={styles.cardTitle}>Recommended hybrid threshold</h3>
                  <p className={styles.cardText}>
                    {demoSnapshot.sweep.hybrid_recommendation.recommended_threshold.toFixed(2)} with{" "}
                    {formatPercent(demoSnapshot.sweep.hybrid_recommendation.recall)} recall and{" "}
                    {formatPercent(demoSnapshot.sweep.hybrid_recommendation.f1)} F1.
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
                    These are the current top-{demoSnapshot.queue_preview.top_k} queues for rules and hybrid scoring, which
                    makes it easy to see when hybrid is surfacing a follow-up-worthy case that rules leave behind.
                  </p>
                </div>
              </div>

              <div className={`${styles.grid} ${styles.gridTwo}`}>
                <article className={styles.card}>
                  <h3 className={styles.cardTitle}>Rules Queue</h3>
                  <div className={styles.queueList}>
                    {demoSnapshot.queue_preview.rules.map((entry) => (
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
                    {demoSnapshot.queue_preview.hybrid.map((entry) => (
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
                    {demoSnapshot.sweep.points.map((point) => (
                      <tr key={point.threshold}>
                        <td>{point.threshold.toFixed(2)}</td>
                        <td>{formatPercent(point.rules_f1)}</td>
                        <td>{formatPercent(point.hybrid_f1)}</td>
                        <td>{formatPercent(point.rules_recall)}</td>
                        <td>{formatPercent(point.hybrid_recall)}</td>
                        <td>
                          {point.flagged_delta >= 0 ? "+" : ""}
                          {point.flagged_delta}
                        </td>
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
                  <h2 className={styles.sectionTitle}>Each demo case carries a reviewer cue, not just a label.</h2>
                  <p className={styles.sectionText}>
                    This is the layer that turns the benchmark from a scoreboard into an explainable proof surface. You can
                    see what kind of case each example represents, what the reviewer should notice, and how rules versus
                    hybrid treat it.
                  </p>
                </div>
              </div>

              <div className={styles.casebookGrid}>
                {demoSnapshot.casebook.map((entry) => (
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
                      <span className={styles.miniChip}>Expected positive: {formatBooleanLabel(entry.expected_positive)}</span>
                      <span className={styles.miniChip}>
                        Expected escalation: {formatBooleanLabel(entry.expected_escalation)}
                      </span>
                      <span className={styles.miniChip}>
                        Hybrid lift: {entry.hybrid_lift >= 0 ? "+" : ""}
                        {entry.hybrid_lift.toFixed(2)}
                      </span>
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
                <h2 className={styles.codeTitle}>The demo benchmark story should survive a clean checkout.</h2>
                <pre className={styles.codeBlock}>
{`make validate-strict
make benchmark-demo
make refresh-demo-proof
python scripts/run_demo_eval.py --compare --json`}
                </pre>
                <p className={styles.codeText}>
                  Dataset paths: <span className={styles.inlineCode}>{demoSnapshot.dataset.reports_path}</span> and{" "}
                  <span className={styles.inlineCode}>{demoSnapshot.dataset.labels_path}</span>.
                </p>
              </div>
            </section>
          </>
        ) : null}

        {retrospectiveSnapshot ? (
          <>
            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <div>
                  <p className={styles.eyebrow}>Retrospective Sample</p>
                  <h2 className={styles.sectionTitle}>A broader multi-cohort external casebook now sits beside the demo proof.</h2>
                  <p className={styles.sectionText}>
                    This sample is still intentionally bounded, but it now shows the same proof shape across multiple
                    deidentified retrospective-style cohorts instead of only a single undifferentiated pack.
                  </p>
                </div>
              </div>

              <div className={`${styles.grid} ${styles.gridFour}`}>
                <article className={styles.card}>
                  <p className={styles.statLabel}>External F1</p>
                  <p className={styles.statValue}>{formatPercent(retrospectiveSnapshot.evaluation.f1)}</p>
                  <p className={styles.statNote}>Current external casebook operating point.</p>
                </article>
                <article className={styles.card}>
                  <p className={styles.statLabel}>External Recall</p>
                  <p className={styles.statValue}>{formatPercent(retrospectiveSnapshot.evaluation.recall)}</p>
                  <p className={styles.statNote}>Action-worthy retrospective-style cases still surfaced at threshold 0.30.</p>
                </article>
                <article className={styles.card}>
                  <p className={styles.statLabel}>Recommended Threshold</p>
                  <p className={styles.statValue}>{retrospectiveSnapshot.sweep.recommendation.recommended_threshold.toFixed(2)}</p>
                  <p className={styles.statNote}>
                    Miss buckets: {formatFalseNegativeBuckets(retrospectiveSnapshot.evaluation.false_negative_buckets)}.
                  </p>
                </article>
                <article className={styles.card}>
                  <p className={styles.statLabel}>Published</p>
                  <p className={styles.statValue}>{formatGeneratedAt(retrospectiveSnapshot.generated_at)}</p>
                  <p className={styles.statNote}>
                    Snapshot file: <span className={styles.inlineCode}>{PUBLISHED_RETROSPECTIVE_SAMPLE_PROOF_PATH}</span>.
                  </p>
                </article>
              </div>
            </section>

            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <div>
                  <p className={styles.eyebrow}>Sample Coverage</p>
                  <h2 className={styles.sectionTitle}>The external proof is small, deidentified, and reviewer-readable.</h2>
                  <p className={styles.sectionText}>
                    The checked-in sample keeps the same bucketed coverage and queue preview structure while adding report
                    excerpts and one intentional follow-up miss that reviewers can inspect directly.
                  </p>
                </div>
              </div>

              <div className={`${styles.grid} ${styles.gridFour}`}>
                <article className={styles.card}>
                  <p className={styles.statLabel}>Reports</p>
                  <p className={styles.statValue}>{retrospectiveSnapshot.dataset_summary.report_count}</p>
                  <p className={styles.statNote}>Deidentified retrospective-style cases in the checked-in sample.</p>
                </article>
                <article className={styles.card}>
                  <p className={styles.statLabel}>Positive Labels</p>
                  <p className={styles.statValue}>{retrospectiveSnapshot.dataset_summary.positive_count}</p>
                  <p className={styles.statNote}>Cases expected to stay visible for review or follow-up.</p>
                </article>
                <article className={styles.card}>
                  <p className={styles.statLabel}>Escalations</p>
                  <p className={styles.statValue}>{retrospectiveSnapshot.dataset_summary.escalation_count}</p>
                  <p className={styles.statNote}>Cases expected to justify escalation rather than passive follow-up.</p>
                </article>
                <article className={styles.card}>
                  <p className={styles.statLabel}>Cohorts</p>
                  <p className={styles.statValue}>
                    {retrospectiveSnapshot.dataset_summary.cohort_counts?.length ?? 0}
                  </p>
                  <p className={styles.statNote}>
                    {retrospectiveSnapshot.dataset.dataset_name} on the {retrospectiveSnapshot.dataset.dataset_split} split.
                  </p>
                </article>
              </div>

              <div className={styles.chipRow}>
                {retrospectiveSnapshot.dataset_summary.bucket_counts.map((bucket) => (
                  <span key={bucket.bucket} className={styles.chip}>
                    {bucket.bucket}: {bucket.case_count}
                  </span>
                ))}
              </div>

              {retrospectiveSnapshot.dataset_summary.cohort_counts?.length ? (
                <div className={styles.chipRow}>
                  {retrospectiveSnapshot.dataset_summary.cohort_counts.map((cohort) => (
                    <span key={cohort.cohort} className={styles.chip}>
                      {cohort.cohort}: {cohort.case_count}
                    </span>
                  ))}
                </div>
              ) : null}
            </section>

            {retrospectiveSnapshot.dataset_context ||
            retrospectiveCohortNotes.length ||
            retrospectiveBucketNotes.length ? (
              <section className={styles.section}>
                <div className={`${styles.grid} ${styles.gridTwo}`}>
                  {retrospectiveSnapshot.dataset_context ? (
                    <article className={styles.card}>
                      <h3 className={styles.cardTitle}>Dataset Framing</h3>
                      {retrospectiveSnapshot.dataset_context.dataset_description ? (
                        <p className={styles.cardText}>{retrospectiveSnapshot.dataset_context.dataset_description}</p>
                      ) : null}
                      {retrospectiveSnapshot.dataset_context.labeling_policy ? (
                        <>
                          <p className={styles.casebookMeta}>Labeling policy</p>
                          <p className={styles.cardText}>{retrospectiveSnapshot.dataset_context.labeling_policy}</p>
                        </>
                      ) : null}
                      {retrospectiveSnapshot.dataset_context.notes ? (
                        <>
                          <p className={styles.casebookMeta}>Notes</p>
                          <p className={styles.cardText}>{retrospectiveSnapshot.dataset_context.notes}</p>
                        </>
                      ) : null}
                      {retrospectiveSnapshot.dataset.manifest_path ? (
                        <p className={styles.casebookMeta}>
                          Manifest: <span className={styles.inlineCode}>{retrospectiveSnapshot.dataset.manifest_path}</span>
                        </p>
                      ) : null}
                    </article>
                  ) : null}

                  {retrospectiveCohortNotes.length || retrospectiveBucketNotes.length ? (
                    <article className={styles.card}>
                      <h3 className={styles.cardTitle}>Benchmark Notes</h3>
                      {retrospectiveCohortNotes.length ? (
                        <>
                          <p className={styles.casebookMeta}>Cohorts</p>
                          <ul className={styles.list}>
                            {retrospectiveCohortNotes.map((cohort) => (
                              <li key={cohort.cohort}>
                                {cohort.cohort}: {cohort.description}
                              </li>
                            ))}
                          </ul>
                        </>
                      ) : null}
                      {retrospectiveBucketNotes.length ? (
                        <>
                          <p className={styles.casebookMeta}>Buckets</p>
                          <ul className={styles.list}>
                            {retrospectiveBucketNotes.map((bucket) => (
                              <li key={bucket.bucket}>
                                {bucket.bucket}: {bucket.description}
                              </li>
                            ))}
                          </ul>
                        </>
                      ) : null}
                    </article>
                  ) : null}
                </div>
              </section>
            ) : null}

            <section className={styles.section}>
              <div className={`${styles.grid} ${styles.gridTwo}`}>
                <article className={styles.card}>
                  <h3 className={styles.cardTitle}>External Queue</h3>
                  <p className={styles.cardText}>
                    Current top-{retrospectiveSnapshot.queue_preview.top_k} ranking for the deidentified retrospective sample
                    across its recorded cohorts.
                  </p>
                  <div className={styles.queueList}>
                    {retrospectiveSnapshot.queue_preview.external.map((entry) => (
                      <div key={`external-${entry.case_id}`} className={styles.queueItem}>
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
                  <h3 className={styles.cardTitle}>Submission Framing</h3>
                  <p className={styles.cardText}>{retrospectiveSnapshot.sweep.recommendation.rationale}</p>
                  {retrospectiveSnapshot.submission?.notable_strengths?.length ? (
                    <>
                      <p className={styles.casebookMeta}>Notable strengths</p>
                      <ul className={styles.list}>
                        {retrospectiveSnapshot.submission.notable_strengths.map((strength) => (
                          <li key={strength}>{strength}</li>
                        ))}
                      </ul>
                    </>
                  ) : null}
                  {retrospectiveSnapshot.submission?.known_limitations?.length ? (
                    <>
                      <p className={styles.casebookMeta}>Known limitations</p>
                      <ul className={styles.list}>
                        {retrospectiveSnapshot.submission.known_limitations.map((limitation) => (
                          <li key={limitation}>{limitation}</li>
                        ))}
                      </ul>
                    </>
                  ) : null}
                </article>
              </div>
            </section>

            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <div>
                  <p className={styles.eyebrow}>External Threshold Sweep</p>
                  <h2 className={styles.sectionTitle}>The external sample keeps its operating point explicit too.</h2>
                </div>
              </div>

              <div className={styles.tableWrap}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>Threshold</th>
                      <th>Precision</th>
                      <th>Recall</th>
                      <th>F1</th>
                      <th>Flagged</th>
                      <th>Top-{retrospectiveSnapshot.sweep.top_k} Sensitivity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {retrospectiveSnapshot.sweep.points.map((point) => (
                      <tr key={point.threshold}>
                        <td>{point.threshold.toFixed(2)}</td>
                        <td>{formatPercent(point.precision)}</td>
                        <td>{formatPercent(point.recall)}</td>
                        <td>{formatPercent(point.f1)}</td>
                        <td>{point.flagged}</td>
                        <td>{formatPercent(point.sensitivity_at_top_k)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className={styles.section}>
              <div className={styles.sectionHeader}>
                <div>
                  <p className={styles.eyebrow}>External Reviewer Casebook</p>
                  <h2 className={styles.sectionTitle}>The same reviewer-facing proof shape now works on less-synthetic text.</h2>
                  <p className={styles.sectionText}>
                    Each entry keeps the deidentified report excerpt, reviewer focus, and the actual external scoring outcome
                    so missed follow-up cases stay inspectable instead of disappearing into summary metrics.
                  </p>
                </div>
              </div>

              <div className={styles.casebookGrid}>
                {retrospectiveSnapshot.casebook.map((entry) => (
                  <article key={entry.case_id} className={styles.casebookCard}>
                    <div className={styles.casebookHeader}>
                      <div>
                        <p className={styles.casebookMeta}>{entry.report_id}</p>
                        <h3 className={styles.cardTitle}>{entry.case_id}</h3>
                      </div>
                      <span className={styles.casebookTag}>{entry.benchmark_bucket || "unbucketed"}</span>
                    </div>

                    <p className={styles.casebookFocus}>{entry.reviewer_focus || "No reviewer cue recorded."}</p>
                    {entry.report_excerpt ? <p className={styles.casebookMeta}>{entry.report_excerpt}</p> : null}
                    <p className={styles.casebookMeta}>{entry.label_notes || "No label note recorded."}</p>

                    <div className={styles.miniChipRow}>
                      {entry.cohort ? <span className={styles.miniChip}>Cohort: {entry.cohort}</span> : null}
                      <span className={styles.miniChip}>Expected positive: {formatBooleanLabel(entry.expected_positive)}</span>
                      <span className={styles.miniChip}>
                        Expected escalation: {formatBooleanLabel(entry.expected_escalation)}
                      </span>
                      {entry.external.false_negative_bucket ? (
                        <span className={styles.miniChip}>Miss bucket: {entry.external.false_negative_bucket}</span>
                      ) : null}
                    </div>

                    <p className={styles.casebookMeta}>
                      Expected rationale cues: <span className={styles.inlineCode}>{formatCodeList(entry.expected_rationale_codes)}</span>
                    </p>

                    <div className={styles.resultCard}>
                      <p className={styles.resultLabel}>External</p>
                      <p className={styles.resultValue}>{formatOutcomeLabel(entry.external.outcome)}</p>
                      <p className={styles.resultText}>{renderExternalModeSummary(entry.external)}</p>
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className={styles.section}>
              <div className={styles.codePanel}>
                <p className={styles.codeLabel}>Reproduce This</p>
                <h2 className={styles.codeTitle}>The external sample proof should survive a clean checkout too.</h2>
                <pre className={styles.codeBlock}>
{`make benchmark-external-sample
make refresh-external-sample-proof
make validate-benchmark-submission \\
  SUBMISSION=docs/examples/retrospective-benchmark-sample-current-submission.json`}
                </pre>
                <p className={styles.codeText}>
                  Source files: <span className={styles.inlineCode}>{retrospectiveSnapshot.dataset.labels_path}</span> and{" "}
                  <span className={styles.inlineCode}>{retrospectiveSnapshot.dataset.predictions_path}</span>.
                </p>
              </div>
            </section>
          </>
        ) : null}
      </div>
    </main>
  );
}
