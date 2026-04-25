import Link from "next/link";

import {
  getAutoresearchLeaderboard,
  getAutoresearchRuns,
  getCurrentUser,
} from "../../lib/api";
import type { AutoresearchRunSummary } from "../../lib/api";

function formatTimestamp(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("en-CA", { dateStyle: "medium", timeStyle: "short" });
}

function formatNumber(value: number | null | undefined, digits = 4): string {
  if (value === null || value === undefined) return "—";
  return value.toFixed(digits);
}

function formatSignedNumber(value: number | null | undefined, digits = 4): string {
  if (value === null || value === undefined) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}`;
}

function statusColor(status: string): { background: string; color: string } {
  switch (status) {
    case "kept":
      return { background: "#dcfce7", color: "#166534" };
    case "discarded_no_improvement":
      return { background: "#fef3c7", color: "#854d0e" };
    case "discarded_guardrail":
      return { background: "#fee2e2", color: "#991b1b" };
    case "agent_failed":
      return { background: "#fee2e2", color: "#7f1d1d" };
    default:
      return { background: "#e2e8f0", color: "#1e293b" };
  }
}

function StatusPill({ status }: { status: string }) {
  const palette = statusColor(status);
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 10px",
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 600,
        ...palette,
      }}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}

function RunRow({ run }: { run: AutoresearchRunSummary }) {
  return (
    <tr style={{ borderTop: "1px solid #e5e7eb" }}>
      <td style={{ padding: 12 }}>
        <Link
          href={`/autoresearch/${encodeURIComponent(run.run_id)}`}
          style={{ color: "#2563eb", fontWeight: 600 }}
        >
          {run.run_id}
        </Link>
        {run.promoted_at ? (
          <p style={{ margin: "4px 0 0", fontSize: 11, color: "#16a34a" }}>
            Promoted {formatTimestamp(run.promoted_at)}
          </p>
        ) : null}
      </td>
      <td style={{ padding: 12 }}>
        <StatusPill status={run.status} />
      </td>
      <td style={{ padding: 12 }}>{formatNumber(run.primary_value)}</td>
      <td style={{ padding: 12 }}>{formatNumber(run.baseline_value)}</td>
      <td style={{ padding: 12, color: (run.delta ?? 0) >= 0 ? "#16a34a" : "#b91c1c" }}>
        {formatSignedNumber(run.delta)}
      </td>
      <td style={{ padding: 12, fontSize: 12, color: "#475569" }}>
        {run.notes_summary || "—"}
      </td>
      <td style={{ padding: 12, fontSize: 12, color: "#64748b" }}>
        {formatTimestamp(run.created_at)}
      </td>
    </tr>
  );
}

export default async function AutoresearchPage() {
  const [runs, leaderboard, currentUser] = await Promise.all([
    getAutoresearchRuns({ limit: 100 }),
    getAutoresearchLeaderboard(5),
    getCurrentUser(),
  ]);

  const canPromote = currentUser?.role === "admin";

  return (
    <main style={{ padding: 32, maxWidth: 1200, margin: "0 auto", color: "#0f172a" }}>
      <header style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#6b7280" }}>Lab</p>
          <h1 style={{ margin: "8px 0 0", fontSize: 32 }}>Autoresearch runs</h1>
          <p style={{ margin: "8px 0 0", color: "#475569", maxWidth: 720 }}>
            Opt-in lab subsystem inspired by{" "}
            <a href="https://github.com/karpathy/autoresearch" style={{ color: "#2563eb" }}>
              karpathy/autoresearch
            </a>
            . An external coding agent proposes candidate edits to{" "}
            <code>data/ontologies/pancreatic_signal_rules.json</code>; the deterministic experiment
            driver decides whether each candidate is kept, discarded, or promoted. Triage, imports,
            and the worklist remain the primary product surfaces.
          </p>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <Link href="/cases" style={{ color: "#2563eb" }}>
            Worklist
          </Link>
          <Link href="/proof" style={{ color: "#2563eb" }}>
            Benchmark proof
          </Link>
        </div>
      </header>

      <section
        style={{
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: 12,
          padding: 20,
          marginBottom: 24,
        }}
      >
        <h2 style={{ marginTop: 0, fontSize: 20 }}>Top kept runs ({leaderboard.primary_metric})</h2>
        {leaderboard.runs.length === 0 ? (
          <p style={{ margin: 0, color: "#64748b" }}>
            No kept runs yet. Run <code>make autoresearch-loop ITERATIONS=1 AGENT_CMD=&quot;...&quot;</code> to
            propose a candidate, or <code>make autoresearch-once</code> to evaluate a manual edit.
          </p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", color: "#64748b", fontSize: 12, textTransform: "uppercase" }}>
                <th style={{ padding: 12 }}>Run</th>
                <th style={{ padding: 12 }}>Status</th>
                <th style={{ padding: 12 }}>F1</th>
                <th style={{ padding: 12 }}>Baseline F1</th>
                <th style={{ padding: 12 }}>Delta</th>
                <th style={{ padding: 12 }}>Notes</th>
                <th style={{ padding: 12 }}>Created</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.runs.map((run) => (
                <RunRow key={run.run_id} run={run} />
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section
        style={{
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: 12,
          padding: 20,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>All runs ({runs.length})</h2>
          {canPromote ? (
            <span style={{ fontSize: 12, color: "#16a34a", fontWeight: 600 }}>
              You can promote kept runs.
            </span>
          ) : (
            <span style={{ fontSize: 12, color: "#64748b" }}>
              Promotion requires the admin role.
            </span>
          )}
        </div>

        {runs.length === 0 ? (
          <p style={{ margin: 0, color: "#64748b" }}>
            No runs recorded yet. Append-only run history will appear here once an experiment finishes.
          </p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", color: "#64748b", fontSize: 12, textTransform: "uppercase" }}>
                <th style={{ padding: 12 }}>Run</th>
                <th style={{ padding: 12 }}>Status</th>
                <th style={{ padding: 12 }}>F1</th>
                <th style={{ padding: 12 }}>Baseline F1</th>
                <th style={{ padding: 12 }}>Delta</th>
                <th style={{ padding: 12 }}>Notes</th>
                <th style={{ padding: 12 }}>Created</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <RunRow key={run.run_id} run={run} />
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}
