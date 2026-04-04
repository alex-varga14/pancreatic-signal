import Link from "next/link";
import type { CSSProperties } from "react";

import { getResearchDigest } from "../../../../lib/api";


const panelStyle: CSSProperties = {
  background: "white",
  border: "1px solid #e5e7eb",
  borderRadius: 14,
  padding: 20,
};

const badgeStyle: CSSProperties = {
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


function formatDateTime(value?: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}


function formatSigned(value?: number | null, digits = 2): string {
  if (value === undefined || value === null) return "n/a";
  return `${value >= 0 ? "+" : ""}${value.toFixed(digits)}`;
}


function humanizeToken(value: string): string {
  return value.replaceAll("_", " ");
}


function TokenList({ items }: { items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div style={{ marginTop: 10 }}>
      {items.map((item) => (
        <span key={item} style={badgeStyle}>
          {humanizeToken(item)}
        </span>
      ))}
    </div>
  );
}


function LabeledList({
  title,
  items,
  emptyLabel,
}: {
  title: string;
  items: string[];
  emptyLabel?: string;
}) {
  if (items.length === 0 && !emptyLabel) return null;
  return (
    <div style={{ marginTop: 14 }}>
      <p style={{ margin: "0 0 8px", fontWeight: 600 }}>{title}</p>
      {items.length > 0 ? (
        <ul style={{ paddingLeft: 18, margin: 0, color: "#334155" }}>
          {items.map((item) => (
            <li key={item} style={{ marginBottom: 8, lineHeight: 1.6 }}>
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p style={{ margin: 0, color: "#64748b" }}>{emptyLabel}</p>
      )}
    </div>
  );
}


export default async function ResearchDigestDetailPage({
  params,
}: {
  params: Promise<{ digestId: string }>;
}) {
  const { digestId } = await params;
  const digest = await getResearchDigest(digestId);

  if (!digest) {
    return (
      <main style={{ padding: 32 }}>
        <p>Digest not found.</p>
        <Link href="/research-intel/digests">Back to digests</Link>
      </main>
    );
  }

  return (
    <main style={{ padding: 32, maxWidth: 1120, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", marginBottom: 20 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Research Intelligence digest</p>
          <h1 style={{ margin: "8px 0 0", fontSize: 32 }}>{digest.title}</h1>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <Link href="/research-intel/digests" style={{ color: "#2563eb" }}>Back to digests</Link>
          <Link href="/research-intel/opportunities" style={{ color: "#2563eb" }}>Opportunities</Link>
        </div>
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))" }}>
        <section style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>Published summary</h2>
          <pre
            style={{
              margin: 0,
              whiteSpace: "pre-wrap",
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
              lineHeight: 1.6,
              color: "#0f172a",
            }}
          >
            {digest.summary_markdown}
          </pre>
        </section>

        <section style={{ display: "grid", gap: 16 }}>
          <div style={panelStyle}>
            <h2 style={{ marginTop: 0 }}>Summary</h2>
            <p><strong>Generated:</strong> {formatDateTime(digest.generated_at)}</p>
            <p><strong>Window:</strong> {formatDateTime(digest.window_start)} to {formatDateTime(digest.window_end)}</p>
            <p><strong>Topics:</strong> {digest.topic_labels.join(", ") || "unbucketed"}</p>
            <p><strong>Disagreement:</strong> {digest.disagreement_score.toFixed(2)}</p>
            <p><strong>Citations:</strong> {digest.citation_count}</p>
            <p><strong>Overall confidence:</strong> {digest.council.stage_3.overall_confidence}</p>
            <p><strong>Confidence trend:</strong> {digest.trend.confidence_trend}</p>
          </div>

          <div style={panelStyle}>
            <h2 style={{ marginTop: 0 }}>Key takeaways</h2>
            <ul style={{ paddingLeft: 18, margin: 0 }}>
              {digest.key_takeaways.map((item) => (
                <li key={item} style={{ marginBottom: 8 }}>{item}</li>
              ))}
            </ul>
          </div>

          <div style={panelStyle}>
            <h2 style={{ marginTop: 0 }}>Supporting documents</h2>
            <ul style={{ paddingLeft: 18, margin: 0 }}>
              {digest.supporting_documents.map((document) => (
                <li key={document.document_id} style={{ marginBottom: 10, lineHeight: 1.6 }}>
                  <strong>{document.title}</strong> ({document.citation_key})
                  {document.topic_labels.length > 0 ? ` • ${document.topic_labels.join(", ")}` : ""}
                </li>
              ))}
            </ul>
          </div>
        </section>
      </div>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", marginTop: 16 }}>
        {digest.council.stage_1.map((item) => (
          <section key={item.persona} style={panelStyle}>
            <p style={{ margin: 0, fontSize: 12, textTransform: "uppercase", color: "#64748b" }}>Council stage 1</p>
            <h2 style={{ margin: "8px 0 0", fontSize: 24 }}>{humanizeToken(item.persona)}</h2>
            <p style={{ color: "#334155", lineHeight: 1.7 }}>{item.summary}</p>
            <TokenList items={[item.confidence_label, ...item.proposed_opportunity_types]} />
            <TokenList items={item.primary_topics} />
            <LabeledList title="Key claims" items={item.key_claims} />
            <LabeledList title="Open questions" items={item.open_questions} />
            <LabeledList title="Evidence gaps" items={item.evidence_gaps} />
            <LabeledList
              title="Citations"
              items={item.citations}
              emptyLabel="No citations were recorded for this opinion."
            />
          </section>
        ))}
      </div>

      <section style={{ ...panelStyle, marginTop: 16 }}>
        <h2 style={{ marginTop: 0 }}>Council stage 2</h2>
        <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))" }}>
          {digest.council.stage_2.map((item) => (
            <article
              key={item.persona}
              style={{ border: "1px solid #e2e8f0", borderRadius: 12, padding: 18, background: "#f8fafc" }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "baseline" }}>
                <h3 style={{ margin: 0 }}>{humanizeToken(item.persona)}</h3>
                <span style={{ color: "#475569", fontSize: 13 }}>
                  confidence {item.confidence_adjustment}
                </span>
              </div>
              <p style={{ color: "#334155", lineHeight: 1.7 }}>{item.critique}</p>
              <TokenList items={item.ranked_topics} />
              <TokenList items={item.ranked_opportunity_types} />
              {item.challenge_target_persona ? (
                <p style={{ margin: "10px 0 0", color: "#475569" }}>
                  <strong>Challenges:</strong> {humanizeToken(item.challenge_target_persona)}
                </p>
              ) : null}
              <LabeledList title="Preferred actions" items={item.preferred_actions} />
              <div style={{ marginTop: 14 }}>
                <p style={{ margin: "0 0 8px", fontWeight: 600 }}>Peer critique</p>
                {item.peer_critiques.length > 0 ? (
                  <div style={{ display: "grid", gap: 12 }}>
                    {item.peer_critiques.map((critique) => (
                      <div
                        key={`${critique.reviewer_persona}-${critique.target_persona}`}
                        style={{ border: "1px solid #cbd5e1", borderRadius: 10, padding: 14, background: "white" }}
                      >
                        <p style={{ margin: 0, color: "#0f172a" }}>
                          <strong>{humanizeToken(critique.reviewer_persona)}</strong> on{" "}
                          <strong>{humanizeToken(critique.target_persona)}</strong> ({critique.alignment})
                        </p>
                        <LabeledList title="Strengths" items={critique.strengths} />
                        <LabeledList title="Concerns" items={critique.concerns} />
                        <LabeledList title="Requested evidence" items={critique.requested_evidence} />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ margin: 0, color: "#64748b" }}>No peer critique was recorded.</p>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section style={{ ...panelStyle, marginTop: 16 }}>
        <h2 style={{ marginTop: 0 }}>Across runs</h2>
        <p style={{ color: "#334155", lineHeight: 1.7 }}>
          Previous digest: {digest.trend.previous_digest_id || "none"} {" • "}
          disagreement delta {formatSigned(digest.trend.disagreement_delta)} {" • "}
          citation delta {formatSigned(digest.trend.citation_delta ?? null, 0)}
        </p>
        <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
          <LabeledList title="New topics" items={digest.trend.new_topic_labels} />
          <LabeledList title="Persistent topics" items={digest.trend.persistent_topic_labels} />
          <LabeledList title="Dropped topics" items={digest.trend.dropped_topic_labels} />
          <LabeledList
            title="Resolved open questions"
            items={digest.history.resolved_open_questions}
            emptyLabel="No previously open questions resolved in this digest window."
          />
          <LabeledList
            title="Resolved disagreement"
            items={digest.history.resolved_disagreement_points}
            emptyLabel="No previously recorded disagreement points resolved in this digest window."
          />
        </div>
        {digest.history.recurring_open_questions.length > 0 ? (
          <div style={{ marginTop: 16 }}>
            <p style={{ margin: "0 0 8px", fontWeight: 600 }}>Recurring open questions</p>
            <ul style={{ paddingLeft: 18, margin: 0, color: "#334155" }}>
              {digest.history.recurring_open_questions.map((item) => (
                <li key={item.text} style={{ marginBottom: 8, lineHeight: 1.6 }}>
                  {item.text} ({item.occurrence_count} digests)
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {digest.history.recurring_disagreement_points.length > 0 ? (
          <div style={{ marginTop: 16 }}>
            <p style={{ margin: "0 0 8px", fontWeight: 600 }}>Recurring disagreement points</p>
            <ul style={{ paddingLeft: 18, margin: 0, color: "#334155" }}>
              {digest.history.recurring_disagreement_points.map((item) => (
                <li key={item.text} style={{ marginBottom: 8, lineHeight: 1.6 }}>
                  {item.text} ({item.occurrence_count} digests)
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {digest.history.recent_digests.length > 0 ? (
          <div style={{ marginTop: 16 }}>
            <p style={{ margin: "0 0 8px", fontWeight: 600 }}>Recent digest window</p>
            <div style={{ display: "grid", gap: 10 }}>
              {digest.history.recent_digests.map((item) => (
                <div key={item.digest_id} style={{ border: "1px solid #e2e8f0", borderRadius: 10, padding: 12, background: "#f8fafc" }}>
                  <p style={{ margin: 0, color: "#0f172a" }}>
                    <strong>{item.digest_id}</strong> • {formatDateTime(item.generated_at)}
                  </p>
                  <p style={{ margin: "6px 0 0", color: "#475569" }}>
                    confidence {item.overall_confidence} • disagreement {item.disagreement_score.toFixed(2)} • citations {item.citation_count}
                  </p>
                  <p style={{ margin: "6px 0 0", color: "#64748b" }}>
                    {item.topic_labels.join(", ") || "unbucketed"}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </section>

      <section style={{ ...panelStyle, marginTop: 16 }}>
        <h2 style={{ marginTop: 0 }}>Chairman synthesis</h2>
        <TokenList items={[digest.council.stage_3.overall_confidence]} />
        <p style={{ color: "#334155", lineHeight: 1.7 }}>{digest.council.stage_3.chairman_summary}</p>
        <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
          <LabeledList title="Consensus" items={digest.council.stage_3.consensus_points} />
          <LabeledList title="Disagreement" items={digest.council.stage_3.disagreement_points} />
          <LabeledList title="Open questions" items={digest.council.stage_3.open_questions} />
          <LabeledList title="Evidence gaps" items={digest.council.stage_3.evidence_gaps} />
          <LabeledList title="Recommended actions" items={digest.council.stage_3.recommended_actions} />
          <LabeledList title="Next experiments" items={digest.council.stage_3.next_experiments} />
          <LabeledList title="Promotion guardrails" items={digest.council.stage_3.promotion_guardrails} />
        </div>
      </section>
    </main>
  );
}
