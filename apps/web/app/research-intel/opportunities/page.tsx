import Link from "next/link";

import { getCurrentUser, getResearchOpportunities, getResearchTopics } from "../../../lib/api";
import { promoteResearchOpportunityAction } from "../actions";


function readSearchParam(value: string | string[] | undefined): string {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}


function formatLabel(value: string): string {
  return value.replace(/_/g, " ");
}


export default async function ResearchOpportunitiesPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const opportunityType = readSearchParam(resolvedSearchParams?.opportunity_type);
  const status = readSearchParam(resolvedSearchParams?.status);
  const topic = readSearchParam(resolvedSearchParams?.topic);

  const [currentUser, opportunities, topics] = await Promise.all([
    getCurrentUser(),
    getResearchOpportunities({
      opportunity_type: opportunityType,
      status,
      topic,
    }),
    getResearchTopics(),
  ]);

  const canPromote = currentUser?.capabilities.can_promote_research_intel ?? false;

  return (
    <main style={{ padding: 32, maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 20 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Research Intelligence</p>
          <h1 style={{ margin: "8px 0 0", fontSize: 32 }}>Opportunity board</h1>
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
        <select
          name="opportunity_type"
          defaultValue={opportunityType}
          style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
        >
          <option value="">All opportunity types</option>
          {[
            "rule_gap",
            "benchmark_gap",
            "trial_catalog_gap",
            "case_brief",
            "community_project",
            "external_tooling",
          ].map((value) => (
            <option key={value} value={value}>
              {formatLabel(value)}
            </option>
          ))}
        </select>
        <select
          name="status"
          defaultValue={status}
          style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
        >
          <option value="">All statuses</option>
          {["proposed", "promoted"].map((value) => (
            <option key={value} value={value}>
              {formatLabel(value)}
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
        {opportunities.length === 0 ? (
          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
            <p style={{ margin: 0, color: "#64748b" }}>No opportunities matched the current filters.</p>
          </div>
        ) : (
          opportunities.map((opportunity) => (
            <article key={opportunity.opportunity_id} style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 14, padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap", marginBottom: 10 }}>
                <div>
                  <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>
                    {formatLabel(opportunity.opportunity_type)} • {formatLabel(opportunity.status)}
                  </p>
                  <h2 style={{ margin: "6px 0 0", fontSize: 22 }}>{opportunity.title}</h2>
                </div>
                <div style={{ color: "#475569", textAlign: "right" }}>
                  <div>confidence {(opportunity.confidence_score * 100).toFixed(0)}%</div>
                  <div style={{ fontSize: 13 }}>
                    {opportunity.topic_labels.join(", ") || "unbucketed"}
                  </div>
                </div>
              </div>

              <p style={{ margin: "0 0 10px", color: "#334155", lineHeight: 1.7 }}>{opportunity.summary}</p>
              <p style={{ margin: "0 0 10px", color: "#64748b" }}>
                Related rationale codes: {opportunity.related_rationale_codes.join(", ") || "none"} • related trial tags:{" "}
                {opportunity.related_trial_ids.join(", ") || "none"}
              </p>

              {Array.isArray(opportunity.action_payload.acceptance_gates) ? (
                <div style={{ marginBottom: 10 }}>
                  <p style={{ margin: "0 0 8px", fontWeight: 700 }}>Acceptance gates</p>
                  <ul style={{ paddingLeft: 18, margin: 0 }}>
                    {(opportunity.action_payload.acceptance_gates as string[]).map((gate) => (
                      <li key={gate} style={{ marginBottom: 8 }}>{gate}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {canPromote && opportunity.status !== "promoted" ? (
                <form action={promoteResearchOpportunityAction} style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                  <input type="hidden" name="opportunity_id" value={opportunity.opportunity_id} />
                  <select
                    name="target"
                    defaultValue={String(opportunity.action_payload.suggested_target || "docs_draft")}
                    style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
                  >
                    <option value="docs_draft">Docs draft</option>
                    <option value="benchmark_task">Benchmark task</option>
                    <option value="github_issue">GitHub issue</option>
                  </select>
                  <button
                    type="submit"
                    style={{
                      border: 0,
                      borderRadius: 8,
                      padding: "10px 14px",
                      background: "#1d4ed8",
                      color: "white",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    Promote
                  </button>
                </form>
              ) : opportunity.promotion_target ? (
                <p style={{ margin: 0, color: "#166534", fontWeight: 700 }}>
                  Promoted to {formatLabel(opportunity.promotion_target)}
                </p>
              ) : null}
            </article>
          ))
        )}
      </div>
    </main>
  );
}
