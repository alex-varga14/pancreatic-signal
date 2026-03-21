import Link from "next/link";

export default function HomePage() {
  return (
    <main style={{ padding: 32, maxWidth: 1000, margin: "0 auto" }}>
      <div style={{ marginBottom: 24 }}>
        <p style={{ margin: 0, fontSize: 12, letterSpacing: 1, textTransform: "uppercase", color: "#6b7280" }}>
          Research-only
        </p>
        <h1 style={{ margin: "8px 0 12px", fontSize: 36 }}>Pancreatic Signal</h1>
        <p style={{ maxWidth: 700, lineHeight: 1.6 }}>
          Open-source workflow stack for identifying radiology reports suspicious for pancreatic malignancy or other high-risk
          pancreatic findings and routing them into a human-reviewed queue.
        </p>
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" }}>
        <Link href="/cases" style={{ background: "white", padding: 20, borderRadius: 12, border: "1px solid #e5e7eb" }}>
          <h2 style={{ marginTop: 0 }}>Worklist</h2>
          <p>View flagged cases, urgency bands, and top rationale codes.</p>
        </Link>
        <Link href="/about" style={{ background: "white", padding: 20, borderRadius: 12, border: "1px solid #e5e7eb" }}>
          <h2 style={{ marginTop: 0 }}>About</h2>
          <p>Read product intent, boundaries, and implementation phases.</p>
        </Link>
      </div>
    </main>
  );
}
