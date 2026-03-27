import Link from "next/link";
import {
  getDemoBenchmarkSnapshot,
  PUBLISHED_DEMO_PROOF_PATH,
  PUBLISHED_EXTERNAL_BENCHMARK_REGISTRY_PATH,
  getPublishedExternalBenchmarkEntries,
  type DemoBenchmarkCaseMode,
  type ExternalBenchmarkCaseMode,
  type ExternalBenchmarkSnapshot,
  type PublishedExternalBenchmarkEntry,
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

type ExternalBenchmarkProofSectionProps = {
  entry: PublishedExternalBenchmarkEntry & { snapshot: ExternalBenchmarkSnapshot };
};

function ExternalBenchmarkProofSection({ entry }: ExternalBenchmarkProofSectionProps) {
  const { descriptor, snapshot } = entry;
  const cohortNotes = snapshot.dataset_summary.cohort_counts?.filter((item) => Boolean(item.description)) ?? [];
  const bucketNotes = snapshot.dataset_summary.bucket_counts.filter((item) => Boolean(item.description));
  const reproduceCommands = [
    descriptor.build_command,
    descriptor.refresh_command,
    descriptor.submission_path
      ? `make validate-benchmark-submission \\\n  SUBMISSION=${descriptor.submission_path}`
      : null,
  ].filter((value): value is string => Boolean(value));

  return (
    <>
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <div>
            <p className={styles.eyebrow}>{descriptor.label}</p>
            <h2 className={styles.sectionTitle}>{descriptor.title}</h2>
            <p className={styles.sectionText}>{descriptor.description}</p>
          </div>
        </div>

        <div className={`${styles.grid} ${styles.gridFour}`}>
          <article className={styles.card}>
            <p className={styles.statLabel}>External F1</p>
            <p className={styles.statValue}>{formatPercent(snapshot.evaluation.f1)}</p>
            <p className={styles.statNote}>Current external casebook operating point.</p>
          </article>
          <article className={styles.card}>
            <p className={styles.statLabel}>External Recall</p>
            <p className={styles.statValue}>{formatPercent(snapshot.evaluation.recall)}</p>
            <p className={styles.statNote}>Action-worthy cases still surfaced at the current threshold.</p>
          </article>
          <article className={styles.card}>
            <p className={styles.statLabel}>Recommended Threshold</p>
            <p className={styles.statValue}>{snapshot.sweep.recommendation.recommended_threshold.toFixed(2)}</p>
            <p className={styles.statNote}>
              Miss buckets: {formatFalseNegativeBuckets(snapshot.evaluation.false_negative_buckets)}.
            </p>
          </article>
          <article className={styles.card}>
            <p className={styles.statLabel}>Published</p>
            <p className={styles.statValue}>{formatGeneratedAt(snapshot.generated_at)}</p>
            <p className={styles.statNote}>
              Snapshot file: <span className={styles.inlineCode}>{descriptor.snapshot_path}</span>.
            </p>
          </article>
        </div>
      </section>

      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <div>
            <p className={styles.eyebrow}>Sample Coverage</p>
            <h2 className={styles.sectionTitle}>The external proof stays reviewer-readable as the pack surface grows.</h2>
            <p className={styles.sectionText}>
              This checked-in benchmark pack keeps dataset coverage, queue previews, and a reviewer-facing casebook visible
              so new collaborator packs can match the same proof shape instead of becoming metrics-only attachments.
            </p>
          </div>
        </div>

        <div className={`${styles.grid} ${styles.gridFour}`}>
          <article className={styles.card}>
            <p className={styles.statLabel}>Reports</p>
            <p className={styles.statValue}>{snapshot.dataset_summary.report_count}</p>
            <p className={styles.statNote}>Published reports in this checked-in external benchmark pack.</p>
          </article>
          <article className={styles.card}>
            <p className={styles.statLabel}>Positive Labels</p>
            <p className={styles.statValue}>{snapshot.dataset_summary.positive_count}</p>
            <p className={styles.statNote}>Cases expected to stay visible for review or follow-up.</p>
          </article>
          <article className={styles.card}>
            <p className={styles.statLabel}>Escalations</p>
            <p className={styles.statValue}>{snapshot.dataset_summary.escalation_count}</p>
            <p className={styles.statNote}>Cases expected to justify escalation rather than passive follow-up.</p>
          </article>
          <article className={styles.card}>
            <p className={styles.statLabel}>Cohorts</p>
            <p className={styles.statValue}>{snapshot.dataset_summary.cohort_counts?.length ?? 0}</p>
            <p className={styles.statNote}>
              {snapshot.dataset.dataset_name} on the {snapshot.dataset.dataset_split} split.
            </p>
          </article>
        </div>

        <div className={styles.chipRow}>
          {snapshot.dataset_summary.bucket_counts.map((bucket) => (
            <span key={bucket.bucket} className={styles.chip}>
              {bucket.bucket}: {bucket.case_count}
            </span>
          ))}
        </div>

        {snapshot.dataset_summary.cohort_counts?.length ? (
          <div className={styles.chipRow}>
            {snapshot.dataset_summary.cohort_counts.map((cohort) => (
              <span key={cohort.cohort} className={styles.chip}>
                {cohort.cohort}: {cohort.case_count}
              </span>
            ))}
          </div>
        ) : null}
      </section>

      {snapshot.dataset_context || cohortNotes.length || bucketNotes.length ? (
        <section className={styles.section}>
          <div className={`${styles.grid} ${styles.gridTwo}`}>
            {snapshot.dataset_context ? (
              <article className={styles.card}>
                <h3 className={styles.cardTitle}>Dataset Framing</h3>
                {snapshot.dataset_context.dataset_description ? (
                  <p className={styles.cardText}>{snapshot.dataset_context.dataset_description}</p>
                ) : null}
                {snapshot.dataset_context.labeling_policy ? (
                  <>
                    <p className={styles.casebookMeta}>Labeling policy</p>
                    <p className={styles.cardText}>{snapshot.dataset_context.labeling_policy}</p>
                  </>
                ) : null}
                {snapshot.dataset_context.notes ? (
                  <>
                    <p className={styles.casebookMeta}>Notes</p>
                    <p className={styles.cardText}>{snapshot.dataset_context.notes}</p>
                  </>
                ) : null}
                {snapshot.dataset.manifest_path ? (
                  <p className={styles.casebookMeta}>
                    Manifest: <span className={styles.inlineCode}>{snapshot.dataset.manifest_path}</span>
                  </p>
                ) : null}
              </article>
            ) : null}

            {cohortNotes.length || bucketNotes.length ? (
              <article className={styles.card}>
                <h3 className={styles.cardTitle}>Benchmark Notes</h3>
                {cohortNotes.length ? (
                  <>
                    <p className={styles.casebookMeta}>Cohorts</p>
                    <ul className={styles.list}>
                      {cohortNotes.map((cohort) => (
                        <li key={cohort.cohort}>
                          {cohort.cohort}: {cohort.description}
                        </li>
                      ))}
                    </ul>
                  </>
                ) : null}
                {bucketNotes.length ? (
                  <>
                    <p className={styles.casebookMeta}>Buckets</p>
                    <ul className={styles.list}>
                      {bucketNotes.map((bucket) => (
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
              Current top-{snapshot.queue_preview.top_k} ranking for this checked-in external benchmark pack across its
              recorded cohorts.
            </p>
            <div className={styles.queueList}>
              {snapshot.queue_preview.external.map((queueEntry) => (
                <div key={`${descriptor.id}-${queueEntry.case_id}`} className={styles.queueItem}>
                  <div>
                    <p className={styles.queueItemTitle}>{renderQueueSummary(queueEntry)}</p>
                    <p className={styles.queueItemMeta}>{queueEntry.report_id}</p>
                  </div>
                  <p className={styles.queueItemScore}>{formatScore(queueEntry.score)}</p>
                </div>
              ))}
            </div>
          </article>
          <article className={styles.card}>
            <h3 className={styles.cardTitle}>Submission Framing</h3>
            <p className={styles.cardText}>{snapshot.sweep.recommendation.rationale}</p>
            {snapshot.submission?.notable_strengths?.length ? (
              <>
                <p className={styles.casebookMeta}>Notable strengths</p>
                <ul className={styles.list}>
                  {snapshot.submission.notable_strengths.map((strength) => (
                    <li key={strength}>{strength}</li>
                  ))}
                </ul>
              </>
            ) : null}
            {snapshot.submission?.known_limitations?.length ? (
              <>
                <p className={styles.casebookMeta}>Known limitations</p>
                <ul className={styles.list}>
                  {snapshot.submission.known_limitations.map((limitation) => (
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
            <h2 className={styles.sectionTitle}>Each external pack should keep its operating point explicit too.</h2>
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
                <th>Top-{snapshot.sweep.top_k} Sensitivity</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.sweep.points.map((point) => (
                <tr key={`${descriptor.id}-${point.threshold}`}>
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
            <h2 className={styles.sectionTitle}>Every checked-in external pack should stay inspectable, not just summarized.</h2>
            <p className={styles.sectionText}>
              Each entry keeps the report excerpt, reviewer focus, and actual external scoring outcome so follow-up misses
              and confounders stay visible as the published benchmark set grows.
            </p>
          </div>
        </div>

        <div className={styles.casebookGrid}>
          {snapshot.casebook.map((casebookEntry) => (
            <article key={`${descriptor.id}-${casebookEntry.case_id}`} className={styles.casebookCard}>
              <div className={styles.casebookHeader}>
                <div>
                  <p className={styles.casebookMeta}>{casebookEntry.report_id}</p>
                  <h3 className={styles.cardTitle}>{casebookEntry.case_id}</h3>
                </div>
                <span className={styles.casebookTag}>{casebookEntry.benchmark_bucket || "unbucketed"}</span>
              </div>

              <p className={styles.casebookFocus}>{casebookEntry.reviewer_focus || "No reviewer cue recorded."}</p>
              {casebookEntry.report_excerpt ? <p className={styles.casebookMeta}>{casebookEntry.report_excerpt}</p> : null}
              <p className={styles.casebookMeta}>{casebookEntry.label_notes || "No label note recorded."}</p>

              <div className={styles.miniChipRow}>
                {casebookEntry.cohort ? <span className={styles.miniChip}>Cohort: {casebookEntry.cohort}</span> : null}
                <span className={styles.miniChip}>
                  Expected positive: {formatBooleanLabel(casebookEntry.expected_positive)}
                </span>
                <span className={styles.miniChip}>
                  Expected escalation: {formatBooleanLabel(casebookEntry.expected_escalation)}
                </span>
                {casebookEntry.external.false_negative_bucket ? (
                  <span className={styles.miniChip}>Miss bucket: {casebookEntry.external.false_negative_bucket}</span>
                ) : null}
              </div>

              <p className={styles.casebookMeta}>
                Expected rationale cues:{" "}
                <span className={styles.inlineCode}>{formatCodeList(casebookEntry.expected_rationale_codes)}</span>
              </p>

              <div className={styles.resultCard}>
                <p className={styles.resultLabel}>External</p>
                <p className={styles.resultValue}>{formatOutcomeLabel(casebookEntry.external.outcome)}</p>
                <p className={styles.resultText}>{renderExternalModeSummary(casebookEntry.external)}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className={styles.section}>
        <div className={styles.codePanel}>
          <p className={styles.codeLabel}>Reproduce This</p>
          <h2 className={styles.codeTitle}>Each published external pack should survive a clean checkout too.</h2>
          <pre className={styles.codeBlock}>{reproduceCommands.join("\n")}</pre>
          <p className={styles.codeText}>
            Source files: <span className={styles.inlineCode}>{snapshot.dataset.labels_path}</span> and{" "}
            <span className={styles.inlineCode}>{snapshot.dataset.predictions_path}</span>.
          </p>
        </div>
      </section>
    </>
  );
}

export default async function ProofPage() {
  const demoSnapshot = await getDemoBenchmarkSnapshot();
  const externalBenchmarkEntries = await getPublishedExternalBenchmarkEntries();
  const configuredExternalBenchmarkEntries = externalBenchmarkEntries.length;
  const availableExternalBenchmarkEntries = externalBenchmarkEntries.filter(
    (entry): entry is PublishedExternalBenchmarkEntry & { snapshot: ExternalBenchmarkSnapshot } =>
      entry.snapshot !== null,
  );
  const missingExternalBenchmarkEntries =
    configuredExternalBenchmarkEntries - availableExternalBenchmarkEntries.length;

  if (!demoSnapshot && availableExternalBenchmarkEntries.length === 0) {
    return (
      <main className={styles.page}>
        <div className={styles.shell}>
          <section className={styles.warningCard}>
            <h1 className={styles.warningTitle}>Published benchmark snapshots not found</h1>
            <p className={styles.warningText}>
              Generate the checked-in proof artifacts with <span className={styles.inlineCode}>make refresh-demo-proof</span> and
              the registered external benchmark refresh commands, then reload this page.
            </p>
          </section>
        </div>
      </main>
    );
  }

  const missingArtifacts = [
    !demoSnapshot ? PUBLISHED_DEMO_PROOF_PATH : null,
    ...externalBenchmarkEntries
      .filter((entry) => entry.snapshot === null)
      .map((entry) => entry.descriptor.snapshot_path),
  ].filter((value): value is string => Boolean(value));

  return (
    <main className={styles.page}>
      <div className={styles.shell}>
        <section className={styles.hero}>
          <p className={styles.eyebrow}>Benchmark Proof</p>
          <h1 className={styles.title}>A reproducible proof surface, not a hand-wavy claim.</h1>
          <p className={styles.subtitle}>
            This page renders the synthetic demo comparison plus every checked-in external benchmark pack listed in the
            published registry. It exists so collaborators can inspect concrete evaluation deltas, queue behavior,
            reviewer-facing casebooks, and the exact commands needed to reproduce them.
          </p>
          <div className={styles.chipRow}>
            <span className={styles.chip}>Synthetic demo comparison</span>
            <span className={styles.chip}>Published external benchmark packs</span>
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
                <span className={styles.inlineCode}>make refresh-demo-proof</span>. External registry coverage is{" "}
                <strong>
                  {availableExternalBenchmarkEntries.length}/{configuredExternalBenchmarkEntries}
                </strong>{" "}
                published snapshots from <span className={styles.inlineCode}>{PUBLISHED_EXTERNAL_BENCHMARK_REGISTRY_PATH}</span>.
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

        {configuredExternalBenchmarkEntries ? (
          <section className={`${styles.section} ${styles.grid} ${styles.gridFour}`}>
            <article className={styles.card}>
              <p className={styles.statLabel}>Registry Entries</p>
              <p className={styles.statValue}>{configuredExternalBenchmarkEntries}</p>
              <p className={styles.statNote}>
                External benchmark packs currently configured in{" "}
                <span className={styles.inlineCode}>{PUBLISHED_EXTERNAL_BENCHMARK_REGISTRY_PATH}</span>.
              </p>
            </article>
            <article className={styles.card}>
              <p className={styles.statLabel}>Published Snapshots</p>
              <p className={styles.statValue}>{availableExternalBenchmarkEntries.length}</p>
              <p className={styles.statNote}>Registry entries with checked-in proof artifacts available to render.</p>
            </article>
            <article className={styles.card}>
              <p className={styles.statLabel}>Missing Snapshots</p>
              <p className={styles.statValue}>{missingExternalBenchmarkEntries}</p>
              <p className={styles.statNote}>Configured packs that still need their snapshot JSON published into the repo.</p>
            </article>
            <article className={styles.card}>
              <p className={styles.statLabel}>Registry Mode</p>
              <p className={styles.statValue}>Validated</p>
              <p className={styles.statNote}>
                Duplicate IDs and malformed snapshot paths now fail fast during the published proof load.
              </p>
            </article>
          </section>
        ) : null}

        {availableExternalBenchmarkEntries.map((entry) => (
          <ExternalBenchmarkProofSection key={entry.descriptor.id} entry={entry} />
        ))}
      </div>
    </main>
  );
}
