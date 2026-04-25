/* eslint-disable no-console */
"use strict";

const http = require("http");
const { URL } = require("url");

const PORT = Number(process.env.MOCK_API_PORT || 3199);

const CURRENT_USER = {
  user_id: "demo-reviewer",
  display_name: "Demo Reviewer",
  role: "admin",
  auth_mode: "mock",
  provider: "mock",
  site_scope: null,
  capabilities: {
    can_view_cases: true,
    can_review_cases: true,
    can_submit_feedback: true,
    can_import_reports: true,
    can_export_data: true,
    can_view_feedback_summary: true,
  },
};

const CASE_LIST = [
  {
    case_id: "C-E2E-1",
    report_id: "R-E2E-1",
    report_datetime: "2026-03-19T10:00:00Z",
    modality: "CT",
    score: 0.86,
    urgency: "high",
    status: "new",
    site: "Demo Hospital",
    assigned_to: null,
    top_rationale: "PDAC_EXPLICIT_SUSPICION",
    hybrid_score: 0.91,
    hybrid_delta: 0.05,
    hybrid_confidence: "high",
    hybrid_review_priority: "expedite",
    active_learning_priority: "medium",
    disagreement_level: null,
    review_feedback_count: 0,
    latest_feedback_label: null,
    latest_feedback_disposition: null,
  },
  {
    case_id: "C-E2E-2",
    report_id: "R-E2E-2",
    report_datetime: "2026-03-18T09:00:00Z",
    modality: "MRI",
    score: 0.32,
    urgency: "medium",
    status: "new",
    site: "North Clinic",
    assigned_to: null,
    top_rationale: "DUCT_DILATION",
    hybrid_score: 0.4,
    hybrid_delta: 0.08,
    hybrid_confidence: "moderate",
    hybrid_review_priority: "review",
    active_learning_priority: "high",
    disagreement_level: "low",
    review_feedback_count: 0,
    latest_feedback_label: null,
    latest_feedback_disposition: null,
  },
];

const CASE_DETAIL = {
  case_id: "C-E2E-1",
  report_id: "R-E2E-1",
  report_datetime: "2026-03-19T10:00:00Z",
  modality: "CT",
  score: 0.86,
  urgency: "high",
  status: "new",
  site: "Demo Hospital",
  assigned_to: null,
  report_text:
    "Findings: Abrupt cutoff of the pancreatic duct with an ill-defined pancreatic head lesion. Impression: Suspicious for pancreatic neoplasm.",
  import_metadata: null,
  rationale_codes: ["PDAC_EXPLICIT_SUSPICION", "DUCT_CUTOFF"],
  evidence: [
    {
      text: "abrupt cutoff of the pancreatic duct",
      section: "findings",
      start: 11,
      end: 47,
      code: "DUCT_CUTOFF",
      label: "Abrupt pancreatic duct cutoff or interruption",
      sentence_index: 0,
      score_contribution: 0.35,
    },
  ],
  review_actions: [],
  review_feedback: [],
};

const EVALUATION_COMPARISON = {
  threshold: 0.3,
  top_k: 3,
  rules: {
    score_mode: "rules",
    threshold: 0.3,
    top_k: 3,
    processed: 12,
    positives: 6,
    flagged: 5,
    true_positives: 5,
    false_positives: 0,
    true_negatives: 6,
    false_negatives: 1,
    precision: 1.0,
    recall: 0.83,
    f1: 0.91,
    precision_at_top_k: 1.0,
    sensitivity_at_top_k: 0.5,
    reviewer_yield_at_top_k: 1.0,
    false_negative_buckets: {},
    cases: [],
  },
  hybrid: {
    score_mode: "hybrid",
    threshold: 0.3,
    top_k: 3,
    processed: 12,
    positives: 6,
    flagged: 6,
    true_positives: 6,
    false_positives: 0,
    true_negatives: 6,
    false_negatives: 0,
    precision: 1.0,
    recall: 1.0,
    f1: 1.0,
    precision_at_top_k: 1.0,
    sensitivity_at_top_k: 0.5,
    reviewer_yield_at_top_k: 1.0,
    false_negative_buckets: {},
    cases: [],
  },
  flagged_delta: 1,
  precision_delta: 0,
  recall_delta: 0.17,
  f1_delta: 0.09,
  precision_at_top_k_delta: 0,
  sensitivity_at_top_k_delta: 0,
  newly_flagged_cases: ["C-E2E-2"],
  resolved_false_negatives: ["C-E2E-2"],
};

const EVALUATION_SWEEP = {
  top_k: 3,
  thresholds: [0.2, 0.3, 0.4],
  points: [
    {
      threshold: 0.2,
      rules_f1: 0.85,
      hybrid_f1: 0.92,
      rules_recall: 0.83,
      hybrid_recall: 1.0,
      rules_flagged: 6,
      hybrid_flagged: 7,
      f1_delta: 0.07,
      recall_delta: 0.17,
      flagged_delta: 1,
    },
    {
      threshold: 0.3,
      rules_f1: 0.91,
      hybrid_f1: 1.0,
      rules_recall: 0.83,
      hybrid_recall: 1.0,
      rules_flagged: 5,
      hybrid_flagged: 6,
      f1_delta: 0.09,
      recall_delta: 0.17,
      flagged_delta: 1,
    },
    {
      threshold: 0.4,
      rules_f1: 0.86,
      hybrid_f1: 0.95,
      rules_recall: 0.67,
      hybrid_recall: 0.83,
      rules_flagged: 4,
      hybrid_flagged: 5,
      f1_delta: 0.09,
      recall_delta: 0.16,
      flagged_delta: 1,
    },
  ],
  rules_recommendation: {
    score_mode: "rules",
    recommended_threshold: 0.3,
    rationale: "Best F1 with full recall.",
    f1: 0.91,
    recall: 0.83,
    flagged: 5,
  },
  hybrid_recommendation: {
    score_mode: "hybrid",
    recommended_threshold: 0.3,
    rationale: "Hybrid keeps perfect recall and best F1 here.",
    f1: 1.0,
    recall: 1.0,
    flagged: 6,
  },
};

const FEEDBACK_SUMMARY = {
  total_feedback: 0,
  labeled_cases: 0,
  unlabeled_cases: 2,
  unlabeled_active_learning_cases: 1,
  label_distribution: {},
  disposition_distribution: {},
  error_bucket_distribution: {},
};

function jsonResponse(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, {
    "content-type": "application/json",
    "content-length": Buffer.byteLength(body),
  });
  res.end(body);
}

function notFound(res) {
  jsonResponse(res, 404, { detail: "Not found" });
}

async function readBody(req) {
  return new Promise((resolve) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
  });
}

const server = http.createServer(async (req, res) => {
  const requestUrl = new URL(req.url, `http://localhost:${PORT}`);
  const pathname = requestUrl.pathname;
  const method = req.method || "GET";

  if (pathname === "/health" && method === "GET") {
    return jsonResponse(res, 200, { status: "ok", service: "mock-api" });
  }
  if (pathname === "/api/v1/auth/me" && method === "GET") {
    return jsonResponse(res, 200, CURRENT_USER);
  }
  if (pathname === "/api/v1/cases" && method === "GET") {
    const filtered = CASE_LIST.filter((item) => {
      const status = requestUrl.searchParams.get("status");
      if (status && item.status !== status) {
        return false;
      }
      const urgency = requestUrl.searchParams.get("urgency");
      if (urgency && item.urgency !== urgency) {
        return false;
      }
      return true;
    });
    return jsonResponse(res, 200, filtered);
  }
  if (pathname === "/api/v1/cases/C-E2E-1" && method === "GET") {
    return jsonResponse(res, 200, CASE_DETAIL);
  }
  if (pathname === "/api/v1/cases/C-E2E-1/review" && method === "POST") {
    await readBody(req);
    return jsonResponse(res, 200, {
      ok: true,
      case_id: "C-E2E-1",
      action: "in_review",
      status: "in_review",
      assigned_to: "demo-reviewer",
    });
  }
  if (pathname === "/api/v1/metrics/evaluation/compare" && method === "GET") {
    return jsonResponse(res, 200, EVALUATION_COMPARISON);
  }
  if (pathname === "/api/v1/metrics/evaluation/sweep" && method === "GET") {
    return jsonResponse(res, 200, EVALUATION_SWEEP);
  }
  if (pathname === "/api/v1/metrics/feedback" && method === "GET") {
    return jsonResponse(res, 200, FEEDBACK_SUMMARY);
  }
  if (pathname === "/api/v1/imports/runs" && method === "GET") {
    return jsonResponse(res, 200, []);
  }
  if (pathname === "/api/v1/imports/reports" && method === "POST") {
    await readBody(req);
    res.writeHead(400, {
      "content-type": "application/json",
      "x-import-run-id": "0",
    });
    res.end(
      JSON.stringify({
        detail: "Mock API rejected the upload because the payload was empty.",
      }),
    );
    return;
  }

  return notFound(res);
});

server.listen(PORT, () => {
  console.log(`mock-api: listening on http://127.0.0.1:${PORT}`);
});

process.on("SIGINT", () => {
  server.close(() => process.exit(0));
});
process.on("SIGTERM", () => {
  server.close(() => process.exit(0));
});
