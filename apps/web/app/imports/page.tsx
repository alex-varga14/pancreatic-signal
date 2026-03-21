import Link from "next/link";

import {
  getCurrentUser,
  getImportRun,
  getImportRuns,
  type ImportAuditItem,
  type ImportFailureBucket,
  type ImportRunDetail,
} from "../../lib/api";
import {
  submitFhirDiagnosticReportImport,
  submitHl7OruImport,
  submitReportFileImport,
} from "./actions";

function readSearchParam(value: string | string[] | undefined): string {
  return Array.isArray(value) ? value[0] ?? "" : value ?? "";
}

function parseRunId(value: string): number | null {
  if (!value) return null;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function formatTimestamp(value?: string | null): string {
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
  return value.replace(/[_-]/g, " ");
}

function formatSiteScope(value?: string[] | null): string {
  if (!value || value.length === 0) return "all sites";
  return value.join(", ");
}

function statusStyle(value: "completed" | "failed"): { background: string; color: string } {
  if (value === "completed") {
    return { background: "#dcfce7", color: "#166534" };
  }
  return { background: "#fee2e2", color: "#991b1b" };
}

function failureBucketLabel(bucket: ImportFailureBucket): string {
  return bucket.replace(/_/g, " ");
}

function renderFailureCounts(failureCounts: Partial<Record<ImportFailureBucket, number>>) {
  const entries = Object.entries(failureCounts) as Array<[ImportFailureBucket, number]>;

  if (entries.length === 0) {
    return <span style={{ color: "#64748b" }}>No failures recorded.</span>;
  }

  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {entries.map(([bucket, count]) => (
        <span
          key={bucket}
          style={{
            borderRadius: 999,
            background: "#fef3c7",
            color: "#92400e",
            padding: "4px 10px",
            fontSize: 12,
            fontWeight: 700,
          }}
        >
          {failureBucketLabel(bucket)}: {count}
        </span>
      ))}
    </div>
  );
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        background: "#f8fafc",
        border: "1px solid #e2e8f0",
        borderRadius: 12,
        padding: 14,
      }}
    >
      <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>{label}</p>
      <p style={{ margin: "8px 0 0", fontSize: 24, fontWeight: 700 }}>{value}</p>
    </div>
  );
}

function RunItemsTable({ items }: { items: ImportAuditItem[] }) {
  if (items.length === 0) {
    return <p style={{ margin: 0, color: "#64748b" }}>This run did not persist per-item entries.</p>;
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ textAlign: "left", background: "#f8fafc" }}>
            <th style={{ padding: "12px 14px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Item</th>
            <th style={{ padding: "12px 14px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Status</th>
            <th style={{ padding: "12px 14px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Source</th>
            <th style={{ padding: "12px 14px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Site</th>
            <th style={{ padding: "12px 14px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Case</th>
            <th style={{ padding: "12px 14px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Failure</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={`${item.item_index}-${item.source_identifier || item.report_id || "item"}`} style={{ borderTop: "1px solid #e5e7eb" }}>
              <td style={{ padding: "14px" }}>{item.item_index}</td>
              <td style={{ padding: "14px" }}>
                <span
                  style={{
                    borderRadius: 999,
                    padding: "4px 10px",
                    fontSize: 12,
                    fontWeight: 700,
                    ...(item.status === "imported"
                      ? { background: "#dcfce7", color: "#166534" }
                      : { background: "#fee2e2", color: "#991b1b" }),
                  }}
                >
                  {formatLabel(item.status)}
                </span>
              </td>
              <td style={{ padding: "14px", color: "#334155" }}>
                <div>{item.source_identifier || "—"}</div>
                {item.report_id ? <div style={{ color: "#64748b", fontSize: 13 }}>report {item.report_id}</div> : null}
              </td>
              <td style={{ padding: "14px" }}>{item.site || "—"}</td>
              <td style={{ padding: "14px" }}>
                {item.case_id ? <Link href={`/cases/${item.case_id}`} style={{ color: "#2563eb" }}>{item.case_id}</Link> : "—"}
              </td>
              <td style={{ padding: "14px", color: "#475569" }}>
                {item.error_bucket ? <div style={{ fontWeight: 700 }}>{failureBucketLabel(item.error_bucket)}</div> : null}
                {item.error_detail ? <div style={{ marginTop: item.error_bucket ? 4 : 0 }}>{item.error_detail}</div> : item.error_bucket ? null : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RunSummaryCard({ run }: { run: ImportRunDetail }) {
  return (
    <section
      style={{
        background: "white",
        border: "1px solid #e5e7eb",
        borderRadius: 16,
        padding: 24,
        marginBottom: 16,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", marginBottom: 16 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Selected run</p>
          <h2 style={{ margin: "8px 0 0", fontSize: 28 }}>Import run #{run.run_id}</h2>
          <p style={{ margin: "8px 0 0", color: "#475569" }}>
            {formatLabel(run.source_format)}
            {run.source_name ? ` • ${run.source_name}` : ""}
          </p>
        </div>
        <span
          style={{
            borderRadius: 999,
            padding: "8px 12px",
            fontWeight: 700,
            alignSelf: "start",
            ...statusStyle(run.status),
          }}
        >
          {formatLabel(run.status)}
        </span>
      </div>

      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", marginBottom: 18 }}>
        <StatTile label="Processed" value={String(run.processed)} />
        <StatTile label="Created" value={String(run.created)} />
        <StatTile label="Updated" value={String(run.updated)} />
        <StatTile label="Flagged" value={String(run.flagged)} />
        <StatTile label="Failed" value={String(run.failed)} />
      </div>

      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginBottom: 18 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Started</p>
          <p style={{ margin: "6px 0 0", color: "#111827" }}>{formatTimestamp(run.started_at)}</p>
        </div>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Completed</p>
          <p style={{ margin: "6px 0 0", color: "#111827" }}>{formatTimestamp(run.completed_at)}</p>
        </div>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Imported sites</p>
          <p style={{ margin: "6px 0 0", color: "#111827" }}>
            {run.imported_sites.length > 0 ? run.imported_sites.join(", ") : "No sites recorded"}
          </p>
        </div>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Actor scope</p>
          <p style={{ margin: "6px 0 0", color: "#111827" }}>{formatSiteScope(run.actor_site_scope)}</p>
        </div>
      </div>

      <div style={{ marginBottom: 18 }}>
        <p style={{ margin: "0 0 8px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Failure buckets</p>
        {renderFailureCounts(run.failure_counts)}
      </div>

      <div>
        <p style={{ margin: "0 0 12px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Run items</p>
        <RunItemsTable items={run.items} />
      </div>
    </section>
  );
}

export default async function ImportsPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const selectedRunId = parseRunId(readSearchParam(resolvedSearchParams?.run_id));
  const infoMessage = readSearchParam(resolvedSearchParams?.info);
  const errorMessage = readSearchParam(resolvedSearchParams?.error);

  const currentUser = await getCurrentUser();
  const canImport = Boolean(currentUser?.capabilities.can_import_reports);

  let recentRuns: Awaited<ReturnType<typeof getImportRuns>> = [];
  let selectedRun: ImportRunDetail | null = null;

  if (canImport) {
    [recentRuns, selectedRun] = await Promise.all([
      getImportRuns({ limit: 12 }),
      selectedRunId ? getImportRun(selectedRunId) : Promise.resolve(null),
    ]);
  }

  const selectedRunMissing = Boolean(selectedRunId && canImport && !selectedRun);

  return (
    <main style={{ padding: 32, maxWidth: 1200, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#6b7280" }}>Operations</p>
          <h1 style={{ margin: "8px 0 0", fontSize: 32 }}>Import workspace</h1>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
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
          <Link href="/cases" style={{ color: "#2563eb", fontWeight: 600 }}>
            Back to worklist
          </Link>
        </div>
      </div>

      <div
        style={{
          background: "linear-gradient(135deg, #fff7ed, #f8fafc)",
          border: "1px solid #fed7aa",
          borderRadius: 16,
          padding: 24,
          marginBottom: 16,
        }}
      >
        <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#c2410c" }}>Pilot intake</p>
        <h2 style={{ margin: "8px 0 10px", fontSize: 24 }}>Submit reports and inspect audit runs in one place</h2>
        <p style={{ margin: 0, color: "#7c2d12", maxWidth: 860, lineHeight: 1.6 }}>
          CSV, JSONL, FHIR DiagnosticReport, and HL7 ORU payloads all flow through the existing deterministic triage
          pipeline. Each submission persists an import run so operators can verify created versus updated cases and
          review stable failure buckets without leaving the web app.
        </p>
      </div>

      {currentUser ? (
        <div style={{ margin: "0 0 16px", color: "#64748b" }}>
          <p style={{ margin: 0 }}>Access scope: {formatSiteScope(currentUser.site_scope)}</p>
          {!canImport ? (
            <p style={{ margin: "6px 0 0" }}>
              This session cannot submit or audit imports. Analyst, navigator, or admin access is required for the
              import workspace.
            </p>
          ) : null}
        </div>
      ) : null}

      {infoMessage ? (
        <div
          style={{
            background: "#eff6ff",
            border: "1px solid #bfdbfe",
            borderRadius: 12,
            padding: "12px 16px",
            color: "#1d4ed8",
            marginBottom: 16,
          }}
        >
          {infoMessage}
        </div>
      ) : null}

      {errorMessage ? (
        <div
          style={{
            background: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: 12,
            padding: "12px 16px",
            color: "#b91c1c",
            marginBottom: 16,
          }}
        >
          {errorMessage}
        </div>
      ) : null}

      {selectedRunMissing ? (
        <div
          style={{
            background: "#fff7ed",
            border: "1px solid #fdba74",
            borderRadius: 12,
            padding: "12px 16px",
            color: "#9a3412",
            marginBottom: 16,
          }}
        >
          Import run #{selectedRunId} is not visible in the current scope.
        </div>
      ) : null}

      {canImport ? (
        <>
          <section
            style={{
              display: "grid",
              gap: 16,
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              marginBottom: 16,
            }}
          >
            <form
              action={submitReportFileImport}
              encType="multipart/form-data"
              style={{
                background: "white",
                border: "1px solid #e5e7eb",
                borderRadius: 16,
                padding: 20,
                display: "grid",
                gap: 14,
              }}
            >
              <div>
                <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>File import</p>
                <h2 style={{ margin: "8px 0 8px", fontSize: 22 }}>CSV, JSON, or JSONL</h2>
                <p style={{ margin: 0, color: "#475569", lineHeight: 1.6 }}>
                  Upload report files with flat or nested provenance metadata. New and updated cases are counted in the
                  resulting audit run.
                </p>
              </div>
              <label style={{ display: "grid", gap: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Report file</span>
                <input
                  type="file"
                  name="report_file"
                  accept=".csv,.json,.jsonl,.ndjson,text/csv,application/json,application/x-ndjson"
                  style={{ border: "1px solid #cbd5e1", borderRadius: 10, padding: 10, background: "#f8fafc" }}
                />
              </label>
              <button
                type="submit"
                style={{
                  border: 0,
                  borderRadius: 10,
                  padding: "11px 14px",
                  background: "#0f172a",
                  color: "white",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Upload file
              </button>
            </form>

            <form
              action={submitFhirDiagnosticReportImport}
              style={{
                background: "white",
                border: "1px solid #e5e7eb",
                borderRadius: 16,
                padding: 20,
                display: "grid",
                gap: 14,
              }}
            >
              <div>
                <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>FHIR intake</p>
                <h2 style={{ margin: "8px 0 8px", fontSize: 22 }}>DiagnosticReport JSON</h2>
                <p style={{ margin: 0, color: "#475569", lineHeight: 1.6 }}>
                  Paste a single DiagnosticReport resource or a Bundle. The backend preserves structured provenance and
                  applies the configured field-preference rules.
                </p>
              </div>
              <label style={{ display: "grid", gap: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>FHIR payload</span>
                <textarea
                  name="fhir_payload"
                  rows={12}
                  placeholder={`{\n  "resourceType": "DiagnosticReport",\n  "id": "dr-001",\n  "conclusion": "Suspicious pancreatic head mass."\n}`}
                  style={{ border: "1px solid #cbd5e1", borderRadius: 10, padding: 12, resize: "vertical", fontFamily: "monospace" }}
                />
              </label>
              <button
                type="submit"
                style={{
                  border: 0,
                  borderRadius: 10,
                  padding: "11px 14px",
                  background: "#0f172a",
                  color: "white",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Submit FHIR payload
              </button>
            </form>

            <form
              action={submitHl7OruImport}
              style={{
                background: "white",
                border: "1px solid #e5e7eb",
                borderRadius: 16,
                padding: 20,
                display: "grid",
                gap: 14,
              }}
            >
              <div>
                <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>HL7 intake</p>
                <h2 style={{ margin: "8px 0 8px", fontSize: 22 }}>HL7 ORU text</h2>
                <p style={{ margin: 0, color: "#475569", lineHeight: 1.6 }}>
                  Paste one ORU payload or multiple concatenated messages. The audit run captures scope rejections and
                  parser failures with stable buckets.
                </p>
              </div>
              <label style={{ display: "grid", gap: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>HL7 payload</span>
                <textarea
                  name="hl7_payload"
                  rows={12}
                  placeholder={`MSH|^~\\&|RIS|DEMO|EHR|DEMO|202603191000||ORU^R01|MSG-001|P|2.5\nPID|1||MRN-001^^^DEMO^MR\nOBR|1||ACC-001||CT ABDOMEN\nOBX|1|TX|IMPRESSION||Suspicious pancreatic head mass.`}
                  style={{ border: "1px solid #cbd5e1", borderRadius: 10, padding: 12, resize: "vertical", fontFamily: "monospace" }}
                />
              </label>
              <button
                type="submit"
                style={{
                  border: 0,
                  borderRadius: 10,
                  padding: "11px 14px",
                  background: "#0f172a",
                  color: "white",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Submit HL7 payload
              </button>
            </form>
          </section>

          {selectedRun ? <RunSummaryCard run={selectedRun} /> : null}

          <section
            style={{
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: 16,
              padding: 24,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", marginBottom: 16 }}>
              <div>
                <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Audit trail</p>
                <h2 style={{ margin: "8px 0 0", fontSize: 24 }}>Recent import runs</h2>
              </div>
              {selectedRun ? (
                <Link href="/imports" style={{ color: "#2563eb", fontWeight: 600 }}>
                  Clear selection
                </Link>
              ) : null}
            </div>

            {recentRuns.length === 0 ? (
              <p style={{ margin: 0, color: "#64748b" }}>No import runs recorded yet.</p>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ textAlign: "left", background: "#f8fafc" }}>
                      <th style={{ padding: "12px 14px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Run</th>
                      <th style={{ padding: "12px 14px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Format</th>
                      <th style={{ padding: "12px 14px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Status</th>
                      <th style={{ padding: "12px 14px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Counts</th>
                      <th style={{ padding: "12px 14px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Started</th>
                      <th style={{ padding: "12px 14px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Sites</th>
                      <th style={{ padding: "12px 14px", fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Failures</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentRuns.map((run) => (
                      <tr key={run.run_id} style={{ borderTop: "1px solid #e5e7eb" }}>
                        <td style={{ padding: "14px" }}>
                          <Link href={`/imports?run_id=${run.run_id}`} style={{ color: "#2563eb", fontWeight: 700 }}>
                            #{run.run_id}
                          </Link>
                          <div style={{ color: "#64748b", fontSize: 13, marginTop: 4 }}>{run.actor_user_id}</div>
                        </td>
                        <td style={{ padding: "14px" }}>
                          <div>{formatLabel(run.source_format)}</div>
                          {run.source_name ? <div style={{ color: "#64748b", fontSize: 13 }}>{run.source_name}</div> : null}
                        </td>
                        <td style={{ padding: "14px" }}>
                          <span
                            style={{
                              borderRadius: 999,
                              padding: "4px 10px",
                              fontSize: 12,
                              fontWeight: 700,
                              ...statusStyle(run.status),
                            }}
                          >
                            {formatLabel(run.status)}
                          </span>
                        </td>
                        <td style={{ padding: "14px", color: "#334155" }}>
                          {run.processed} processed • {run.created} created • {run.updated} updated • {run.failed} failed
                        </td>
                        <td style={{ padding: "14px" }}>{formatTimestamp(run.started_at)}</td>
                        <td style={{ padding: "14px" }}>
                          {run.imported_sites.length > 0 ? run.imported_sites.join(", ") : "—"}
                        </td>
                        <td style={{ padding: "14px" }}>{renderFailureCounts(run.failure_counts)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      ) : null}
    </main>
  );
}
