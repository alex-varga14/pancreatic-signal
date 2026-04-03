import Link from "next/link";

import { getResearchDocuments, getResearchSources, getResearchTopics } from "../../../lib/api";


function readSearchParam(value: string | string[] | undefined): string {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}


function formatDate(value?: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString("en-CA", { dateStyle: "medium" });
}


export default async function ResearchDocumentsPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const sourceKind = readSearchParam(resolvedSearchParams?.source_kind);
  const topic = readSearchParam(resolvedSearchParams?.topic);
  const q = readSearchParam(resolvedSearchParams?.q);

  const [documents, sources, topics] = await Promise.all([
    getResearchDocuments({ source_kind: sourceKind, topic, q, limit: 50 }),
    getResearchSources(),
    getResearchTopics(),
  ]);

  return (
    <main style={{ padding: 32, maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 20 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Research Intelligence</p>
          <h1 style={{ margin: "8px 0 0", fontSize: 32 }}>Document explorer</h1>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <Link href="/research-intel" style={{ color: "#2563eb" }}>Dashboard</Link>
          <Link href="/research-intel/digests" style={{ color: "#2563eb" }}>Digests</Link>
        </div>
      </div>

      <form
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 12,
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: 14,
          padding: 16,
          marginBottom: 16,
        }}
      >
        <input
          type="text"
          name="q"
          placeholder="Search title, abstract, or tags"
          defaultValue={q}
          style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px" }}
        />
        <select
          name="source_kind"
          defaultValue={sourceKind}
          style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
        >
          <option value="">All source kinds</option>
          {Array.from(new Set(sources.map((source) => source.source_kind))).map((value) => (
            <option key={value} value={value}>
              {value.replace(/_/g, " ")}
            </option>
          ))}
        </select>
        <select
          name="topic"
          defaultValue={topic}
          style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
        >
          <option value="">All topics</option>
          {topics.map((item) => (
            <option key={item.topic_id} value={item.topic_id}>
              {item.label}
            </option>
          ))}
        </select>
        <button
          type="submit"
          style={{
            border: 0,
            borderRadius: 8,
            padding: "10px 14px",
            background: "#0f172a",
            color: "white",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          Filter
        </button>
      </form>

      <div style={{ display: "grid", gap: 14 }}>
        {documents.length === 0 ? (
          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
            <p style={{ margin: 0, color: "#64748b" }}>No research documents matched the current filters.</p>
          </div>
        ) : (
          documents.map((document) => (
            <article key={document.document_id} style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", marginBottom: 8 }}>
                <div>
                  <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>
                    {document.source_label} • {document.source_kind}
                  </p>
                  <h2 style={{ margin: "6px 0 0", fontSize: 22 }}>{document.title}</h2>
                </div>
                <div style={{ color: "#475569", textAlign: "right" }}>
                  <div>{formatDate(document.published_at)}</div>
                  <div style={{ fontSize: 13 }}>{document.citation_key}</div>
                </div>
              </div>

              <p style={{ margin: "0 0 10px", color: "#334155", lineHeight: 1.7 }}>{document.abstract_text}</p>
              <p style={{ margin: "0 0 10px", color: "#64748b" }}>
                Topics: {document.topic_labels.join(", ") || "unbucketed"} • Entities: {document.entity_tags.join(", ") || "none"}
              </p>

              {document.evidence.length > 0 ? (
                <div style={{ marginBottom: 10 }}>
                  <p style={{ margin: "0 0 8px", fontWeight: 700 }}>Cited evidence</p>
                  <ul style={{ paddingLeft: 18, margin: 0 }}>
                    {document.evidence.slice(0, 3).map((item, index) => (
                      <li key={`${document.document_id}-${index}`} style={{ marginBottom: 8 }}>
                        <strong>{item.claim_type}</strong>: {item.evidence_text}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {document.url ? (
                <Link href={document.url} style={{ color: "#2563eb" }}>
                  Open source link
                </Link>
              ) : null}
            </article>
          ))
        )}
      </div>
    </main>
  );
}
