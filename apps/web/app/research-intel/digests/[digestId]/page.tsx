import Link from "next/link";

import { getResearchDigest } from "../../../../lib/api";


function formatDateTime(value?: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}


export default async function ResearchDigestDetailPage({
  params,
}: {
  params: Promise<{ digestId: string }>;
}) {
  const { digestId } = await params;
  const digest = await getResearchDigest(digestId);

  if (!digest) {
    return (
      <main style={{ padding: 32 }}>
        <p>Digest not found.</p>
        <Link href="/research-intel/digests">Back to digests</Link>
      </main>
    );
  }

  return (
    <main style={{ padding: 32, maxWidth: 1040, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 20 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Research Intelligence digest</p>
          <h1 style={{ margin: "8px 0 0", fontSize: 32 }}>{digest.title}</h1>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <Link href="/research-intel/digests" style={{ color: "#2563eb" }}>Back to digests</Link>
          <Link href="/research-intel/opportunities" style={{ color: "#2563eb" }}>Opportunities</Link>
        </div>
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))" }}>
        <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
          <h2 style={{ marginTop: 0 }}>Published summary</h2>
          <pre
            style={{
              margin: 0,
              whiteSpace: "pre-wrap",
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
              lineHeight: 1.6,
              color: "#0f172a",
            }}
          >
            {digest.summary_markdown}
          </pre>
        </section>

        <section style={{ display: "grid", gap: 16 }}>
          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Summary</h2>
            <p><strong>Generated:</strong> {formatDateTime(digest.generated_at)}</p>
            <p><strong>Window:</strong> {formatDateTime(digest.window_start)} to {formatDateTime(digest.window_end)}</p>
            <p><strong>Topics:</strong> {digest.topic_labels.join(", ") || "unbucketed"}</p>
            <p><strong>Disagreement:</strong> {digest.disagreement_score.toFixed(2)}</p>
            <p><strong>Citations:</strong> {digest.citation_count}</p>
          </div>

          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Key takeaways</h2>
            <ul style={{ paddingLeft: 18, margin: 0 }}>
              {digest.key_takeaways.map((item) => (
                <li key={item} style={{ marginBottom: 8 }}>{item}</li>
              ))}
            </ul>
          </div>

          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Supporting documents</h2>
            <ul style={{ paddingLeft: 18, margin: 0 }}>
              {digest.supporting_documents.map((document) => (
                <li key={document.document_id} style={{ marginBottom: 10 }}>
                  <strong>{document.title}</strong> ({document.citation_key})
                  {document.topic_labels.length > 0 ? ` • ${document.topic_labels.join(", ")}` : ""}
                </li>
              ))}
            </ul>
          </div>
        </section>
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", marginTop: 16 }}>
        <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
          <h2 style={{ marginTop: 0 }}>Council stage 1</h2>
          <ul style={{ paddingLeft: 18, margin: 0 }}>
            {digest.council.stage_1.map((item) => (
              <li key={item.persona} style={{ marginBottom: 12 }}>
                <strong>{item.persona}</strong>: {item.summary}
              </li>
            ))}
          </ul>
        </section>

        <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
          <h2 style={{ marginTop: 0 }}>Council stage 2</h2>
          <ul style={{ paddingLeft: 18, margin: 0 }}>
            {digest.council.stage_2.map((item) => (
              <li key={item.persona} style={{ marginBottom: 12 }}>
                <strong>{item.persona}</strong>: {item.ranked_topics.join(", ")}. {item.critique}
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20, marginTop: 16 }}>
        <h2 style={{ marginTop: 0 }}>Chairman synthesis</h2>
        <p style={{ color: "#334155", lineHeight: 1.7 }}>{digest.council.stage_3.chairman_summary}</p>
        <p><strong>Consensus</strong></p>
        <ul style={{ paddingLeft: 18, marginTop: 0 }}>
          {digest.council.stage_3.consensus_points.map((item) => (
            <li key={item} style={{ marginBottom: 8 }}>{item}</li>
          ))}
        </ul>
        {digest.council.stage_3.disagreement_points.length > 0 ? (
          <>
            <p><strong>Disagreement</strong></p>
            <ul style={{ paddingLeft: 18, marginTop: 0 }}>
              {digest.council.stage_3.disagreement_points.map((item) => (
                <li key={item} style={{ marginBottom: 8 }}>{item}</li>
              ))}
            </ul>
          </>
        ) : null}
        <p><strong>Recommended actions</strong></p>
        <ul style={{ paddingLeft: 18, marginTop: 0, marginBottom: 0 }}>
          {digest.council.stage_3.recommended_actions.map((item) => (
            <li key={item} style={{ marginBottom: 8 }}>{item}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
