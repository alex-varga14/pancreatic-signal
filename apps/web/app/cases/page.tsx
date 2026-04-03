import Link from "next/link";
import { getCases, getCurrentUser, getEvaluationComparison, getEvaluationSweep, getFeedbackSummary } from "../../lib/api";

const STATUS_OPTIONS = ["new", "in_review", "escalated", "dismissed", "closed"];
const URGENCY_OPTIONS = ["low", "medium", "high", "critical"];
const MODALITY_OPTIONS = ["CT", "MRI"];
const HYBRID_REVIEW_OPTIONS = ["expedite", "review", "defer"];
const ACTIVE_LEARNING_OPTIONS = ["high", "medium", "low"];
const FEEDBACK_LABEL_OPTIONS = [
  "true_positive",
  "false_positive",
  "actionable_followup",
  "benign",
  "uncertain",
];
const SORT_OPTIONS = [
  { value: "score", label: "Highest score" },
  { value: "hybrid_score", label: "Highest hybrid score" },
  { value: "hybrid_delta", label: "Largest hybrid uplift" },
  { value: "review_feedback_count", label: "Most feedback" },
  { value: "urgency", label: "Highest urgency" },
  { value: "report_datetime", label: "Most recent" },
  { value: "case_id", label: "Case ID" },
];
const SORT_DIRECTION_OPTIONS = [
  { value: "desc", label: "Descending" },
  { value: "asc", label: "Ascending" },
];

function readSearchParam(value: string | string[] | undefined): string {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

function readBoolSearchParam(value: string | string[] | undefined): boolean {
  const normalized = readSearchParam(value).toLowerCase();
  return normalized === "1" || normalized === "true" || normalized === "on" || normalized === "yes";
}

function formatReportedAt(value?: string | null): string {
  if (!value) return "—";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;

  return parsed.toLocaleString("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatLabel(value?: string | null): string {
  if (!value) return "—";
  return value.replace(/_/g, " ");
}

function badgeStyle(value?: string | null): { background: string; color: string } {
  if (value === "high" || value === "critical" || value === "expedite") {
    return { background: "#fee2e2", color: "#991b1b" };
  }
  if (value === "medium" || value === "review") {
    return { background: "#fef3c7", color: "#92400e" };
  }
  if (value === "borderline") {
    return { background: "#e0f2fe", color: "#075985" };
  }
  return { background: "#e2e8f0", color: "#475569" };
}

function formatDelta(value?: number | null): string {
  if (value === undefined || value === null) return "—";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;
}

function formatSiteScope(value?: string[] | null): string {
  if (!value || value.length === 0) return "all sites";
  return value.join(", ");
}

export default async function CasesPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const status = readSearchParam(resolvedSearchParams?.status);
  const urgency = readSearchParam(resolvedSearchParams?.urgency);
  const site = readSearchParam(resolvedSearchParams?.site);
  const reviewer = readSearchParam(resolvedSearchParams?.reviewer);
  const modality = readSearchParam(resolvedSearchParams?.modality);
  const rationale = readSearchParam(resolvedSearchParams?.rationale);
  const feedbackLabel = readSearchParam(resolvedSearchParams?.feedback_label);
  const needsFeedback = readBoolSearchParam(resolvedSearchParams?.needs_feedback);
  const disagreementOnly = readBoolSearchParam(resolvedSearchParams?.disagreement_only);
  const hybridDeltaMin = readSearchParam(resolvedSearchParams?.hybrid_delta_min);
  const hybridReviewPriority = readSearchParam(resolvedSearchParams?.hybrid_review_priority);
  const activeLearningPriority = readSearchParam(resolvedSearchParams?.active_learning_priority);
  const activeLearningOnly = readBoolSearchParam(resolvedSearchParams?.active_learning_only);
  const q = readSearchParam(resolvedSearchParams?.q);
  const sortBy = readSearchParam(resolvedSearchParams?.sort_by) || "score";
  const sortDir = readSearchParam(resolvedSearchParams?.sort_dir) || "desc";

  const [cases, evaluationComparison, evaluationSweep, feedbackSummary, currentUser] = await Promise.all([
    getCases({
      status,
      urgency,
      site,
      reviewer,
      modality,
      rationale,
      feedback_label: feedbackLabel,
      needs_feedback: needsFeedback,
      disagreement_only: disagreementOnly,
      hybrid_delta_min: hybridDeltaMin ? Number(hybridDeltaMin) : undefined,
      hybrid_review_priority: hybridReviewPriority,
      active_learning_priority: activeLearningPriority,
      active_learning_only: activeLearningOnly,
      include_hybrid: true,
      q,
      sort_by: sortBy,
      sort_dir: sortDir,
    }),
    getEvaluationComparison(),
    getEvaluationSweep(),
    getFeedbackSummary(),
    getCurrentUser(),
  ]);
  const hasActiveFilters = Boolean(
    status ||
      urgency ||
      site ||
      reviewer ||
      modality ||
      rationale ||
      feedbackLabel ||
      needsFeedback ||
      disagreementOnly ||
      hybridDeltaMin ||
      hybridReviewPriority ||
      activeLearningPriority ||
      activeLearningOnly ||
      q ||
      sortBy !== "score" ||
      sortDir !== "desc"
  );
  const expediteCount = cases.filter((item) => item.hybrid_review_priority === "expedite").length;
  const activeLearningCount = cases.filter((item) => item.active_learning_priority === "high").length;
  const disagreementCount = cases.filter((item) => item.disagreement_level === "high").length;
  const bestSweepPoint =
    evaluationSweep?.points.reduce<typeof evaluationSweep.points[number] | null>(
      (best, point) => (!best || point.f1_delta > best.f1_delta ? point : best),
      null,
    ) ?? null;

  return (
    <main style={{ padding: 32, maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#6b7280" }}>Worklist</p>
          <h1 style={{ margin: "8px 0 0", fontSize: 32 }}>Flagged cases</h1>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {currentUser ? (
            <div
              style={{
                borderRadius: 999,
                background:
                  currentUser.auth_mode === "proxy"
                    ? "#dcfce7"
                    : currentUser.auth_mode === "header"
                      ? "#dbeafe"
                      : "#f3f4f6",
                color:
                  currentUser.auth_mode === "proxy"
                    ? "#166534"
                    : currentUser.auth_mode === "header"
                      ? "#1d4ed8"
                      : "#475569",
                padding: "8px 12px",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              {currentUser.display_name} • {currentUser.role} • {currentUser.provider}
            </div>
          ) : null}
          {currentUser?.capabilities.can_import_reports ? (
            <Link href="/imports" style={{ color: "#2563eb", fontWeight: 600 }}>
              Import workspace
            </Link>
          ) : null}
          <Link href="/research-intel" style={{ color: "#2563eb" }}>
            Research intelligence
          </Link>
          <Link href="/" style={{ color: "#2563eb" }}>Back</Link>
        </div>
      </div>

      {currentUser ? (
        <div style={{ margin: "0 0 16px", color: "#64748b" }}>
          <p style={{ margin: 0 }}>Access scope: {formatSiteScope(currentUser.site_scope)}</p>
          {!currentUser.capabilities.can_review_cases ? (
            <p style={{ margin: "6px 0 0" }}>
              This session is read-only. Case details remain available, but reviewer actions are hidden.
            </p>
          ) : null}
        </div>
      ) : null}

      {evaluationComparison ? (
        <div
          style={{
            background: "linear-gradient(135deg, #eff6ff, #f8fafc)",
            border: "1px solid #bfdbfe",
            borderRadius: 12,
            padding: 20,
            marginBottom: 16,
          }}
        >
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#1d4ed8" }}>Hybrid benchmark</p>
          <h2 style={{ margin: "8px 0 10px", fontSize: 22 }}>Rules vs hybrid demo comparison</h2>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 12 }}>
            <span style={{ ...badgeStyle(evaluationComparison.recall_delta >= 0 ? "review" : "defer"), borderRadius: 999, padding: "4px 10px", fontWeight: 700 }}>
              recall {evaluationComparison.recall_delta >= 0 ? "+" : ""}
              {(evaluationComparison.recall_delta * 100).toFixed(0)} pts
            </span>
            <span style={{ ...badgeStyle(evaluationComparison.f1_delta >= 0 ? "review" : "defer"), borderRadius: 999, padding: "4px 10px", fontWeight: 700 }}>
              f1 {evaluationComparison.f1_delta >= 0 ? "+" : ""}
              {(evaluationComparison.f1_delta * 100).toFixed(0)} pts
            </span>
            <span style={{ ...badgeStyle(evaluationComparison.flagged_delta >= 0 ? "review" : "defer"), borderRadius: 999, padding: "4px 10px", fontWeight: 700 }}>
              flagged {evaluationComparison.flagged_delta >= 0 ? "+" : ""}
              {evaluationComparison.flagged_delta}
            </span>
          </div>
          <p style={{ margin: "0 0 8px", color: "#334155" }}>
            Hybrid mode newly flags {evaluationComparison.newly_flagged_cases.length} case
            {evaluationComparison.newly_flagged_cases.length === 1 ? "" : "s"} and resolves{" "}
            {evaluationComparison.resolved_false_negatives.length} demo false negative
            {evaluationComparison.resolved_false_negatives.length === 1 ? "" : "s"} at the default threshold.
          </p>
          {evaluationComparison.newly_flagged_cases.length > 0 ? (
            <p style={{ margin: 0, color: "#475569" }}>
              Newly surfaced: {evaluationComparison.newly_flagged_cases.join(", ")}
            </p>
          ) : null}
          {evaluationSweep ? (
            <p style={{ margin: "8px 0 0", color: "#475569" }}>
              Recommended thresholds: rules {evaluationSweep.rules_recommendation.recommended_threshold.toFixed(2)} •
              hybrid {evaluationSweep.hybrid_recommendation.recommended_threshold.toFixed(2)}
              {bestSweepPoint
                ? ` • best hybrid F1 gain ${bestSweepPoint.f1_delta >= 0 ? "+" : ""}${(bestSweepPoint.f1_delta * 100).toFixed(0)} pts at ${bestSweepPoint.threshold.toFixed(2)}`
                : ""}
            </p>
          ) : null}
        </div>
      ) : null}

      {feedbackSummary ? (
        <div
          style={{
            background: "white",
            border: "1px solid #e5e7eb",
            borderRadius: 12,
            padding: 20,
            marginBottom: 16,
          }}
        >
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#6b7280" }}>Feedback coverage</p>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 10 }}>
            <StatPill label="Labeled cases" value={String(feedbackSummary.labeled_cases)} />
            <StatPill label="Unlabeled" value={String(feedbackSummary.unlabeled_cases)} />
            <StatPill label="Unlabeled active-learning" value={String(feedbackSummary.unlabeled_active_learning_cases)} />
            <StatPill label="Total labels" value={String(feedbackSummary.total_feedback)} />
          </div>
          {Object.keys(feedbackSummary.label_distribution).length > 0 ? (
            <p style={{ margin: "12px 0 0", color: "#475569" }}>
              Labels:{" "}
              {Object.entries(feedbackSummary.label_distribution)
                .map(([label, count]) => `${formatLabel(label)} (${count})`)
                .join(" • ")}
            </p>
          ) : (
            <p style={{ margin: "12px 0 0", color: "#64748b" }}>No structured reviewer labels recorded yet.</p>
          )}
        </div>
      ) : null}

      <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20, marginBottom: 16 }}>
        <form method="get" style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
          <label style={{ display: "grid", gap: 6, gridColumn: "1 / -1" }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Search</span>
            <input
              type="text"
              name="q"
              defaultValue={q}
              placeholder="Search case ID or report ID"
              style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px" }}
            />
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Status</span>
            <select
              name="status"
              defaultValue={status}
              style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
            >
              <option value="">All statuses</option>
              {STATUS_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Urgency</span>
            <select
              name="urgency"
              defaultValue={urgency}
              style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
            >
              <option value="">All urgency bands</option>
              {URGENCY_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Site</span>
            <input
              type="text"
              name="site"
              defaultValue={site}
              placeholder="Demo Hospital"
              style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px" }}
            />
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Modality</span>
            <select
              name="modality"
              defaultValue={modality}
              style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
            >
              <option value="">All modalities</option>
              {MODALITY_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Reviewer</span>
            <input
              type="text"
              name="reviewer"
              defaultValue={reviewer}
              placeholder="alex"
              style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px" }}
            />
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Rationale</span>
            <input
              type="text"
              name="rationale"
              defaultValue={rationale}
              placeholder="PDAC_EXPLICIT_SUSPICION"
              style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px" }}
            />
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Feedback label</span>
            <select
              name="feedback_label"
              defaultValue={feedbackLabel}
              style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
            >
              <option value="">All feedback labels</option>
              {FEEDBACK_LABEL_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {formatLabel(option)}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Min hybrid uplift</span>
            <input
              type="number"
              name="hybrid_delta_min"
              min="0"
              max="1"
              step="0.05"
              defaultValue={hybridDeltaMin}
              placeholder="0.10"
              style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px" }}
            />
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Hybrid review</span>
            <select
              name="hybrid_review_priority"
              defaultValue={hybridReviewPriority}
              style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
            >
              <option value="">All hybrid review bands</option>
              {HYBRID_REVIEW_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {formatLabel(option)}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Active learning</span>
            <select
              name="active_learning_priority"
              defaultValue={activeLearningPriority}
              style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
            >
              <option value="">All active-learning bands</option>
              {ACTIVE_LEARNING_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Sort by</span>
            <select
              name="sort_by"
              defaultValue={sortBy}
              style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Direction</span>
            <select
              name="sort_dir"
              defaultValue={sortDir}
              style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
            >
              {SORT_DIRECTION_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: "flex", gap: 8, alignItems: "center", alignSelf: "end", paddingBottom: 10 }}>
            <input type="checkbox" name="active_learning_only" value="true" defaultChecked={activeLearningOnly} />
            <span style={{ fontSize: 13, fontWeight: 600 }}>Only active-learning queue</span>
          </label>

          <label style={{ display: "flex", gap: 8, alignItems: "center", alignSelf: "end", paddingBottom: 10 }}>
            <input type="checkbox" name="needs_feedback" value="true" defaultChecked={needsFeedback} />
            <span style={{ fontSize: 13, fontWeight: 600 }}>Only unlabeled cases</span>
          </label>

          <label style={{ display: "flex", gap: 8, alignItems: "center", alignSelf: "end", paddingBottom: 10 }}>
            <input type="checkbox" name="disagreement_only" value="true" defaultChecked={disagreementOnly} />
            <span style={{ fontSize: 13, fontWeight: 600 }}>Only disagreement queue</span>
          </label>

          <div style={{ display: "flex", gap: 10, alignItems: "end", flexWrap: "wrap", alignSelf: "end" }}>
            <button
              type="submit"
              style={{
                border: 0,
                borderRadius: 8,
                padding: "10px 14px",
                background: "#0f172a",
                color: "white",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Apply filters
            </button>
            {hasActiveFilters ? (
              <Link href="/cases" style={{ color: "#2563eb", fontWeight: 600 }}>
                Clear
              </Link>
            ) : null}
          </div>
        </form>

        <p style={{ margin: "14px 0 0", color: "#475569" }}>
          {cases.length} case{cases.length === 1 ? "" : "s"} shown
          {hasActiveFilters ? " for the current filter set." : "."}
        </p>
        <p style={{ margin: "6px 0 0", color: "#64748b" }}>
          {expediteCount} hybrid expedite case{expediteCount === 1 ? "" : "s"} and {activeLearningCount} high-priority
          active-learning case{activeLearningCount === 1 ? "" : "s"} in the current view.
        </p>
        <p style={{ margin: "6px 0 0", color: "#64748b" }}>
          {disagreementCount} high-disagreement case{disagreementCount === 1 ? "" : "s"} in the current view.
        </p>
      </div>

      <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", background: "#f9fafb" }}>
              <th style={{ padding: 12 }}>Case</th>
              <th style={{ padding: 12 }}>Reported</th>
              <th style={{ padding: 12 }}>Modality</th>
              <th style={{ padding: 12 }}>Site</th>
              <th style={{ padding: 12 }}>Urgency</th>
              <th style={{ padding: 12 }}>Score</th>
              <th style={{ padding: 12 }}>Hybrid</th>
              <th style={{ padding: 12 }}>Review</th>
              <th style={{ padding: 12 }}>Active learning</th>
              <th style={{ padding: 12 }}>Feedback</th>
              <th style={{ padding: 12 }}>Status</th>
              <th style={{ padding: 12 }}>Assigned</th>
              <th style={{ padding: 12 }}>Top rationale</th>
            </tr>
          </thead>
          <tbody>
            {cases.length === 0 ? (
              <tr>
                <td colSpan={13} style={{ padding: 16, color: "#6b7280" }}>
                  {hasActiveFilters
                    ? "No cases matched the current filters."
                    : "No cases yet. Load the demo reports through the API batch endpoint first."}
                </td>
              </tr>
            ) : (
              cases.map((item) => (
                <tr key={item.case_id} style={{ borderTop: "1px solid #e5e7eb" }}>
                  <td style={{ padding: 12 }}>
                    <Link href={`/cases/${item.case_id}`} style={{ color: "#2563eb", fontWeight: 600 }}>
                      {item.case_id}
                    </Link>
                  </td>
                  <td style={{ padding: 12 }}>{formatReportedAt(item.report_datetime)}</td>
                  <td style={{ padding: 12 }}>{item.modality || "—"}</td>
                  <td style={{ padding: 12 }}>{item.site || "—"}</td>
                  <td style={{ padding: 12 }}>{item.urgency}</td>
                  <td style={{ padding: 12 }}>{item.score.toFixed(2)}</td>
                  <td style={{ padding: 12 }}>
                    {item.hybrid_score !== undefined && item.hybrid_score !== null ? (
                      <div style={{ display: "grid", gap: 4 }}>
                        <strong>{item.hybrid_score.toFixed(2)}</strong>
                        <span style={{ fontSize: 12, color: "#64748b" }}>
                          {formatLabel(item.hybrid_confidence)} • delta {formatDelta(item.hybrid_delta)}
                        </span>
                        <span style={{ fontSize: 12, color: "#64748b" }}>
                          {item.disagreement_level ? `${formatLabel(item.disagreement_level)} disagreement` : "aligned"}
                        </span>
                      </div>
                    ) : "—"}
                  </td>
                  <td style={{ padding: 12 }}>
                    {item.hybrid_review_priority ? (
                      <span
                        style={{
                          ...badgeStyle(item.hybrid_review_priority),
                          borderRadius: 999,
                          padding: "4px 10px",
                          fontSize: 12,
                          fontWeight: 700,
                          textTransform: "uppercase",
                        }}
                      >
                        {formatLabel(item.hybrid_review_priority)}
                      </span>
                    ) : "—"}
                  </td>
                  <td style={{ padding: 12 }}>
                    {item.active_learning_priority ? (
                      <span
                        style={{
                          ...badgeStyle(item.active_learning_priority),
                          borderRadius: 999,
                          padding: "4px 10px",
                          fontSize: 12,
                          fontWeight: 700,
                          textTransform: "uppercase",
                        }}
                      >
                        {formatLabel(item.active_learning_priority)}
                      </span>
                    ) : "—"}
                  </td>
                  <td style={{ padding: 12 }}>
                    <div style={{ display: "grid", gap: 4 }}>
                      <strong>{item.review_feedback_count ?? 0}</strong>
                      <span style={{ fontSize: 12, color: "#64748b" }}>
                        {item.latest_feedback_label ? formatLabel(item.latest_feedback_label) : "unlabeled"}
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: 12 }}>{item.status}</td>
                  <td style={{ padding: 12 }}>{item.assigned_to || "—"}</td>
                  <td style={{ padding: 12 }}>{item.top_rationale || "—"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}

function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        background: "#f8fafc",
        border: "1px solid #e2e8f0",
        borderRadius: 12,
        padding: "10px 12px",
        minWidth: 150,
      }}
    >
      <div style={{ fontSize: 12, color: "#64748b", marginBottom: 4 }}>{label}</div>
      <strong style={{ fontSize: 18 }}>{value}</strong>
    </div>
  );
}
