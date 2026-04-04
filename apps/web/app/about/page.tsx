import Link from "next/link";
import styles from "../marketing.module.css";

export default function AboutPage() {
  return (
    <main className={styles.page}>
      <div className={styles.shell}>
        <section className={styles.hero}>
          <p className={styles.eyebrow}>About Pancreatic Signal</p>
          <h1 className={styles.title}>An open pancreatic oncology discovery system with explainable workflow surfaces.</h1>
          <p className={styles.subtitle}>
            The product now leads with Research Intelligence: a cited discovery loop for pancreatic oncology literature,
            trials, guidance, and workflow gaps. Explainable triage, benchmarking, trial upkeep, and case briefs remain
            downstream applications of that discovery engine rather than separate black-box products.
          </p>
          <div className={styles.ctaRow}>
            <Link href="/research-intel" className={styles.primaryLink}>
              Open Research Intelligence
            </Link>
            <Link href="/proof" className={styles.secondaryLink}>
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
                An open-source pancreatic oncology discovery platform with cited monitoring, graph-backed clustering,
                council digests, opportunity specs, safe experiments, and applied workflow surfaces like triage and case
                briefs.
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
                The point is to make the citations, discovery logic, workflow assumptions, safety boundaries, and benchmark
                methods inspectable and improvable without hidden operational knowledge.
              </p>
            </article>
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <div>
              <p className={styles.eyebrow}>How The Pillars Fit</p>
              <h2 className={styles.sectionTitle}>Discovery first, workflow surfaces second.</h2>
            </div>
          </div>

          <div className={`${styles.grid} ${styles.gridThree}`}>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Research intelligence core</h3>
              <p className={styles.cardText}>
                Documents, graph entities, council deliberation, opportunities, and safe experiments form the primary system
                for understanding what pancreatic oncology signals matter right now.
              </p>
            </article>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Applied workflow surfaces</h3>
              <p className={styles.cardText}>
                Explainable report triage, benchmark proof, trial upkeep, and case briefs turn the discovery loop into
                concrete tools without hiding evidence or removing the human reviewer.
              </p>
            </article>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Contributor loop</h3>
              <p className={styles.cardText}>
                Opportunity specs, benchmark packs, import adapters, and safe experiment gates give contributors a visible,
                citation-backed path from discovery to implementation.
              </p>
            </article>
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.sectionHeader}>
            <div>
              <p className={styles.eyebrow}>Intended Users</p>
              <h2 className={styles.sectionTitle}>Built for the people doing the research and the follow-through.</h2>
            </div>
          </div>

          <div className={`${styles.grid} ${styles.gridThree}`}>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Research operators and contributors</h3>
              <p className={styles.cardText}>
                Track pancreatic oncology movement, challenge interpretations, publish cited digests, and turn findings into
                benchmark, rule, or tooling proposals.
              </p>
            </article>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Navigators and coordinators</h3>
              <p className={styles.cardText}>
                Use the explainable triage surface to prioritize suspicious cases, review why they were flagged, and record
                escalation, dismissal, or follow-up decisions with an audit trail.
              </p>
            </article>
            <article className={styles.card}>
              <h3 className={styles.cardTitle}>Informatics and software teams</h3>
              <p className={styles.cardText}>
                Test CSV, JSONL, FHIR, and HL7 ingestion paths while preserving auth, site scope, de-identification, and
                audit visibility across research and workflow surfaces.
              </p>
            </article>
          </div>
        </section>

        <section className={styles.section}>
          <div className={styles.warningCard}>
            <h3 className={styles.warningTitle}>Safety posture</h3>
            <p className={styles.warningText}>
              Every strong version of this project should keep citations visible, preserve the evidence behind every claim or
              flag, show uncertainty rather than hide it, and keep the human reviewer or operator visibly in the loop.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
