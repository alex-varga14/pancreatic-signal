import Link from "next/link";

import { getCurrentUser, getResearchCase } from "../../../../lib/api";
import type { ImportMetadata } from "../../../../lib/api";

type HighlightRange = {
  start: number;
  end: number;
  codes: string[];
};

function buildHighlightRanges(
  evidence: { code: string; start: number; end: number }[],
  reportLength: number,
): HighlightRange[] {
  return evidence
    .filter((item) => item.start >= 0 && item.end > item.start && item.end <= reportLength)
    .sort((left, right) => left.start - right.start || left.end - right.end)
    .reduce<HighlightRange[]>((ranges, item) => {
      const previous = ranges[ranges.length - 1];
      if (previous && item.start <= previous.end) {
        previous.end = Math.max(previous.end, item.end);
        if (!previous.codes.includes(item.code)) {
          previous.codes.push(item.code);
        }
        return ranges;
      }
      ranges.push({ start: item.start, end: item.end, codes: [item.code] });
      return ranges;
    }, []);
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
        style={{ background: "#bfdbfe", borderRadius: 4, padding: "0 2px" }}
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

function formatDate(value?: string | null): string {
  if (!value) {
    return "—";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleDateString("en-CA", { dateStyle: "medium" });
}

function formatLabel(value: string): string {
  return value.replace(/_/g, " ");
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

export default async function ResearchCasePage({ params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = await params;
  const [data, currentUser] = await Promise.all([getResearchCase(caseId), getCurrentUser()]);

  if (!data) {
    return (
      <main style={{ padding: 32 }}>
        <p>Research-safe case view not found.</p>
        <Link href="/cases">Back to worklist</Link>
      </main>
    );
  }

  const importMetadataRows = getImportMetadataRows(data.import_metadata);

  return (
    <main style={{ padding: 32, maxWidth: 960, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#0f766e" }}>
            Research-safe view
          </p>
          <h1 style={{ margin: "8px 0 0", fontSize: 30 }}>{data.case_id}</h1>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <Link href={`/cases/${caseId}`} style={{ color: "#2563eb" }}>
            Raw case
          </Link>
          <Link href="/cases" style={{ color: "#2563eb" }}>
            Back
          </Link>
        </div>
      </div>

      <div
        style={{
          background: "#ecfeff",
          border: "1px solid #a5f3fc",
          borderRadius: 12,
          padding: 16,
          marginBottom: 16,
          color: "#155e75",
        }}
      >
        <p style={{ margin: 0, fontWeight: 700 }}>Identifiers and free text are de-identified in this view.</p>
        <p style={{ margin: "6px 0 0" }}>
          {data.redaction_summary.redaction_count} redactions across {data.redaction_summary.redacted_characters} masked
          characters. Pseudonymized fields: {data.redaction_summary.pseudonymized_fields.join(", ")}.
        </p>
        {currentUser ? (
          <p style={{ margin: "6px 0 0" }}>
            Accessed as {currentUser.display_name} ({currentUser.role}).
          </p>
        ) : null}
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "1.25fr 0.75fr" }}>
        <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
          <h2 style={{ marginTop: 0 }}>Redacted report text</h2>
          <p style={{ lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
            {renderHighlightedReport(data.report_text, data.evidence)}
          </p>
        </section>

        <section style={{ display: "grid", gap: 16 }}>
          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Summary</h2>
            <p><strong>Report:</strong> {data.report_id}</p>
            <p><strong>Date:</strong> {formatDate(data.report_date)}</p>
            <p><strong>Modality:</strong> {data.modality || "—"}</p>
            <p><strong>Score:</strong> {data.score.toFixed(2)}</p>
            <p><strong>Urgency:</strong> {data.urgency}</p>
            <p><strong>Status:</strong> {data.status}</p>
            <p><strong>Site:</strong> {data.site || "—"}</p>
            <p><strong>Assigned:</strong> {data.assigned_to || "—"}</p>
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
              <p style={{ margin: 0 }}>No upstream import metadata was preserved for this case.</p>
            )}
          </div>

          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Rationale codes</h2>
            {data.rationale_codes.length > 0 ? (
              <ul style={{ paddingLeft: 18, margin: 0 }}>
                {data.rationale_codes.map((code) => (
                  <li key={code}>{code}</li>
                ))}
              </ul>
            ) : (
              <p style={{ margin: 0 }}>No triage rationale codes recorded.</p>
            )}
          </div>

          <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
            <h2 style={{ marginTop: 0 }}>Redaction categories</h2>
            {Object.keys(data.redaction_summary.categories).length > 0 ? (
              <ul style={{ paddingLeft: 18, margin: 0 }}>
                {Object.entries(data.redaction_summary.categories).map(([category, count]) => (
                  <li key={category}>
                    {formatLabel(category)}: {count}
                  </li>
                ))}
              </ul>
            ) : (
              <p style={{ margin: 0 }}>No PHI patterns were detected in this case.</p>
            )}
          </div>
        </section>
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "1fr 1fr", marginTop: 16 }}>
        <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
          <h2 style={{ marginTop: 0 }}>Review history</h2>
          {data.review_actions.length > 0 ? (
            <ul style={{ paddingLeft: 18, margin: 0 }}>
              {data.review_actions.map((action, index) => (
                <li key={`${action.action}-${action.created_date}-${index}`}>
                  {action.action} by {action.reviewer} on {formatDate(action.created_date)}
                  {action.assigned_to ? ` • assigned ${action.assigned_to}` : ""}
                  {action.note ? ` • ${action.note}` : ""}
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ margin: 0 }}>No review actions recorded.</p>
          )}
        </section>

        <section style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 12, padding: 20 }}>
          <h2 style={{ marginTop: 0 }}>Reviewer feedback</h2>
          {data.review_feedback.length > 0 ? (
            <ul style={{ paddingLeft: 18, margin: 0 }}>
              {data.review_feedback.map((feedback, index) => (
                <li key={`${feedback.reviewer}-${feedback.created_date}-${index}`}>
                  {feedback.reviewer} • {formatLabel(feedback.label)} / {formatLabel(feedback.disposition)} on{" "}
                  {formatDate(feedback.created_date)}
                  {feedback.error_bucket ? ` • ${formatLabel(feedback.error_bucket)}` : ""}
                  {feedback.notes ? ` • ${feedback.notes}` : ""}
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ margin: 0 }}>No reviewer feedback recorded.</p>
          )}
        </section>
      </div>
    </main>
  );
}
