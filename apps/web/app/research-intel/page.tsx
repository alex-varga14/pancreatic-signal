import Link from "next/link";

import {
  getCurrentUser,
  getResearchDigests,
  getResearchDocuments,
  getResearchOpportunities,
  getResearchRuns,
  getResearchSources,
  getResearchTopics,
} from "../../lib/api";
import { triggerResearchDigestAction, triggerResearchIngestAction } from "./actions";


function formatDateTime(value?: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}


function formatLabel(value: string): string {
  return value.replace(/_/g, " ");
}


export default async function ResearchIntelPage() {
  const [currentUser, sources, topics, digests, opportunities, runs, documents] = await Promise.all([
    getCurrentUser(),
    getResearchSources(),
    getResearchTopics(),
    getResearchDigests(),
    getResearchOpportunities(),
    getResearchRuns(6),
    getResearchDocuments({ limit: 5 }),
  ]);

  const canManage = currentUser?.capabilities.can_manage_research_intel ?? false;
  const latestRun = runs[0] ?? null;
  const publishedDigest = digests[0] ?? null;
  const hottestTopics = topics.slice(0, 4);
  const topOpportunities = opportunities.slice(0, 4);

  return (
    <main style={{ padding: 32, maxWidth: 1160, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap", marginBottom: 20 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#0f766e" }}>
            Research Intelligence
          </p>
          <h1 style={{ margin: "8px 0 0", fontSize: 34 }}>Pancreatic oncology watchtower</h1>
          <p style={{ maxWidth: 760, color: "#475569", lineHeight: 1.7 }}>
            A sibling workspace for cited pancreatic oncology monitoring, topic clustering, council digests, and
            open-source opportunity planning. It feeds benchmark, trial-catalog, and case-brief work without changing
            triage scores automatically.
          </p>
        </div>

        <div style={{ display: "flex", gap: 12, alignItems: "start", flexWrap: "wrap" }}>
          {canManage ? (
            <>
              <form action={triggerResearchIngestAction}>
                <button
                  type="submit"
                  style={{
                    border: 0,
                    borderRadius: 10,
                    padding: "10px 14px",
                    background: "#0f172a",
                    color: "white",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  Run ingest
                </button>
              </form>
              <form action={triggerResearchDigestAction}>
                <button
                  type="submit"
                  style={{
                    border: 0,
                    borderRadius: 10,
                    padding: "10px 14px",
                    background: "#1d4ed8",
                    color: "white",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  Build digest
                </button>
              </form>
            </>
          ) : null}
          <Link href="/cases" style={{ color: "#2563eb" }}>
            Open worklist
          </Link>
          <Link href="/" style={{ color: "#2563eb" }}>
            Back
          </Link>
        </div>
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginBottom: 16 }}>
        <StatCard label="Tracked sources" value={String(sources.length)} note="Curated public source connectors" />
        <StatCard label="Topic watchlists" value={String(topics.length)} note="Rolling pancreatic oncology clusters" />
        <StatCard label="Published digests" value={String(digests.length)} note="Cited summaries with council output" />
        <StatCard label="Open opportunities" value={String(opportunities.length)} note="Human-gated proposals for next work" />
      </div>

      <div
        style={{
          background: "linear-gradient(135deg, #f0fdfa, #eff6ff)",
          border: "1px solid #bae6fd",
          borderRadius: 14,
          padding: 20,
          marginBottom: 16,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
          <div>
            <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#0f766e" }}>Latest activity</p>
            <h2 style={{ margin: "8px 0 10px", fontSize: 24 }}>
              {latestRun ? `Last ${latestRun.run_type} run completed ${formatDateTime(latestRun.completed_at)}` : "No research runs yet"}
            </h2>
            <p style={{ margin: 0, color: "#334155" }}>
              {latestRun
                ? `Processed ${latestRun.processed} items across ${latestRun.source_scope.length} source bucket(s).`
                : "Trigger the seeded ingest to load the local pancreatic oncology watch catalog, then build a digest to surface opportunities."}
            </p>
          </div>
          {publishedDigest ? (
            <div style={{ minWidth: 280, background: "white", borderRadius: 12, padding: 16, border: "1px solid #dbeafe" }}>
              <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#1d4ed8" }}>Current digest</p>
              <h3 style={{ margin: "8px 0", fontSize: 18 }}>{publishedDigest.title}</h3>
              <p style={{ margin: "0 0 8px", color: "#475569" }}>
                Disagreement {publishedDigest.disagreement_score.toFixed(2)} • citations {publishedDigest.citation_count}
              </p>
              <Link href={`/research-intel/digests/${publishedDigest.digest_id}`} style={{ color: "#2563eb" }}>
                Open digest
              </Link>
            </div>
          ) : null}
        </div>
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", marginBottom: 16 }}>
        <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 12 }}>
            <div>
              <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Topic heat</p>
              <h2 style={{ margin: "6px 0 0", fontSize: 22 }}>Watchlists shaping next work</h2>
            </div>
            <Link href="/research-intel/documents" style={{ color: "#2563eb" }}>
              Explore documents
            </Link>
          </div>

          {hottestTopics.length === 0 ? (
            <p style={{ marginBottom: 0, color: "#64748b" }}>No topic activity yet.</p>
          ) : (
            <div style={{ display: "grid", gap: 12 }}>
              {hottestTopics.map((topic) => (
                <div key={topic.topic_id} style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 14, background: "#f8fafc" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 6 }}>
                    <strong>{topic.label}</strong>
                    <span style={{ fontSize: 12, color: "#0f766e", fontWeight: 700 }}>
                      heat {topic.topic_heat.toFixed(2)}
                    </span>
                  </div>
                  <p style={{ margin: "0 0 8px", color: "#475569" }}>{topic.description}</p>
                  <p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>
                    {topic.document_count} document{topic.document_count === 1 ? "" : "s"} • last seen {formatDateTime(topic.last_document_at)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>

        <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 12 }}>
            <div>
              <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Opportunity board</p>
              <h2 style={{ margin: "6px 0 0", fontSize: 22 }}>Human-gated next steps</h2>
            </div>
            <Link href="/research-intel/opportunities" style={{ color: "#2563eb" }}>
              Open board
            </Link>
          </div>

          {topOpportunities.length === 0 ? (
            <p style={{ marginBottom: 0, color: "#64748b" }}>No opportunities published yet.</p>
          ) : (
            <div style={{ display: "grid", gap: 12 }}>
              {topOpportunities.map((opportunity) => (
                <div key={opportunity.opportunity_id} style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 14 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 6 }}>
                    <strong>{opportunity.title}</strong>
                    <span style={{ color: "#1d4ed8", fontSize: 12, fontWeight: 700 }}>
                      {formatLabel(opportunity.opportunity_type)}
                    </span>
                  </div>
                  <p style={{ margin: "0 0 8px", color: "#475569" }}>{opportunity.summary}</p>
                  <p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>
                    confidence {(opportunity.confidence_score * 100).toFixed(0)}% • {opportunity.topic_labels.join(", ") || "unbucketed"}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))" }}>
        <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 12 }}>
            <div>
              <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Recent documents</p>
              <h2 style={{ margin: "6px 0 0", fontSize: 22 }}>Cited source stream</h2>
            </div>
            <Link href="/research-intel/documents" style={{ color: "#2563eb" }}>
              Document explorer
            </Link>
          </div>

          {documents.length === 0 ? (
            <p style={{ marginBottom: 0, color: "#64748b" }}>No documents ingested yet.</p>
          ) : (
            <div style={{ display: "grid", gap: 12 }}>
              {documents.map((document) => (
                <div key={document.document_id} style={{ borderBottom: "1px solid #e2e8f0", paddingBottom: 12 }}>
                  <p style={{ margin: 0, fontSize: 12, color: "#64748b" }}>
                    {document.source_label} • {formatDateTime(document.published_at)}
                  </p>
                  <h3 style={{ margin: "6px 0", fontSize: 18 }}>{document.title}</h3>
                  <p style={{ margin: "0 0 8px", color: "#475569" }}>{document.abstract_text}</p>
                  <p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>
                    {document.citation_key} • {document.topic_labels.join(", ") || "unbucketed"}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>

        <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 12 }}>
            <div>
              <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Tracked sources</p>
              <h2 style={{ margin: "6px 0 0", fontSize: 22 }}>Connector registry</h2>
            </div>
            <Link href="/research-intel/digests" style={{ color: "#2563eb" }}>
              Digest archive
            </Link>
          </div>

          <div style={{ display: "grid", gap: 12 }}>
            {sources.map((source) => (
              <div key={source.source_id} style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 14, background: "#f8fafc" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginBottom: 6 }}>
                  <strong>{source.label}</strong>
                  <span style={{ fontSize: 12, color: source.enabled ? "#166534" : "#64748b", fontWeight: 700 }}>
                    {source.enabled ? "enabled" : "disabled"}
                  </span>
                </div>
                <p style={{ margin: "0 0 6px", color: "#475569" }}>{source.description}</p>
                <p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>
                  {formatLabel(source.source_kind)} • {formatLabel(source.trust_level)} trust • every{" "}
                  {String(source.polling_config.interval_hours || "—")}h
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}


function StatCard({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 18 }}>
      <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>{label}</p>
      <p style={{ margin: "8px 0 6px", fontSize: 30, fontWeight: 800 }}>{value}</p>
      <p style={{ margin: 0, color: "#64748b" }}>{note}</p>
    </div>
  );
}
