import Link from "next/link";
import { notFound } from "next/navigation";

import { getAutoresearchRun, getCurrentUser } from "../../../lib/api";
import { promoteAutoresearchRunAction } from "../actions";

function formatTimestamp(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("en-CA", { dateStyle: "medium", timeStyle: "short" });
}

function readSearchParam(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return typeof value === "string" ? value : null;
}

function StatusPill({ status }: { status: string }) {
  const palette = (() => {
    switch (status) {
      case "kept":
        return { background: "#dcfce7", color: "#166534" };
      case "discarded_no_improvement":
        return { background: "#fef3c7", color: "#854d0e" };
      case "discarded_guardrail":
      case "agent_failed":
        return { background: "#fee2e2", color: "#991b1b" };
      default:
        return { background: "#e2e8f0", color: "#1e293b" };
    }
  })();
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

function JsonBlock({ payload }: { payload: unknown }) {
  return (
    <pre
      style={{
        background: "#0f172a",
        color: "#e2e8f0",
        borderRadius: 8,
        padding: 16,
        fontSize: 12,
        overflowX: "auto",
        maxHeight: 480,
      }}
    >
      {JSON.stringify(payload, null, 2)}
    </pre>
  );
}

type DiffPayload = {
  added_family_codes?: string[];
  removed_family_codes?: string[];
  family_changes?: { code: string; weight?: { before: number; after: number }; patterns_added?: string[]; patterns_removed?: string[] }[];
  thresholds_before?: Record<string, number> | null;
  thresholds_after?: Record<string, number> | null;
  scoring_before?: Record<string, unknown> | null;
  scoring_after?: Record<string, unknown> | null;
};

function DiffSummary({ diff }: { diff: DiffPayload | null | undefined }) {
  if (!diff) {
    return <p style={{ margin: 0, color: "#64748b" }}>No structured diff available.</p>;
  }

  const familyChanges = diff.family_changes ?? [];
  const added = diff.added_family_codes ?? [];
  const removed = diff.removed_family_codes ?? [];

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Added families</p>
          <p style={{ margin: "4px 0 0", fontWeight: 600 }}>
            {added.length ? added.join(", ") : "none"}
          </p>
        </div>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Removed families</p>
          <p style={{ margin: "4px 0 0", fontWeight: 600 }}>
            {removed.length ? removed.join(", ") : "none"}
          </p>
        </div>
      </div>

      {familyChanges.length === 0 ? (
        <p style={{ margin: 0, color: "#64748b" }}>No per-family weight or pattern changes vs. baseline.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: "left", color: "#64748b", textTransform: "uppercase", fontSize: 11 }}>
              <th style={{ padding: 8 }}>Code</th>
              <th style={{ padding: 8 }}>Weight</th>
              <th style={{ padding: 8 }}>Patterns added</th>
              <th style={{ padding: 8 }}>Patterns removed</th>
            </tr>
          </thead>
          <tbody>
            {familyChanges.map((entry) => (
              <tr key={entry.code} style={{ borderTop: "1px solid #e5e7eb" }}>
                <td style={{ padding: 8, fontWeight: 600 }}>{entry.code}</td>
                <td style={{ padding: 8 }}>
                  {entry.weight
                    ? `${entry.weight.before.toFixed(2)} → ${entry.weight.after.toFixed(2)}`
                    : "—"}
                </td>
                <td style={{ padding: 8, color: "#16a34a" }}>
                  {(entry.patterns_added ?? []).join(", ") || "—"}
                </td>
                <td style={{ padding: 8, color: "#b91c1c" }}>
                  {(entry.patterns_removed ?? []).join(", ") || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

type EvalSummary = {
  threshold?: number;
  top_k?: number;
  precision?: number;
  recall?: number;
  f1?: number;
  precision_at_top_k?: number;
  sensitivity_at_top_k?: number;
};

function MetricRow({ label, candidate, baseline }: { label: string; candidate: number | undefined; baseline: number | undefined }) {
  const candidateText = candidate === undefined ? "—" : candidate.toFixed(4);
  const baselineText = baseline === undefined ? "—" : baseline.toFixed(4);
  const delta = candidate === undefined || baseline === undefined ? null : candidate - baseline;
  return (
    <tr style={{ borderTop: "1px solid #e5e7eb" }}>
      <td style={{ padding: 8, fontWeight: 600 }}>{label}</td>
      <td style={{ padding: 8 }}>{candidateText}</td>
      <td style={{ padding: 8 }}>{baselineText}</td>
      <td style={{ padding: 8, color: (delta ?? 0) >= 0 ? "#16a34a" : "#b91c1c" }}>
        {delta === null ? "—" : `${delta > 0 ? "+" : ""}${delta.toFixed(4)}`}
      </td>
    </tr>
  );
}

export default async function AutoresearchRunDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ runId: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { runId } = await params;
  const resolvedSearchParams = searchParams ? await searchParams : undefined;
  const errorMessage = readSearchParam(resolvedSearchParams?.error);
  const infoMessage = readSearchParam(resolvedSearchParams?.info);

  const [detail, currentUser] = await Promise.all([getAutoresearchRun(runId), getCurrentUser()]);
  if (!detail) {
    notFound();
  }

  const canPromote = currentUser?.role === "admin";
  const isPromotable = detail.status === "kept" && !detail.promotion;

  const evalPayload = (detail.eval ?? {}) as {
    candidate?: { rules?: EvalSummary; hybrid?: EvalSummary };
    baseline?: { rules?: EvalSummary; hybrid?: EvalSummary };
    external_sample?: Record<string, unknown> | null;
  };

  const candidateRules = evalPayload.candidate?.rules;
  const baselineRules = evalPayload.baseline?.rules;
  const candidateHybrid = evalPayload.candidate?.hybrid;
  const baselineHybrid = evalPayload.baseline?.hybrid;

  return (
    <main style={{ padding: 32, maxWidth: 1200, margin: "0 auto", color: "#0f172a" }}>
      <header style={{ marginBottom: 24 }}>
        <Link href="/autoresearch" style={{ color: "#2563eb" }}>
          ← All runs
        </Link>
        <h1 style={{ margin: "12px 0 4px", fontSize: 28 }}>Run {detail.run_id}</h1>
        <div style={{ display: "flex", alignItems: "center", gap: 12, color: "#64748b" }}>
          <StatusPill status={detail.status} />
          <span>Created {formatTimestamp(detail.created_at)}</span>
          {detail.promotion ? (
            <span style={{ color: "#16a34a", fontWeight: 600 }}>
              Promoted {formatTimestamp(detail.promotion.promoted_at as string)}
            </span>
          ) : null}
        </div>
      </header>

      {errorMessage ? (
        <div
          style={{
            background: "#fef2f2",
            border: "1px solid #fecaca",
            color: "#991b1b",
            borderRadius: 8,
            padding: 12,
            marginBottom: 16,
          }}
        >
          {errorMessage}
        </div>
      ) : null}
      {infoMessage ? (
        <div
          style={{
            background: "#ecfdf5",
            border: "1px solid #bbf7d0",
            color: "#166534",
            borderRadius: 8,
            padding: 12,
            marginBottom: 16,
          }}
        >
          {infoMessage}
        </div>
      ) : null}

      <section
        style={{
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: 12,
          padding: 20,
          marginBottom: 24,
        }}
      >
        <h2 style={{ marginTop: 0, fontSize: 20 }}>Decision</h2>
        <JsonBlock payload={detail.decision} />
      </section>

      <section
        style={{
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: 12,
          padding: 20,
          marginBottom: 24,
        }}
      >
        <h2 style={{ marginTop: 0, fontSize: 20 }}>Evaluation snapshot</h2>
        <h3 style={{ fontSize: 14, color: "#475569" }}>Demo benchmark, rules score mode</h3>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: "left", color: "#64748b", textTransform: "uppercase", fontSize: 11 }}>
              <th style={{ padding: 8 }}>Metric</th>
              <th style={{ padding: 8 }}>Candidate</th>
              <th style={{ padding: 8 }}>Baseline</th>
              <th style={{ padding: 8 }}>Delta</th>
            </tr>
          </thead>
          <tbody>
            <MetricRow label="Precision" candidate={candidateRules?.precision} baseline={baselineRules?.precision} />
            <MetricRow label="Recall" candidate={candidateRules?.recall} baseline={baselineRules?.recall} />
            <MetricRow label="F1" candidate={candidateRules?.f1} baseline={baselineRules?.f1} />
            <MetricRow
              label="Precision @ top-k"
              candidate={candidateRules?.precision_at_top_k}
              baseline={baselineRules?.precision_at_top_k}
            />
            <MetricRow
              label="Sensitivity @ top-k"
              candidate={candidateRules?.sensitivity_at_top_k}
              baseline={baselineRules?.sensitivity_at_top_k}
            />
          </tbody>
        </table>

        <h3 style={{ fontSize: 14, color: "#475569", marginTop: 16 }}>Demo benchmark, hybrid score mode (visibility)</h3>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: "left", color: "#64748b", textTransform: "uppercase", fontSize: 11 }}>
              <th style={{ padding: 8 }}>Metric</th>
              <th style={{ padding: 8 }}>Candidate</th>
              <th style={{ padding: 8 }}>Baseline</th>
              <th style={{ padding: 8 }}>Delta</th>
            </tr>
          </thead>
          <tbody>
            <MetricRow label="Precision" candidate={candidateHybrid?.precision} baseline={baselineHybrid?.precision} />
            <MetricRow label="Recall" candidate={candidateHybrid?.recall} baseline={baselineHybrid?.recall} />
            <MetricRow label="F1" candidate={candidateHybrid?.f1} baseline={baselineHybrid?.f1} />
          </tbody>
        </table>

        {evalPayload.external_sample ? (
          <>
            <h3 style={{ fontSize: 14, color: "#475569", marginTop: 16 }}>External retrospective sample (static)</h3>
            <JsonBlock payload={evalPayload.external_sample} />
          </>
        ) : null}
      </section>

      <section
        style={{
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: 12,
          padding: 20,
          marginBottom: 24,
        }}
      >
        <h2 style={{ marginTop: 0, fontSize: 20 }}>Diff vs. baseline ontology</h2>
        <DiffSummary diff={detail.diff as DiffPayload | null} />
      </section>

      {detail.notes_markdown ? (
        <section
          style={{
            background: "white",
            border: "1px solid #e5e7eb",
            borderRadius: 12,
            padding: 20,
            marginBottom: 24,
          }}
        >
          <h2 style={{ marginTop: 0, fontSize: 20 }}>Agent notes</h2>
          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", margin: 0 }}>
            {detail.notes_markdown}
          </pre>
        </section>
      ) : null}

      <section
        style={{
          background: "white",
          border: "1px solid #e5e7eb",
          borderRadius: 12,
          padding: 20,
          marginBottom: 24,
        }}
      >
        <h2 style={{ marginTop: 0, fontSize: 20 }}>Promotion</h2>
        {detail.promotion ? (
          <>
            <p style={{ margin: 0, color: "#475569" }}>
              This run was promoted into the live ontology at{" "}
              {formatTimestamp(detail.promotion.promoted_at as string)}.
            </p>
            <JsonBlock payload={detail.promotion} />
          </>
        ) : isPromotable && canPromote ? (
          <form action={promoteAutoresearchRunAction} style={{ display: "grid", gap: 12 }}>
            <input type="hidden" name="run_id" value={detail.run_id} />
            <p style={{ margin: 0, color: "#475569" }}>
              Promotion will copy <code>proposal.json</code> into{" "}
              <code>data/ontologies/pancreatic_signal_rules.json</code> and write provenance to{" "}
              <code>autoresearch/runs/{detail.run_id}/promotion.json</code>.
            </p>
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
                width: "fit-content",
              }}
            >
              Promote into live ontology
            </button>
          </form>
        ) : isPromotable ? (
          <p style={{ margin: 0, color: "#64748b" }}>
            This run is promotable, but your role does not include the <code>admin</code>{" "}
            capability required to promote.
          </p>
        ) : (
          <p style={{ margin: 0, color: "#64748b" }}>
            This run is not promotable (status: <strong>{detail.status}</strong>).
          </p>
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
        <h2 style={{ marginTop: 0, fontSize: 20 }}>Raw artifacts</h2>
        <details>
          <summary style={{ cursor: "pointer", fontWeight: 600 }}>proposal.json</summary>
          <JsonBlock payload={detail.proposal} />
        </details>
        {detail.proposal_meta ? (
          <details>
            <summary style={{ cursor: "pointer", fontWeight: 600 }}>proposal_meta.json</summary>
            <JsonBlock payload={detail.proposal_meta} />
          </details>
        ) : null}
        <details>
          <summary style={{ cursor: "pointer", fontWeight: 600 }}>eval.json</summary>
          <JsonBlock payload={detail.eval} />
        </details>
        <details>
          <summary style={{ cursor: "pointer", fontWeight: 600 }}>diff.json</summary>
          <JsonBlock payload={detail.diff} />
        </details>
      </section>
    </main>
  );
}
