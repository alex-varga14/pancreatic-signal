import Link from "next/link";
import styles from "../marketing.module.css";

export default function AboutPage() {
  return (
    <main className={styles.page}>
      <div className={styles.shell}>
        <section className={styles.hero}>
          <p className={styles.eyebrow}>About Pancreatic Signal</p>
          <h1 className={styles.title}>A workflow layer for suspicious pancreatic report follow-up.</h1>
          <p className={styles.subtitle}>
            The product targets the operational gap between imaging interpretation and timely follow-up. It emphasizes
            explainable report-level signals, human review, and reproducible benchmarking rather than autonomous diagnosis.
          </p>
          <div className={styles.ctaRow}>
            <Link href="/proof" className={styles.primaryLink}>
              See Benchmark Proof
            </Link>
            <Link href="/" className={styles.secondaryLink}>
              Back Home
            </Link>
          </div>
        </section>

        <section className={styles.section}>
          <div className={`${styles.grid} ${styles.gridThree}`}>
            <article className={styles.card}>
              <h2 className={styles.cardTitle}>What it is</h2>
              <p className={styles.cardText}>
                An open-source, research-first triage stack for suspicious pancreatic radiology reports with evidence spans,
                rationale codes, reviewer workflow, imports, exports, and benchmark helpers.
              </p>
            </article>
            <article className={styles.card}>
              <h2 className={styles.cardTitle}>What it is not</h2>
              <p className={styles.cardText}>
                It is not autonomous diagnosis, treatment advice, unsupervised production hospital deployment guidance, or a
                substitute for radiologist and navigator review.
              </p>
            </article>
            <article className={styles.card}>
              <h2 className={styles.cardTitle}>Why open source</h2>
              <p className={styles.cardText}>
                The point is to make the logic, workflow assumptions, safety boundaries, and benchmark methods inspectable and
                improvable without hidden operational knowledge.
              </p>
            </article>
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <div>
              <p className={styles.eyebrow}>Intended Users</p>
              <h2 className={styles.sectionTitle}>Built for the people who close the follow-up loop.</h2>
            </div>
          </div>

          <div className={`${styles.grid} ${styles.gridThree}`}>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Navigators and coordinators</h3>
              <p className={styles.cardText}>
                Prioritize suspicious cases, review why they were flagged, and record escalation, dismissal, or follow-up
                decisions with an audit trail.
              </p>
            </article>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Researchers and quality teams</h3>
              <p className={styles.cardText}>
                Run retrospective datasets through a transparent baseline, compare thresholds, and inspect false negatives by
                rationale family.
              </p>
            </article>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Informatics and software teams</h3>
              <p className={styles.cardText}>
                Test CSV, JSONL, FHIR, and HL7 ingestion paths while preserving auth, site scope, de-identification, and audit
                visibility.
              </p>
            </article>
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.warningCard}>
            <h3 className={styles.warningTitle}>Safety posture</h3>
            <p className={styles.warningText}>
              Every strong version of this project should keep the raw report text, expose the evidence behind a flag, show
              uncertainty rather than hide it, and keep the human reviewer visibly in the loop.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
