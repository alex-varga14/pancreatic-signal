import Link from "next/link";

import { getCurrentUser, getResearchRuns, getResearchSchedule, type ResearchRunSummary } from "../../../lib/api";
import {
  triggerDueResearchIngestAction,
  triggerResearchIngestAction,
  triggerResearchWatchtowerAction,
} from "../actions";


function formatDateTime(value?: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}


export default async function ResearchIntelSchedulePage() {
  const [currentUser, schedule, runs] = await Promise.all([
    getCurrentUser(),
    getResearchSchedule(),
    getResearchRuns(10),
  ]);
  const canManage = currentUser?.capabilities.can_manage_research_intel ?? false;
  const latestWatchtowerRun = runs.find((run) => run.run_type === "watchtower") || null;

  return (
    <main style={{ padding: 32, maxWidth: 1160, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap", marginBottom: 20 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#0f766e" }}>
            Research Intelligence schedule
          </p>
          <h1 style={{ margin: "8px 0 0", fontSize: 34 }}>Discovery watchtower cadence</h1>
          <p style={{ maxWidth: 760, color: "#475569", lineHeight: 1.7 }}>
            This view shows which pancreatic oncology sources are due, which are waiting on their next interval, and which
            connectors are ready for live discovery. It is the scheduling layer behind the standing watchtower model.
          </p>
        </div>

        <div style={{ display: "flex", gap: 12, alignItems: "start", flexWrap: "wrap" }}>
          {canManage ? (
            <>
              <form action={triggerResearchWatchtowerAction}>
                <button
                  type="submit"
                  style={{
                    border: 0,
                    borderRadius: 10,
                    padding: "10px 14px",
                    background: "#0f766e",
                    color: "white",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  Run watchtower tick
                </button>
              </form>
              <form action={triggerDueResearchIngestAction}>
                <button
                  type="submit"
                  style={{
                    border: 0,
                    borderRadius: 10,
                    padding: "10px 14px",
                    background: "#134e4a",
                    color: "white",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  Run due sources
                </button>
              </form>
              <form action={triggerResearchIngestAction}>
                <button
                  type="submit"
                  style={{
                    border: "1px solid #cbd5e1",
                    borderRadius: 10,
                    padding: "10px 14px",
                    background: "white",
                    color: "#0f172a",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  Run all sources
                </button>
              </form>
            </>
          ) : null}
          <Link href="/research-intel" style={{ color: "#2563eb" }}>
            Back to dashboard
          </Link>
        </div>
      </div>

      {schedule ? (
        <>
          {latestWatchtowerRun ? <LatestWatchtowerRunCard run={latestWatchtowerRun} /> : null}

          <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", marginBottom: 16 }}>
            <StatCard label="Due now" value={String(schedule.due_count)} note={`${schedule.overdue_count} overdue`} />
            <StatCard label="Scheduled" value={String(schedule.scheduled_count)} note="Waiting on their next interval" />
            <StatCard label="Live-ready" value={String(schedule.live_ready_count)} note="Can attempt live discovery mode" />
            <StatCard label="Fixture-only" value={String(schedule.fixture_only_count)} note="Still curated through checked-in fixtures" />
          </div>

          <div style={{ display: "grid", gap: 14 }}>
            {schedule.sources.map((source) => (
              <section
                key={source.source_id}
                style={{
                  background: "white",
                  border: "1px solid #e5e7eb",
                  borderRadius: 14,
                  padding: 20,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap", marginBottom: 8 }}>
                  <div>
                    <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>
                      {source.source_kind.replace(/_/g, " ")}
                    </p>
                    <h2 style={{ margin: "6px 0 4px", fontSize: 22 }}>{source.label}</h2>
                    <p style={{ margin: 0, color: "#475569", lineHeight: 1.65 }}>{source.description}</p>
                  </div>
                  <div style={{ minWidth: 240 }}>
                    <p style={{ margin: 0, fontSize: 13, color: "#0f172a", fontWeight: 700 }}>
                      {source.schedule_state === "due" ? "Due now" : source.schedule_state}
                    </p>
                    <p style={{ margin: "6px 0 0", fontSize: 13, color: "#475569" }}>
                      {source.schedule_summary || "No schedule configured"}
                    </p>
                    <p style={{ margin: "6px 0 0", fontSize: 13, color: "#475569" }}>
                      next run {formatDateTime(source.next_run_at)} • last success {formatDateTime(source.last_success_at)}
                    </p>
                  </div>
                </div>

                <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
                  <SourceFact label="Connector" value={source.connector_id || "unassigned"} />
                  <SourceFact label="Mode" value={`${source.default_mode || "fixture"} default`} />
                  <SourceFact label="Priority" value={source.priority || "normal"} />
                  <SourceFact
                    label="Cadence"
                    value={
                      source.effective_interval_hours
                        ? `every ${source.effective_interval_hours}h`
                        : source.interval_hours
                          ? `every ${source.interval_hours}h`
                          : "manual"
                    }
                  />
                  <SourceFact label="Health" value={source.health_status} />
                  <SourceFact label="Last document count" value={source.last_document_count?.toString() || "—"} />
                  <SourceFact label="Live-ready" value={source.live_ready ? "yes" : "no"} />
                  <SourceFact
                    label="Failures"
                    value={
                      source.consecutive_failures > 0
                        ? `${source.consecutive_failures} consecutive`
                        : "none"
                    }
                  />
                </div>

                {(source.overdue_by_hours || source.last_error_detail) ? (
                  <div
                    style={{
                      marginTop: 14,
                      padding: 14,
                      borderRadius: 12,
                      background: "#f8fafc",
                      border: "1px solid #e2e8f0",
                    }}
                  >
                    {source.overdue_by_hours ? (
                      <p style={{ margin: 0, color: "#334155" }}>
                        Overdue by {source.overdue_by_hours.toFixed(1)} hours.
                      </p>
                    ) : null}
                    {source.last_error_detail ? (
                      <p style={{ margin: source.overdue_by_hours ? "8px 0 0" : 0, color: "#334155" }}>
                        Last error: {source.last_error_detail}
                      </p>
                    ) : null}
                  </div>
                ) : null}
              </section>
            ))}
          </div>
        </>
      ) : (
        <p style={{ color: "#64748b" }}>Schedule data is unavailable right now.</p>
      )}
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


function SourceFact({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 12, background: "#f8fafc" }}>
      <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>{label}</p>
      <p style={{ margin: "6px 0 0", color: "#0f172a", fontWeight: 700 }}>{value}</p>
    </div>
  );
}


function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  return value as Record<string, unknown>;
}


function readBoolean(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}


function readNumber(value: unknown): number | null {
  return typeof value === "number" ? value : null;
}


function readString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}


function LatestWatchtowerRunCard({ run }: { run: ResearchRunSummary }) {
  const metadata = asRecord(run.metadata);
  const ingestDecision = asRecord(metadata?.ingest_decision);
  const digestDecision = asRecord(metadata?.digest_decision);
  const scheduleBefore = asRecord(metadata?.schedule_before);
  const scheduleAfter = asRecord(metadata?.schedule_after);
  const ingestRun = asRecord(metadata?.ingest_run);
  const digestRun = asRecord(metadata?.digest_run);

  return (
    <section
      style={{
        marginBottom: 18,
        background: "#ecfeff",
        border: "1px solid #99f6e4",
        borderRadius: 16,
        padding: 20,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#0f766e" }}>
            Latest automation tick
          </p>
          <h2 style={{ margin: "6px 0 4px", fontSize: 24 }}>Watchtower run {run.run_id}</h2>
          <p style={{ margin: 0, color: "#155e75", lineHeight: 1.65, maxWidth: 760 }}>
            The recurring watchtower runner uses due-only ingest plus digest gating so the project can keep scanning
            pancreatic oncology sources without publishing synthetic digest churn.
          </p>
        </div>
        <div style={{ minWidth: 260 }}>
          <p style={{ margin: 0, fontWeight: 700, color: "#0f172a" }}>{run.status.replace(/_/g, " ")}</p>
          <p style={{ margin: "6px 0 0", color: "#0f172a" }}>
            actor {run.actor_user_id} • completed {formatDateTime(run.completed_at)}
          </p>
          <p style={{ margin: "6px 0 0", color: "#155e75" }}>
            processed {run.processed} • created {run.created} • updated {run.updated} • failed {run.failed}
          </p>
        </div>
      </div>

      <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginTop: 14 }}>
        <SourceFact
          label="Ingest"
          value={
            `${readBoolean(ingestDecision?.triggered) ? "triggered" : "skipped"}`
            + (readString(ingestDecision?.reason) ? ` • ${readString(ingestDecision?.reason)}` : "")
          }
        />
        <SourceFact
          label="Digest"
          value={
            `${readBoolean(digestDecision?.triggered) ? "triggered" : "skipped"}`
            + (readString(digestDecision?.reason) ? ` • ${readString(digestDecision?.reason)}` : "")
          }
        />
        <SourceFact
          label="Due before"
          value={
            readNumber(scheduleBefore?.scoped_due_count) !== null
              ? String(readNumber(scheduleBefore?.scoped_due_count))
              : "—"
          }
        />
        <SourceFact
          label="Due after"
          value={
            readNumber(scheduleAfter?.scoped_due_count) !== null
              ? String(readNumber(scheduleAfter?.scoped_due_count))
              : "—"
          }
        />
        <SourceFact
          label="Ingest run"
          value={readNumber(ingestRun?.run_id) !== null ? `#${readNumber(ingestRun?.run_id)}` : "—"}
        />
        <SourceFact
          label="Digest run"
          value={readNumber(digestRun?.run_id) !== null ? `#${readNumber(digestRun?.run_id)}` : "—"}
        />
      </div>
    </section>
  );
}
