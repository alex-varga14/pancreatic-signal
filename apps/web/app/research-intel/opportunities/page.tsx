import Link from "next/link";
import type { CSSProperties } from "react";

import { getCurrentUser, getResearchOpportunities, getResearchTopics } from "../../../lib/api";
import { promoteResearchOpportunityAction, runResearchOpportunityExperimentAction } from "../actions";


const cardStyle: CSSProperties = {
  background: "white",
  border: "1px solid #e5e7eb",
  borderRadius: 14,
  padding: 20,
};

const chipStyle: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  borderRadius: 999,
  border: "1px solid #cbd5e1",
  background: "#f8fafc",
  color: "#0f172a",
  fontSize: 12,
  padding: "4px 10px",
  marginRight: 8,
  marginBottom: 8,
};


function readSearchParam(value: string | string[] | undefined): string {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}


function formatLabel(value: string): string {
  return value.replace(/_/g, " ");
}


function formatScore(value?: number | null): string {
  return value === undefined || value === null ? "n/a" : value.toFixed(2);
}


function experimentOptionsForType(opportunityType: string): Array<{ value: string; label: string }> {
  if (opportunityType === "benchmark_gap") {
    return [
      { value: "benchmark_readiness", label: "Benchmark readiness" },
      { value: "benchmark_stress_test", label: "Benchmark stress test" },
    ];
  }
  if (opportunityType === "rule_gap") {
    return [
      { value: "rule_explainability", label: "Rule explainability" },
      { value: "rule_stress_test", label: "Rule stress test" },
    ];
  }
  return [];
}


function ChipList({ items }: { items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div style={{ marginTop: 10 }}>
      {items.map((item) => (
        <span key={item} style={chipStyle}>
          {formatLabel(item)}
        </span>
      ))}
    </div>
  );
}


function SectionList({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  if (items.length === 0) return null;
  return (
    <div style={{ marginTop: 14 }}>
      <p style={{ margin: "0 0 8px", fontWeight: 700 }}>{title}</p>
      <ul style={{ paddingLeft: 18, margin: 0, color: "#334155" }}>
        {items.map((item) => (
          <li key={item} style={{ marginBottom: 8, lineHeight: 1.6 }}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
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
  const canExperiment = currentUser?.capabilities.can_manage_research_intel ?? false;

  return (
    <main style={{ padding: 32, maxWidth: 1120, margin: "0 auto" }}>
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
          <div style={cardStyle}>
            <p style={{ margin: 0, color: "#64748b" }}>No opportunities matched the current filters.</p>
          </div>
        ) : (
          opportunities.map((opportunity) => (
            <article key={opportunity.opportunity_id} style={cardStyle}>
              {(() => {
                const canRunExperiment =
                  canExperiment &&
                  ["benchmark_gap", "rule_gap"].includes(opportunity.opportunity_type);
                return (
                  <>
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
                    council {formatLabel(opportunity.action_payload.council_confidence)}
                  </div>
                </div>
              </div>

              <p style={{ margin: "0 0 10px", color: "#334155", lineHeight: 1.7 }}>{opportunity.summary}</p>
              <p style={{ margin: 0, color: "#0f172a", fontWeight: 700 }}>Objective</p>
              <p style={{ margin: "6px 0 0", color: "#334155", lineHeight: 1.7 }}>{opportunity.action_payload.objective}</p>
              <p style={{ margin: "10px 0 0", color: "#334155", lineHeight: 1.7 }}>
                <strong>Why now:</strong> {opportunity.action_payload.why_now}
              </p>
              <p style={{ margin: "10px 0 0", color: "#334155", lineHeight: 1.7 }}>
                <strong>Discovery question:</strong> {opportunity.action_payload.discovery_question}
              </p>

              <ChipList
                items={[
                  ...opportunity.topic_labels,
                  ...opportunity.action_payload.theme_snapshot,
                  opportunity.action_payload.artifact_spec.artifact_kind,
                ]}
              />

              <div style={{ marginTop: 14, padding: 14, borderRadius: 12, background: "#f8fafc", border: "1px solid #e2e8f0" }}>
                <p style={{ margin: 0, fontWeight: 700 }}>Suggested downstream artifact</p>
                <p style={{ margin: "8px 0 0", color: "#334155" }}>{opportunity.action_payload.artifact_spec.title}</p>
                <p style={{ margin: "8px 0 0", color: "#475569", lineHeight: 1.6 }}>
                  {opportunity.action_payload.artifact_spec.summary}
                </p>
                <p style={{ margin: "8px 0 0", color: "#475569" }}>
                  <strong>Target hint:</strong> {formatLabel(opportunity.action_payload.artifact_spec.target_hint || "docs_draft")}
                </p>
                {opportunity.action_payload.artifact_spec.suggested_path ? (
                  <p style={{ margin: "8px 0 0", color: "#475569" }}>
                    <strong>Suggested path:</strong> {opportunity.action_payload.artifact_spec.suggested_path}
                  </p>
                ) : null}
              </div>

              {opportunity.action_payload.evidence_bundle.length > 0 ? (
                <div style={{ marginTop: 14 }}>
                  <p style={{ margin: "0 0 8px", fontWeight: 700 }}>Evidence bundle</p>
                  <div style={{ display: "grid", gap: 10 }}>
                    {opportunity.action_payload.evidence_bundle.map((item) => (
                      <div key={item.document_id} style={{ border: "1px solid #e2e8f0", borderRadius: 10, padding: 12 }}>
                        <p style={{ margin: 0, color: "#0f172a" }}>
                          <strong>{item.citation_key}</strong> {item.title}
                        </p>
                        <p style={{ margin: "6px 0 0", color: "#475569", lineHeight: 1.6 }}>{item.why_it_matters}</p>
                        <p style={{ margin: "6px 0 0", color: "#64748b", fontSize: 13 }}>
                          {item.source_kind ? `${formatLabel(item.source_kind)} source` : "source unspecified"}
                          {item.topic_labels.length > 0 ? ` • ${item.topic_labels.join(", ")}` : ""}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              <div style={{ display: "grid", gap: 14, gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", marginTop: 14 }}>
                <SectionList title="Proposed steps" items={opportunity.action_payload.proposed_steps} />
                <SectionList title="Measurable outcomes" items={opportunity.action_payload.measurable_outcomes} />
                <SectionList title="Acceptance gates" items={opportunity.action_payload.acceptance_gates} />
                <SectionList title="Open questions" items={opportunity.action_payload.open_questions} />
                <SectionList title="Evidence gaps" items={opportunity.action_payload.evidence_gaps} />
                <SectionList title="Next experiments" items={opportunity.action_payload.next_experiments} />
                <SectionList title="Promotion guardrails" items={opportunity.action_payload.promotion_guardrails} />
              </div>

              {opportunity.action_payload.contributor_packets.length > 0 ? (
                <div style={{ marginTop: 14 }}>
                  <p style={{ margin: "0 0 8px", fontWeight: 700 }}>Contributor packets</p>
                  <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
                    {opportunity.action_payload.contributor_packets.map((packet) => (
                      <div
                        key={`${opportunity.opportunity_id}-${packet.packet_kind}`}
                        style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 14, background: "#f8fafc" }}
                      >
                        <p style={{ margin: 0, color: "#0f172a" }}>
                          <strong>{packet.title}</strong>
                        </p>
                        <p style={{ margin: "8px 0 0", color: "#475569", lineHeight: 1.6 }}>{packet.summary}</p>
                        <p style={{ margin: "8px 0 0", color: "#64748b", fontSize: 13 }}>
                          {formatLabel(packet.packet_kind)} • owner {packet.suggested_owner || "n/a"}
                        </p>
                        <SectionList title="Checklist" items={packet.checklist} />
                        <SectionList title="Repo targets" items={packet.repo_targets} />
                        <SectionList title="Expected outputs" items={packet.output_artifacts} />
                        <SectionList title="Validation steps" items={packet.validation_steps} />
                        <SectionList title="Handoff notes" items={packet.handoff_notes} />
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              <p style={{ margin: "14px 0 0", color: "#64748b" }}>
                Related rationale codes: {opportunity.related_rationale_codes.join(", ") || "none"} • related trial tags:{" "}
                {opportunity.related_trial_ids.join(", ") || "none"}
              </p>

              {opportunity.action_payload.last_experiment ? (
                <div style={{ marginTop: 14, padding: 14, borderRadius: 12, background: "#f8fafc", border: "1px solid #e2e8f0" }}>
                  <p style={{ margin: 0, fontWeight: 700 }}>Latest experiment</p>
                  <p style={{ margin: "8px 0 0", color: "#334155" }}>
                    <strong>{formatLabel(opportunity.action_payload.last_experiment.ratchet_outcome)}</strong> via{" "}
                    {formatLabel(opportunity.action_payload.last_experiment.experiment_kind || "proposal_validation")}
                  </p>
                  {opportunity.action_payload.last_experiment.experiment_summary ? (
                    <p style={{ margin: "8px 0 0", color: "#475569", lineHeight: 1.6 }}>
                      {opportunity.action_payload.last_experiment.experiment_summary}
                    </p>
                  ) : null}
                  <p style={{ margin: "8px 0 0", color: "#475569" }}>
                    {opportunity.action_payload.last_experiment.metric_name}: baseline{" "}
                    {formatScore(opportunity.action_payload.last_experiment.baseline_value)} • candidate{" "}
                    {formatScore(opportunity.action_payload.last_experiment.candidate_value)} • delta{" "}
                    {formatScore(opportunity.action_payload.last_experiment.delta)}
                  </p>
                  <p style={{ margin: "8px 0 0", color: "#475569" }}>
                    threshold {formatScore(opportunity.action_payload.last_experiment.threshold)} • min delta{" "}
                    {formatScore(opportunity.action_payload.last_experiment.min_delta)} • evidence coverage{" "}
                    {formatScore(opportunity.action_payload.last_experiment.evidence_coverage_score)}
                  </p>
                  {Object.keys(opportunity.action_payload.last_experiment.scored_dimensions).length > 0 ? (
                    <div style={{ marginTop: 10 }}>
                      <p style={{ margin: "0 0 8px", fontWeight: 700 }}>Scored dimensions</p>
                      <ul style={{ paddingLeft: 18, margin: 0, color: "#334155" }}>
                        {Object.entries(opportunity.action_payload.last_experiment.scored_dimensions).map(([label, value]) => (
                          <li key={label} style={{ marginBottom: 6 }}>
                            {formatLabel(label)}: {formatScore(value)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  <SectionList title="Experiment notes" items={opportunity.action_payload.last_experiment.notes} />
                  {opportunity.action_payload.last_experiment.artifact_paths.length > 0 ? (
                    <p style={{ margin: "10px 0 0", color: "#475569" }}>
                      Experiment artifacts: {opportunity.action_payload.last_experiment.artifact_paths.join(", ")}
                    </p>
                  ) : null}
                </div>
              ) : null}

              {canPromote && opportunity.status !== "promoted" ? (
                <form action={promoteResearchOpportunityAction} style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginTop: 14 }}>
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
                <div style={{ marginTop: 14 }}>
                  <p style={{ margin: 0, color: "#166534", fontWeight: 700 }}>
                    Promoted to {formatLabel(opportunity.promotion_target)}
                  </p>
                  {opportunity.action_payload.promotion_artifact_path ? (
                    <p style={{ margin: "6px 0 0", color: "#475569" }}>
                      Promotion artifact: {opportunity.action_payload.promotion_artifact_path}
                    </p>
                  ) : null}
                </div>
              ) : null}
              {canRunExperiment ? (
                <form action={runResearchOpportunityExperimentAction} style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginTop: 14 }}>
                  <input type="hidden" name="opportunity_id" value={opportunity.opportunity_id} />
                  <select
                    name="experiment_kind"
                    defaultValue={experimentOptionsForType(opportunity.opportunity_type)[0]?.value || ""}
                    style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
                  >
                    {experimentOptionsForType(opportunity.opportunity_type).map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  <button
                    type="submit"
                    style={{
                      border: "1px solid #cbd5e1",
                      borderRadius: 8,
                      padding: "10px 14px",
                      background: "white",
                      color: "#0f172a",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    Run experiment
                  </button>
                </form>
              ) : null}
                  </>
                );
              })()}
            </article>
          ))
        )}
      </div>
    </main>
  );
}
