export default function AboutPage() {
  return (
    <main style={{ padding: 32, maxWidth: 900, margin: "0 auto" }}>
      <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#6b7280" }}>About</p>
      <h1 style={{ margin: "8px 0 12px", fontSize: 32 }}>Why this product exists</h1>
      <p style={{ lineHeight: 1.7 }}>
        Pancreatic Signal is designed as a triage aid for suspicious pancreatic radiology reports. It focuses on explainable
        report-level signals and a human review workflow rather than autonomous diagnosis.
      </p>
      <p style={{ lineHeight: 1.7 }}>
        This scaffold ships with documentation-first planning so implementation agents can progress in phases while keeping
        product boundaries and safety constraints intact.
      </p>
    </main>
  );
}
