import Link from "next/link";
import { getCase, getCurrentUser, getFeedbackRecommendation, getHybridAnalysis, getTrialMatches } from "../../../lib/api";
import type { FeedbackRecommendation, HybridAnalysis, ImportMetadata, TrialAbstraction } from "../../../lib/api";
import { submitCaseFeedback, submitReviewAction } from "../actions";

type HighlightRange = {
  start: number;
  end: number;
  codes: string[];
};

function buildHighlightRanges(
  evidence: { code: string; start: number; end: number }[],
  reportLength: number,
): HighlightRange[] {
  const valid = evidence
    .filter((item) => item.start >= 0 && item.end > item.start && item.end <= reportLength)
    .sort((left, right) => left.start - right.start || left.end - right.end);

  const merged: HighlightRange[] = [];
  for (const item of valid) {
    const previous = merged[merged.length - 1];
    if (previous && item.start <= previous.end) {
      previous.end = Math.max(previous.end, item.end);
      if (!previous.codes.includes(item.code)) {
        previous.codes.push(item.code);
      }
      continue;
    }

    merged.push({ start: item.start, end: item.end, codes: [item.code] });
  }

  return merged;
}

function renderHighlightedReport(
  reportText: string,
  evidence: { code: string; start: number; end: number }[],
): React.ReactNode {
  const ranges = buildHighlightRanges(evidence, reportText.length);
  if (ranges.length === 0) {
    return reportText;
  }

  const fragments: React.ReactNode[] = [];
  let cursor = 0;

  for (const range of ranges) {
    if (range.start > cursor) {
      fragments.push(<span key={`plain-${cursor}`}>{reportText.slice(cursor, range.start)}</span>);
    }

    fragments.push(
      <mark
        key={`highlight-${range.start}-${range.end}`}
        title={range.codes.join(", ")}
        style={{
          background: "#fde68a",
          borderRadius: 4,
          padding: "0 2px",
        }}
      >
        {reportText.slice(range.start, range.end)}
      </mark>,
    );
    cursor = range.end;
  }

  if (cursor < reportText.length) {
    fragments.push(<span key={`plain-${cursor}`}>{reportText.slice(cursor)}</span>);
  }

  return fragments;
}

function formatTimestamp(value?: string | null): string {
  if (!value) {
    return "—";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatLabel(value: string): string {
  return value.replace(/_/g, " ");
}

function formatSiteScope(value?: string[] | null): string {
  if (!value || value.length === 0) {
    return "all sites";
  }
  return value.join(", ");
}

const IMPORT_METADATA_LABELS: { key: keyof ImportMetadata; label: string }[] = [
  { key: "patient_identifier", label: "Patient identifier" },
  { key: "encounter_identifier", label: "Encounter identifier" },
  { key: "accession_number", label: "Accession number" },
  { key: "ordering_provider", label: "Ordering provider" },
  { key: "source_system", label: "Source system" },
  { key: "source_format", label: "Source format" },
  { key: "import_source_id", label: "Import source ID" },
];

function getImportMetadataRows(metadata?: ImportMetadata | null) {
  return IMPORT_METADATA_LABELS
    .map(({ key, label }) => ({ label, value: metadata?.[key] || null }))
    .filter((item) => item.value);
}

function badgeStyle(kind: string) {
  switch (kind) {
    case "high":
    case "expedite":
      return { background: "#fee2e2", color: "#991b1b" };
    case "moderate":
    case "review":
      return { background: "#fef3c7", color: "#92400e" };
    case "borderline":
      return { background: "#e0f2fe", color: "#075985" };
    case "anchored":
      return { background: "#dbeafe", color: "#1d4ed8" };
    default:
      return { background: "#e2e8f0", color: "#475569" };
  }
}

const ABSTRACTION_LABELS: { key: keyof TrialAbstraction; label: string }[] = [
  { key: "modality", label: "Modality" },
  { key: "high_risk_pancreatic_signal", label: "High-risk signal" },
  { key: "suspected_pdac", label: "Suspicious PDAC language" },
  { key: "pancreatic_mass", label: "Pancreatic mass language" },
  { key: "secondary_signs_present", label: "Secondary signs present" },
  { key: "needs_tissue_confirmation", label: "Needs tissue confirmation" },
  { key: "localized_disease_suspected", label: "Localized pattern suspected" },
  { key: "pancreatic_head_focus", label: "Pancreatic head focus" },
  { key: "metastatic_language_present", label: "Metastatic language present" },
];

const FEEDBACK_LABEL_OPTIONS = [
  { value: "true_positive", label: "True positive" },
  { value: "false_positive", label: "False positive" },
  { value: "actionable_followup", label: "Actionable follow-up" },
  { value: "benign", label: "Benign" },
  { value: "uncertain", label: "Uncertain" },
];

const FEEDBACK_DISPOSITION_OPTIONS = [
  { value: "escalate", label: "Escalate" },
  { value: "dismiss", label: "Dismiss" },
  { value: "routine_followup", label: "Routine follow-up" },
  { value: "monitor", label: "Monitor" },
  { value: "needs_more_review", label: "Needs more review" },
];

const FEEDBACK_BUCKET_OPTIONS = [
  { value: "", label: "No error bucket" },
  { value: "wording_variance", label: "Wording variance" },
  { value: "negation_failure", label: "Negation failure" },
  { value: "incidental_cyst", label: "Incidental cyst" },
  { value: "pancreatitis_confounder", label: "Pancreatitis confounder" },
  { value: "secondary_signs_only", label: "Secondary signs only" },
  { value: "other", label: "Other" },
];

export default async function CaseDetailPage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = await params;
  const [data, trialMatches, hybridAnalysis, feedbackRecommendation, currentUser] = await Promise.all([
    getCase(caseId),
    getTrialMatches(caseId),
    getHybridAnalysis(caseId),
    getFeedbackRecommendation(caseId),
    getCurrentUser(),
  ]);
  const canReviewCases = currentUser?.capabilities.can_review_cases ?? false;
  const canSubmitFeedback = currentUser?.capabilities.can_submit_feedback ?? false;

  if (!data) {
    return (
      <main style={{ padding: 32 }}>
        <p>Case not found.</p>
        <Link href="/cases">Back to worklist</Link>
      </main>
    );
  }

  const importMetadataRows = getImportMetadataRows(data.import_metadata);

  return (
    <main style={{ padding: 32, maxWidth: 1000, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#6b7280" }}>Case detail</p>
          <h1 style={{ margin: "8px 0 0", fontSize: 32 }}>{data.case_id}</h1>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <Link href={`/cases/${caseId}/research`} style={{ color: "#2563eb" }}>Research-safe view</Link>
          <Link href="/cases" style={{ color: "#2563eb" }}>Back</Link>
        </div>
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "1.3fr 0.7fr" }}>
        <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
          <h2 style={{ marginTop: 0 }}>Report text</h2>
          <p style={{ lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
            {renderHighlightedReport(data.report_text, data.evidence)}
          </p>
        </section>

        <section style={{ display: "grid", gap: 16 }}>
          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Summary</h2>
            <p><strong>Urgency:</strong> {data.urgency}</p>
            <p><strong>Score:</strong> {data.score.toFixed(2)}</p>
            <p><strong>Status:</strong> {data.status}</p>
            <p><strong>Reported:</strong> {formatTimestamp(data.report_datetime)}</p>
            <p><strong>Modality:</strong> {data.modality || "—"}</p>
            <p><strong>Site:</strong> {data.site || "—"}</p>
            <p><strong>Assigned:</strong> {data.assigned_to || "Unassigned"}</p>
            <p><strong>Trial candidates:</strong> {trialMatches?.matches.length ?? 0}</p>
            <p><strong>Hybrid score:</strong> {hybridAnalysis ? hybridAnalysis.calibrated_score.toFixed(2) : "—"}</p>
            <p><strong>Reviewer labels:</strong> {data.review_feedback.length}</p>
            <p>
              <strong>Signed in as:</strong>{" "}
              {currentUser ? `${currentUser.display_name} (${currentUser.role})` : "Unavailable"}
            </p>
            <p><strong>Auth mode:</strong> {currentUser?.auth_mode || "unavailable"}</p>
            <p><strong>Provider:</strong> {currentUser?.provider || "unavailable"}</p>
            <p><strong>Access scope:</strong> {formatSiteScope(currentUser?.site_scope)}</p>
          </div>

          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Import context</h2>
            {importMetadataRows.length > 0 ? (
              <div style={{ display: "grid", gap: 10 }}>
                {importMetadataRows.map((item) => (
                  <div
                    key={item.label}
                    style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "baseline" }}
                  >
                    <strong>{item.label}</strong>
                    <span style={{ color: "#334155", textAlign: "right", wordBreak: "break-word" }}>{item.value}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ marginBottom: 0, color: "#64748b" }}>No upstream import metadata recorded for this case.</p>
            )}
          </div>

          <HybridReviewCard hybridAnalysis={hybridAnalysis} />

          <FeedbackRecommendationCard feedbackRecommendation={feedbackRecommendation} />

          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Reviewer action</h2>
            {canReviewCases ? (
              <>
                <p style={{ marginTop: 0, color: "#475569" }}>
                  Actions are recorded under the current authenticated actor.
                </p>
                <form action={submitReviewAction} style={{ display: "grid", gap: 12 }}>
                  <input type="hidden" name="case_id" value={data.case_id} />

                  <label style={{ display: "grid", gap: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Action</span>
                    <select
                      name="action"
                      defaultValue="in_review"
                      style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
                    >
                      <option value="in_review">Mark in review</option>
                      <option value="assign">Assign</option>
                      <option value="note">Add note</option>
                      <option value="escalate">Escalate</option>
                      <option value="dismiss">Dismiss</option>
                      <option value="close">Close</option>
                      <option value="reopen">Reopen</option>
                    </select>
                  </label>

                  <label style={{ display: "grid", gap: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Assign to</span>
                    <input
                      type="text"
                      name="assigned_to"
                      placeholder="navigator-a"
                      style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px" }}
                    />
                  </label>

                  <label style={{ display: "grid", gap: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Note</span>
                    <textarea
                      name="note"
                      rows={4}
                      placeholder="Why this case was escalated, dismissed, or reassigned."
                      style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", resize: "vertical" }}
                    />
                  </label>

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
                    Save action
                  </button>
                </form>
              </>
            ) : (
              <p style={{ marginBottom: 0, color: "#64748b" }}>
                This session is read-only. Reviewer actions are hidden for the current actor.
              </p>
            )}
          </div>

          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Reviewer feedback label</h2>
            {canSubmitFeedback ? (
              <>
                <p style={{ marginTop: 0, color: "#475569" }}>
                  Feedback labels are saved under the current authenticated actor.
                </p>
                <form action={submitCaseFeedback} style={{ display: "grid", gap: 12 }}>
                  <input type="hidden" name="case_id" value={data.case_id} />

                  <label style={{ display: "grid", gap: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Label</span>
                    <select
                      name="feedback_label"
                      defaultValue={feedbackRecommendation?.recommended_label || "true_positive"}
                      style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
                    >
                      {FEEDBACK_LABEL_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label style={{ display: "grid", gap: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Disposition</span>
                    <select
                      name="feedback_disposition"
                      defaultValue={feedbackRecommendation?.recommended_disposition || "needs_more_review"}
                      style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
                    >
                      {FEEDBACK_DISPOSITION_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label style={{ display: "grid", gap: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Error bucket</span>
                    <select
                      name="feedback_error_bucket"
                      defaultValue={feedbackRecommendation?.recommended_error_bucket || ""}
                      style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", background: "white" }}
                    >
                      {FEEDBACK_BUCKET_OPTIONS.map((option) => (
                        <option key={option.value || "none"} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label style={{ display: "grid", gap: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Notes</span>
                    <textarea
                      name="feedback_notes"
                      rows={4}
                      placeholder="What the reviewer learned from this case."
                      defaultValue={feedbackRecommendation?.suggested_notes || ""}
                      style={{ border: "1px solid #cbd5e1", borderRadius: 8, padding: "10px 12px", resize: "vertical" }}
                    />
                  </label>

                  <button
                    type="submit"
                    style={{
                      border: 0,
                      borderRadius: 8,
                      padding: "10px 14px",
                      background: "#1d4ed8",
                      color: "white",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Save feedback label
                  </button>
                </form>
              </>
            ) : (
              <p style={{ marginBottom: 0, color: "#64748b" }}>
                Structured reviewer labels are hidden for read-only sessions.
              </p>
            )}
          </div>

          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Rationale codes</h2>
            <ul>
              {data.rationale_codes.map((code) => <li key={code}>{code}</li>)}
            </ul>
          </div>

          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Trial abstractions</h2>
            {trialMatches ? (
              <div style={{ display: "grid", gap: 10 }}>
                {ABSTRACTION_LABELS.map(({ key, label }) => {
                  const value = trialMatches.abstraction[key];
                  const display = typeof value === "boolean" ? (value ? "Yes" : "No") : value;
                  const accent =
                    typeof value === "boolean"
                      ? value
                        ? "#166534"
                        : "#64748b"
                      : "#0f172a";
                  const background =
                    typeof value === "boolean"
                      ? value
                        ? "#dcfce7"
                        : "#f1f5f9"
                      : "#e2e8f0";

                  return (
                    <div
                      key={String(key)}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        gap: 12,
                        padding: "10px 12px",
                        borderRadius: 10,
                        background,
                      }}
                    >
                      <span style={{ fontWeight: 600 }}>{label}</span>
                      <span style={{ color: accent }}>{display}</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p style={{ marginBottom: 0, color: "#64748b" }}>Trial abstractions unavailable for this case.</p>
            )}
          </div>

          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Evidence</h2>
            <ul>
              {data.evidence.map((item, idx) => (
                <li key={`${item.code}-${idx}`} style={{ marginBottom: 8 }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginBottom: 4 }}>
                    <strong>{item.code}</strong>
                    <span
                      style={{
                        fontSize: 12,
                        textTransform: "uppercase",
                        letterSpacing: 0.4,
                        color: "#475569",
                        background: "#f1f5f9",
                        borderRadius: 999,
                        padding: "2px 8px",
                      }}
                    >
                      {item.section || "unknown"}
                    </span>
                    <span style={{ fontSize: 12, color: "#64748b" }}>
                      chars {item.start}-{item.end}
                      {item.sentence_index !== undefined && item.sentence_index !== null
                        ? ` • sentence ${item.sentence_index + 1}`
                        : ""}
                    </span>
                  </div>
                  <span>{item.text}</span>
                </li>
              ))}
            </ul>
          </div>

          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Review history</h2>
            {data.review_actions.length === 0 ? (
              <p style={{ marginBottom: 0, color: "#64748b" }}>No reviewer actions recorded yet.</p>
            ) : (
              <ul style={{ paddingLeft: 18, marginBottom: 0 }}>
                {data.review_actions.map((action, idx) => (
                  <li key={`${action.created_at}-${idx}`} style={{ marginBottom: 10 }}>
                    <strong>{action.action}</strong> by {action.reviewer} on {formatTimestamp(action.created_at)}
                    {action.assigned_to ? ` • assigned to ${action.assigned_to}` : ""}
                    {action.note ? ` • ${action.note}` : ""}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Reviewer feedback history</h2>
            {data.review_feedback.length === 0 ? (
              <p style={{ marginBottom: 0, color: "#64748b" }}>No structured reviewer labels recorded yet.</p>
            ) : (
              <ul style={{ paddingLeft: 18, marginBottom: 0 }}>
                {data.review_feedback.map((feedback, idx) => (
                  <li key={`${feedback.created_at}-${idx}`} style={{ marginBottom: 10 }}>
                    <strong>{formatLabel(feedback.label)}</strong> by {feedback.reviewer} on{" "}
                    {formatTimestamp(feedback.created_at)}
                    {feedback.disposition ? ` • ${formatLabel(feedback.disposition)}` : ""}
                    {feedback.error_bucket ? ` • ${formatLabel(feedback.error_bucket)}` : ""}
                    {feedback.notes ? ` • ${feedback.notes}` : ""}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <HybridSentenceCard hybridAnalysis={hybridAnalysis} />

          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Trial matches</h2>
            {!trialMatches || trialMatches.matches.length === 0 ? (
              <p style={{ marginBottom: 0, color: "#64748b" }}>
                No potential PDAC trial candidates matched the current explainable rule set.
              </p>
            ) : (
              <div style={{ display: "grid", gap: 14 }}>
                {trialMatches.matches.map((candidate) => (
                  <div
                    key={candidate.trial_id}
                    style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 16, background: "#f8fafc" }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                      <div>
                        <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>
                          {candidate.trial_id}
                        </p>
                        <h3 style={{ margin: "6px 0 8px", fontSize: 18 }}>{candidate.title}</h3>
                      </div>
                      <div
                        style={{
                          alignSelf: "start",
                          borderRadius: 999,
                          padding: "4px 10px",
                          background: candidate.match_status === "strong" ? "#dcfce7" : "#fef3c7",
                          color: candidate.match_status === "strong" ? "#166534" : "#92400e",
                          fontWeight: 700,
                        }}
                      >
                        {candidate.match_status} • {(candidate.match_score * 100).toFixed(0)}%
                      </div>
                    </div>

                    <p style={{ margin: "0 0 8px", color: "#334155" }}>{candidate.summary}</p>
                    <p style={{ margin: "0 0 12px", color: "#475569" }}>
                      <strong>Why it matched:</strong> {candidate.rationale}
                    </p>
                    <p style={{ margin: "0 0 12px", fontSize: 13, color: "#64748b" }}>
                      Source: {candidate.source}
                    </p>

                    <ul style={{ paddingLeft: 18, marginBottom: 0 }}>
                      {candidate.criteria.map((criterion) => (
                        <li key={criterion.id} style={{ marginBottom: 10 }}>
                          <strong>{criterion.label}</strong> ({criterion.status})
                          <div style={{ color: "#475569", marginTop: 4 }}>{criterion.rationale}</div>
                          {criterion.evidence.length > 0 ? (
                            <div style={{ color: "#64748b", marginTop: 4 }}>
                              Evidence: {criterion.evidence.join(" | ")}
                            </div>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function HybridReviewCard({ hybridAnalysis }: { hybridAnalysis: HybridAnalysis | null }) {
  if (!hybridAnalysis) {
    return (
      <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
        <h2 style={{ marginTop: 0 }}>Hybrid review</h2>
        <p style={{ marginBottom: 0, color: "#64748b" }}>Hybrid analysis unavailable for this case.</p>
      </div>
    );
  }

  const confidenceTone = badgeStyle(hybridAnalysis.confidence_label);
  const priorityTone = badgeStyle(hybridAnalysis.review_priority);

  return (
    <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
      <h2 style={{ marginTop: 0 }}>Hybrid review</h2>
      <p style={{ marginTop: 0, color: "#334155", lineHeight: 1.6 }}>{hybridAnalysis.summary}</p>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        <span
          style={{
            ...confidenceTone,
            borderRadius: 999,
            padding: "4px 10px",
            fontSize: 12,
            fontWeight: 700,
            textTransform: "uppercase",
          }}
        >
          {formatLabel(hybridAnalysis.confidence_label)}
        </span>
        <span
          style={{
            ...priorityTone,
            borderRadius: 999,
            padding: "4px 10px",
            fontSize: 12,
            fontWeight: 700,
            textTransform: "uppercase",
          }}
        >
          {formatLabel(hybridAnalysis.review_priority)}
        </span>
        <span
          style={{
            background: "#eff6ff",
            color: "#1d4ed8",
            borderRadius: 999,
            padding: "4px 10px",
            fontSize: 12,
            fontWeight: 700,
            textTransform: "uppercase",
          }}
        >
          active learning {formatLabel(hybridAnalysis.active_learning_priority)}
        </span>
      </div>
      <p><strong>Calibrated score:</strong> {hybridAnalysis.calibrated_score.toFixed(2)}</p>
      <ul style={{ paddingLeft: 18, marginBottom: 0 }}>
        {hybridAnalysis.factors.map((factor) => (
          <li key={factor} style={{ marginBottom: 8 }}>{factor}</li>
        ))}
      </ul>
    </div>
  );
}

function FeedbackRecommendationCard({
  feedbackRecommendation,
}: {
  feedbackRecommendation: FeedbackRecommendation | null;
}) {
  if (!feedbackRecommendation) {
    return (
      <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
        <h2 style={{ marginTop: 0 }}>Label recommendation</h2>
        <p style={{ marginBottom: 0, color: "#64748b" }}>Feedback recommendation unavailable for this case.</p>
      </div>
    );
  }

  const confidenceTone = badgeStyle(feedbackRecommendation.confidence);
  return (
    <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
      <h2 style={{ marginTop: 0 }}>Label recommendation</h2>
      <p style={{ marginTop: 0, color: "#334155", lineHeight: 1.6 }}>{feedbackRecommendation.rationale}</p>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        <span
          style={{
            ...confidenceTone,
            borderRadius: 999,
            padding: "4px 10px",
            fontSize: 12,
            fontWeight: 700,
            textTransform: "uppercase",
          }}
        >
          {formatLabel(feedbackRecommendation.confidence)}
        </span>
        <span
          style={{
            background: "#eff6ff",
            color: "#1d4ed8",
            borderRadius: 999,
            padding: "4px 10px",
            fontSize: 12,
            fontWeight: 700,
            textTransform: "uppercase",
          }}
        >
          {formatLabel(feedbackRecommendation.recommended_label)}
        </span>
        <span
          style={{
            background: "#f8fafc",
            color: "#334155",
            borderRadius: 999,
            padding: "4px 10px",
            fontSize: 12,
            fontWeight: 700,
            textTransform: "uppercase",
          }}
        >
          {formatLabel(feedbackRecommendation.recommended_disposition)}
        </span>
      </div>
      {feedbackRecommendation.recommended_error_bucket ? (
        <p style={{ margin: "0 0 12px", color: "#475569" }}>
          <strong>Suggested bucket:</strong> {formatLabel(feedbackRecommendation.recommended_error_bucket)}
        </p>
      ) : null}
      {feedbackRecommendation.already_labeled ? (
        <p style={{ margin: "0 0 12px", color: "#475569" }}>
          <strong>Anchored by latest label:</strong> {formatLabel(feedbackRecommendation.latest_feedback_label || "")}
          {feedbackRecommendation.latest_feedback_disposition
            ? ` • ${formatLabel(feedbackRecommendation.latest_feedback_disposition)}`
            : ""}
        </p>
      ) : null}
      <ul style={{ paddingLeft: 18, marginBottom: 0 }}>
        {feedbackRecommendation.reasons.map((reason) => (
          <li key={reason} style={{ marginBottom: 8 }}>{reason}</li>
        ))}
      </ul>
    </div>
  );
}

function HybridSentenceCard({ hybridAnalysis }: { hybridAnalysis: HybridAnalysis | null }) {
  return (
    <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
      <h2 style={{ marginTop: 0 }}>Hybrid ranked sentences</h2>
      {!hybridAnalysis || hybridAnalysis.sentence_candidates.length === 0 ? (
        <p style={{ marginBottom: 0, color: "#64748b" }}>No additional sentence-level hybrid signals were surfaced.</p>
      ) : (
        <div style={{ display: "grid", gap: 14 }}>
          {hybridAnalysis.sentence_candidates.map((candidate) => (
            <div
              key={`${candidate.section}-${candidate.sentence_index}-${candidate.text}`}
              style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 16, background: "#f8fafc" }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 12,
                  alignItems: "center",
                  flexWrap: "wrap",
                  marginBottom: 8,
                }}
              >
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                  <strong>{candidate.section}</strong>
                  <span style={{ fontSize: 12, color: "#64748b" }}>sentence {candidate.sentence_index + 1}</span>
                </div>
                <div
                  style={{
                    borderRadius: 999,
                    padding: "4px 10px",
                    background: candidate.score >= 0.5 ? "#fee2e2" : candidate.score >= 0.25 ? "#fef3c7" : "#e2e8f0",
                    color: candidate.score >= 0.5 ? "#991b1b" : candidate.score >= 0.25 ? "#92400e" : "#475569",
                    fontWeight: 700,
                  }}
                >
                  {formatLabel(candidate.classification)} • {(candidate.score * 100).toFixed(0)}%
                </div>
              </div>
              <p style={{ margin: "0 0 12px", color: "#0f172a", lineHeight: 1.6 }}>{candidate.text}</p>
              {candidate.matched_codes.length > 0 ? (
                <p style={{ margin: "0 0 10px", color: "#475569" }}>
                  <strong>Matched codes:</strong> {candidate.matched_codes.join(", ")}
                </p>
              ) : null}
              <ul style={{ paddingLeft: 18, marginBottom: 0 }}>
                {candidate.signals.map((signal) => (
                  <li key={`${candidate.sentence_index}-${signal.code}`} style={{ marginBottom: 8 }}>
                    <strong>{signal.label}</strong> ({signal.weight >= 0 ? "+" : ""}
                    {signal.weight.toFixed(2)}) {signal.rationale}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
