import Link from "next/link";

import { getResearchDigests } from "../../../lib/api";


function formatDateTime(value?: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}


function formatSignedNumber(value?: number | null): string {
  if (value === undefined || value === null) return "n/a";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;
}


function formatSignedInteger(value?: number | null): string {
  if (value === undefined || value === null) return "n/a";
  return `${value >= 0 ? "+" : ""}${value}`;
}


export default async function ResearchDigestsPage() {
  const digests = await getResearchDigests();

  return (
    <main style={{ padding: 32, maxWidth: 1000, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 20 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Research Intelligence</p>
          <h1 style={{ margin: "8px 0 0", fontSize: 32 }}>Digest archive</h1>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <Link href="/research-intel" style={{ color: "#2563eb" }}>Dashboard</Link>
          <Link href="/research-intel/opportunities" style={{ color: "#2563eb" }}>Opportunities</Link>
        </div>
      </div>

      <div style={{ display: "grid", gap: 14 }}>
        {digests.length === 0 ? (
          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
            <p style={{ margin: 0, color: "#64748b" }}>No digests have been generated yet.</p>
          </div>
        ) : (
          digests.map((digest) => (
            <article key={digest.digest_id} style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap", marginBottom: 10 }}>
                <div>
                  <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>
                    {digest.status} • {digest.publication_scope}
                  </p>
                  <h2 style={{ margin: "6px 0 0", fontSize: 24 }}>{digest.title}</h2>
                </div>
                <div style={{ color: "#475569", textAlign: "right" }}>
                  <div>{formatDateTime(digest.generated_at)}</div>
                  <div style={{ fontSize: 13 }}>
                    disagreement {digest.disagreement_score.toFixed(2)} • citations {digest.citation_count}
                  </div>
                </div>
              </div>

              <p style={{ margin: "0 0 12px", color: "#475569" }}>
                Topics: {digest.topic_labels.join(", ") || "unbucketed"}
              </p>
              <p style={{ margin: "0 0 12px", color: "#334155", lineHeight: 1.6 }}>
                Across runs: {digest.trend.confidence_trend}
                {digest.trend.previous_digest_id ? ` from ${digest.trend.previous_digest_id}` : ""}
                {" • "}disagreement {formatSignedNumber(digest.trend.disagreement_delta)}
                {" • "}citations {formatSignedInteger(digest.trend.citation_delta)}
              </p>
              {digest.trend.new_topic_labels.length > 0 ? (
                <p style={{ margin: "0 0 12px", color: "#475569" }}>
                  New topics: {digest.trend.new_topic_labels.join(", ")}
                </p>
              ) : null}
              <Link href={`/research-intel/digests/${digest.digest_id}`} style={{ color: "#2563eb" }}>
                Open full digest
              </Link>
            </article>
          ))
        )}
      </div>
    </main>
  );
}
