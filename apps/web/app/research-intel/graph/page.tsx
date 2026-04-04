import Link from "next/link";

import { getResearchGraph } from "../../../lib/api";


export default async function ResearchGraphPage() {
  const graph = await getResearchGraph();
  const activeNodes = (graph?.nodes || []).filter((node) => node.document_count > 0);
  const edgeMap = new Map((graph?.nodes || []).map((node) => [node.node_id, node.label]));

  return (
    <main style={{ padding: 32, maxWidth: 1160, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 20 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Research Intelligence</p>
          <h1 style={{ margin: "8px 0 0", fontSize: 32 }}>Knowledge graph</h1>
          <p style={{ margin: "8px 0 0", color: "#475569", maxWidth: 780, lineHeight: 1.7 }}>
            The entity layer linking pancreatic oncology diseases, biomarkers, procedures, cohorts, workflow concepts,
            and research artifacts. Active nodes are derived from ingested documents and set up later council and
            discovery-to-action work.
          </p>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <Link href="/research-intel" style={{ color: "#2563eb" }}>
            Dashboard
          </Link>
          <Link href="/research-intel/documents" style={{ color: "#2563eb" }}>
            Documents
          </Link>
        </div>
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", marginBottom: 16 }}>
        <SummaryCard label="Graph nodes" value={String(graph?.nodes.length || 0)} note="Typed pancreatic oncology entities" />
        <SummaryCard label="Graph edges" value={String(graph?.edges.length || 0)} note="Cross-entity scientific relationships" />
        <SummaryCard label="Active nodes" value={String(activeNodes.length)} note="Entities grounded in current document evidence" />
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "minmax(0, 2fr) minmax(320px, 1fr)" }}>
        <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
          <div style={{ marginBottom: 12 }}>
            <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Active nodes</p>
            <h2 style={{ margin: "6px 0 0", fontSize: 24 }}>Graph-backed discovery surface</h2>
          </div>

          {activeNodes.length === 0 ? (
            <p style={{ marginBottom: 0, color: "#64748b" }}>No graph activity yet.</p>
          ) : (
            <div style={{ display: "grid", gap: 12 }}>
              {activeNodes.map((node) => (
                <div key={node.node_id} style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 16 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 6 }}>
                    <strong>{node.label}</strong>
                    <span style={{ fontSize: 12, color: "#1d4ed8", fontWeight: 700 }}>
                      {node.document_count} doc{node.document_count === 1 ? "" : "s"}
                    </span>
                  </div>
                  <p style={{ margin: "0 0 8px", color: "#475569" }}>{node.description}</p>
                  <p style={{ margin: "0 0 8px", color: "#64748b", fontSize: 13 }}>
                    {node.node_type.replace(/_/g, " ")} • heat {node.heat.toFixed(2)} • topics {node.topic_ids.join(", ") || "none"}
                  </p>
                  <p style={{ margin: 0, color: "#64748b", fontSize: 13 }}>
                    Related nodes:{" "}
                    {node.related_node_ids.map((relatedId) => edgeMap.get(relatedId) || relatedId).join(", ") || "none"}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>

        <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
          <div style={{ marginBottom: 12 }}>
            <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Relationships</p>
            <h2 style={{ margin: "6px 0 0", fontSize: 24 }}>Current graph edges</h2>
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            {(graph?.edges || []).map((edge, index) => (
              <div key={`${edge.source}-${edge.target}-${index}`} style={{ borderBottom: "1px solid #e2e8f0", paddingBottom: 10 }}>
                <p style={{ margin: 0, fontWeight: 700 }}>
                  {edgeMap.get(edge.source) || edge.source} → {edgeMap.get(edge.target) || edge.target}
                </p>
                <p style={{ margin: "4px 0 0", color: "#64748b", fontSize: 13 }}>
                  {edge.relation.replace(/_/g, " ")}{typeof edge.weight === "number" ? ` • weight ${edge.weight.toFixed(2)}` : ""}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}


function SummaryCard({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 18 }}>
      <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>{label}</p>
      <p style={{ margin: "8px 0 6px", fontSize: 30, fontWeight: 800 }}>{value}</p>
      <p style={{ margin: 0, color: "#64748b" }}>{note}</p>
    </div>
  );
}
