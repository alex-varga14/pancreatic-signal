export type CaseListItem = {
  case_id: string;
  report_id: string;
  report_datetime?: string | null;
  modality?: string | null;
  score: number;
  urgency: string;
  status: string;
  site?: string | null;
  assigned_to?: string | null;
  top_rationale?: string | null;
  hybrid_score?: number | null;
  hybrid_delta?: number | null;
  hybrid_confidence?: string | null;
  hybrid_review_priority?: string | null;
  active_learning_priority?: string | null;
  disagreement_level?: string | null;
  review_feedback_count?: number;
  latest_feedback_label?: string | null;
  latest_feedback_disposition?: string | null;
};

export type ImportMetadata = {
  patient_identifier?: string | null;
  encounter_identifier?: string | null;
  accession_number?: string | null;
  ordering_provider?: string | null;
  source_system?: string | null;
  source_format?: string | null;
  import_source_id?: string | null;
};

export type ImportFailureBucket =
  | "parse_error"
  | "validation_error"
  | "unsupported_payload"
  | "site_scope_rejection";

export type ReportImportSummary = {
  run_id?: number | null;
  processed: number;
  flagged: number;
  created: number;
  updated: number;
  failed: number;
  failure_counts: Partial<Record<ImportFailureBucket, number>>;
  source_format: string;
  case_ids: string[];
  report_ids: string[];
};

export type ImportAuditItem = {
  item_index: number;
  status: "imported" | "failed";
  source_identifier?: string | null;
  site?: string | null;
  case_id?: string | null;
  report_id?: string | null;
  error_bucket?: ImportFailureBucket | null;
  error_detail?: string | null;
};

export type ImportRunSummary = {
  run_id: number;
  source_format: string;
  source_name?: string | null;
  actor_user_id: string;
  actor_role: string;
  actor_site_scope?: string[] | null;
  imported_sites: string[];
  status: "completed" | "failed";
  processed: number;
  flagged: number;
  created: number;
  updated: number;
  failed: number;
  failure_counts: Partial<Record<ImportFailureBucket, number>>;
  started_at: string;
  completed_at: string;
};

export type ImportRunDetail = ImportRunSummary & {
  items: ImportAuditItem[];
};

export type CaseDetail = {
  case_id: string;
  report_id: string;
  report_datetime?: string | null;
  modality?: string | null;
  score: number;
  urgency: string;
  status: string;
  site?: string | null;
  assigned_to?: string | null;
  report_text: string;
  import_metadata?: ImportMetadata | null;
  rationale_codes: string[];
  evidence: {
    text: string;
    code: string;
    section?: string;
    start: number;
    end: number;
    sentence_index?: number | null;
  }[];
  review_actions: {
    action: string;
    reviewer: string;
    note?: string;
    assigned_to?: string | null;
    created_at: string;
  }[];
  review_feedback: {
    reviewer: string;
    label: string;
    disposition: string;
    error_bucket?: string | null;
    notes?: string | null;
    created_at: string;
  }[];
};

export type RedactionSummary = {
  mode: string;
  redaction_count: number;
  redacted_characters: number;
  categories: Record<string, number>;
  pseudonymized_fields: string[];
};

export type ResearchCaseDetail = {
  case_id: string;
  report_id: string;
  report_date?: string | null;
  modality?: string | null;
  score: number;
  urgency: string;
  status: string;
  site?: string | null;
  assigned_to?: string | null;
  report_text: string;
  import_metadata?: ImportMetadata | null;
  rationale_codes: string[];
  evidence: {
    text: string;
    code: string;
    section?: string;
    start: number;
    end: number;
    sentence_index?: number | null;
  }[];
  review_actions: {
    action: string;
    reviewer: string;
    note?: string | null;
    assigned_to?: string | null;
    created_date: string;
  }[];
  review_feedback: {
    reviewer: string;
    label: string;
    disposition: string;
    error_bucket?: string | null;
    notes?: string | null;
    created_date: string;
  }[];
  redaction_summary: RedactionSummary;
  deidentified: boolean;
};

export type CaseFilters = {
  status?: string;
  urgency?: string;
  site?: string;
  reviewer?: string;
  modality?: string;
  rationale?: string;
  feedback_label?: string;
  needs_feedback?: boolean;
  disagreement_only?: boolean;
  hybrid_delta_min?: number;
  hybrid_review_priority?: string;
  active_learning_priority?: string;
  active_learning_only?: boolean;
  include_hybrid?: boolean;
  q?: string;
  sort_by?: string;
  sort_dir?: string;
  limit?: number;
  offset?: number;
};

export type CurrentUser = {
  user_id: string;
  display_name: string;
  role: string;
  auth_mode: "mock" | "header" | "proxy";
  provider: string;
  site_scope?: string[] | null;
  capabilities: {
    can_view_cases: boolean;
    can_review_cases: boolean;
    can_submit_feedback: boolean;
    can_import_reports: boolean;
    can_export_data: boolean;
    can_view_feedback_summary: boolean;
    can_manage_research_intel: boolean;
    can_promote_research_intel: boolean;
  };
};

export type ReviewActionPayload = {
  action: string;
  reviewer?: string;
  note?: string;
  assigned_to?: string;
};

export type ReviewFeedbackPayload = {
  reviewer?: string;
  label: string;
  disposition: string;
  error_bucket?: string;
  notes?: string;
};

export type FeedbackRecommendation = {
  case_id: string;
  recommended_label: string;
  recommended_disposition: string;
  recommended_error_bucket?: string | null;
  confidence: string;
  rationale: string;
  reasons: string[];
  suggested_notes?: string | null;
  already_labeled: boolean;
  latest_feedback_label?: string | null;
  latest_feedback_disposition?: string | null;
};

export type TrialAbstraction = {
  modality: string;
  suspected_pdac: boolean;
  pancreatic_mass: boolean;
  duct_cutoff: boolean;
  duct_dilation: boolean;
  double_duct_sign: boolean;
  focal_atrophy: boolean;
  followup_recommended: boolean;
  eus_recommended: boolean;
  biopsy_recommended: boolean;
  needs_tissue_confirmation: boolean;
  pancreatic_head_focus: boolean;
  pancreatic_tail_focus: boolean;
  secondary_signs_present: boolean;
  high_risk_pancreatic_signal: boolean;
  metastatic_language_present: boolean;
  localized_disease_suspected: boolean;
};

export type TrialCriterionTrace = {
  id: string;
  label: string;
  status: string;
  rationale: string;
  evidence: string[];
};

export type TrialCandidate = {
  trial_id: string;
  title: string;
  source: string;
  summary: string;
  match_score: number;
  match_status: string;
  rationale: string;
  criteria: TrialCriterionTrace[];
};

export type TrialMatchResponse = {
  case_id: string;
  abstraction: TrialAbstraction;
  matches: TrialCandidate[];
};

export type SentenceSignal = {
  code: string;
  label: string;
  weight: number;
  rationale: string;
};

export type SentenceCandidate = {
  text: string;
  section: string;
  sentence_index: number;
  score: number;
  classification: string;
  matched_codes: string[];
  signals: SentenceSignal[];
};

export type HybridAnalysis = {
  calibrated_score: number;
  confidence_label: string;
  review_priority: string;
  active_learning_priority: string;
  summary: string;
  factors: string[];
  sentence_candidates: SentenceCandidate[];
};

export type EvaluationCaseResult = {
  report_id: string;
  case_id: string;
  score: number;
  base_score: number;
  hybrid_score: number;
  urgency: string;
  flagged: boolean;
  expected_positive: boolean;
  expected_escalation: boolean;
  rationale_codes: string[];
  label_notes?: string | null;
  benchmark_bucket?: string | null;
  reviewer_focus?: string | null;
  expected_rationale_codes: string[];
};

export type EvaluationSummary = {
  score_mode: "rules" | "hybrid" | "external";
  threshold: number;
  top_k: number;
  processed: number;
  positives: number;
  flagged: number;
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1: number;
  precision_at_top_k: number;
  sensitivity_at_top_k: number;
  reviewer_yield_at_top_k: number;
  false_negative_buckets: Record<string, number>;
  cases: EvaluationCaseResult[];
};

export type EvaluationComparison = {
  threshold: number;
  top_k: number;
  rules: EvaluationSummary;
  hybrid: EvaluationSummary;
  flagged_delta: number;
  precision_delta: number;
  recall_delta: number;
  f1_delta: number;
  precision_at_top_k_delta: number;
  sensitivity_at_top_k_delta: number;
  newly_flagged_cases: string[];
  resolved_false_negatives: string[];
};

export type ThresholdSweepPoint = {
  threshold: number;
  rules_f1: number;
  hybrid_f1: number;
  rules_recall: number;
  hybrid_recall: number;
  rules_flagged: number;
  hybrid_flagged: number;
  f1_delta: number;
  recall_delta: number;
  flagged_delta: number;
};

export type ThresholdRecommendation = {
  score_mode: "rules" | "hybrid";
  recommended_threshold: number;
  rationale: string;
  f1: number;
  recall: number;
  flagged: number;
};

export type ThresholdSweepSummary = {
  top_k: number;
  thresholds: number[];
  points: ThresholdSweepPoint[];
  rules_recommendation: ThresholdRecommendation;
  hybrid_recommendation: ThresholdRecommendation;
};

export type ExternalThresholdSweepPoint = {
  threshold: number;
  f1: number;
  recall: number;
  flagged: number;
  precision: number;
  precision_at_top_k: number;
  sensitivity_at_top_k: number;
};

export type ExternalThresholdRecommendation = {
  score_mode: "external";
  recommended_threshold: number;
  rationale: string;
  f1: number;
  recall: number;
  flagged: number;
};

export type ExternalThresholdSweepSummary = {
  score_mode: "external";
  top_k: number;
  thresholds: number[];
  points: ExternalThresholdSweepPoint[];
  recommendation: ExternalThresholdRecommendation;
};

export type FeedbackSummary = {
  total_feedback: number;
  labeled_cases: number;
  unlabeled_cases: number;
  unlabeled_active_learning_cases: number;
  label_distribution: Record<string, number>;
  disposition_distribution: Record<string, number>;
  error_bucket_distribution: Record<string, number>;
};

export type ResearchSource = {
  source_id: string;
  label: string;
  source_kind: string;
  trust_level: string;
  access_class: string;
  base_url?: string | null;
  description?: string | null;
  polling_config: Record<string, unknown>;
  enabled: boolean;
  connector_id?: string | null;
  default_mode?: "auto" | "seeded" | "fixture" | "live" | null;
  live_ready: boolean;
  schedule_summary?: string | null;
  health_status: string;
  last_run_at?: string | null;
  last_success_at?: string | null;
  last_error_at?: string | null;
  last_error_detail?: string | null;
  last_document_count?: number | null;
};

export type ResearchRunItem = {
  item_index: number;
  stage: string;
  status: string;
  source_identifier?: string | null;
  document_id?: string | null;
  error_bucket?: string | null;
  error_detail?: string | null;
  created_at: string;
};

export type ResearchRunSummary = {
  run_id: number;
  run_type: string;
  status: string;
  actor_user_id: string;
  source_scope: string[];
  processed: number;
  created: number;
  updated: number;
  failed: number;
  failure_counts: Record<string, number>;
  artifact_paths: string[];
  metadata: Record<string, unknown>;
  started_at: string;
  completed_at: string;
};

export type ResearchRunDetail = ResearchRunSummary & {
  items: ResearchRunItem[];
};

export type ResearchEvidence = {
  evidence_text: string;
  char_start: number;
  char_end: number;
  claim_text: string;
  claim_type: string;
  entity_tags: string[];
  citation_label?: string | null;
  confidence?: number | null;
};

export type ResearchGraphEntity = {
  node_id: string;
  label: string;
  node_type: string;
  description?: string | null;
  tags: string[];
  topic_ids: string[];
  match_terms: string[];
  related_node_ids: string[];
  confidence?: number | null;
};

export type ResearchDocument = {
  document_id: string;
  source_id: string;
  source_label: string;
  source_kind: string;
  document_type: string;
  title: string;
  abstract_text: string;
  url?: string | null;
  canonical_url?: string | null;
  doi?: string | null;
  pmid?: string | null;
  nct_id?: string | null;
  citation_key: string;
  published_at?: string | null;
  authors: string[];
  organizations: string[];
  topic_ids: string[];
  topic_labels: string[];
  entity_tags: string[];
  relevance_scores: Record<string, number>;
  novelty_score?: number | null;
  ingest_mode?: string | null;
  provenance: Record<string, unknown>;
  graph_entities: ResearchGraphEntity[];
  evidence: ResearchEvidence[];
  created_at: string;
  updated_at: string;
};

export type ResearchTopic = {
  topic_id: string;
  label: string;
  description?: string | null;
  keywords: string[];
  related_rationale_codes: string[];
  related_trial_tags: string[];
  opportunity_types: string[];
  topic_heat: number;
  document_count: number;
  last_document_at?: string | null;
  status: string;
};

export type ResearchCouncilStage1Opinion = {
  persona: string;
  focus: string;
  summary: string;
  citations: string[];
  proposed_opportunity_types: string[];
  primary_topics: string[];
  confidence_label: string;
  key_claims: string[];
  open_questions: string[];
  evidence_gaps: string[];
};

export type ResearchCouncilPeerCritique = {
  reviewer_persona: string;
  target_persona: string;
  alignment: string;
  strengths: string[];
  concerns: string[];
  requested_evidence: string[];
};

export type ResearchCouncilStage2Ranking = {
  persona: string;
  ranked_topics: string[];
  ranked_opportunity_types: string[];
  critique: string;
  challenge_target_persona?: string | null;
  peer_critiques: ResearchCouncilPeerCritique[];
  preferred_actions: string[];
  confidence_adjustment: string;
};

export type ResearchCouncilStage3Synthesis = {
  chairman_summary: string;
  overall_confidence: string;
  consensus_points: string[];
  disagreement_points: string[];
  evidence_gaps: string[];
  open_questions: string[];
  recommended_actions: string[];
  next_experiments: string[];
  promotion_guardrails: string[];
};

export type ResearchCouncilPayload = {
  stage_1: ResearchCouncilStage1Opinion[];
  stage_2: ResearchCouncilStage2Ranking[];
  stage_3: ResearchCouncilStage3Synthesis;
};

export type ResearchDigestDocumentRef = {
  document_id: string;
  title: string;
  citation_key: string;
  url?: string | null;
  topic_labels: string[];
};

export type ResearchGraphEdge = {
  source: string;
  target: string;
  relation: string;
  weight?: number | null;
};

export type ResearchGraphNode = {
  node_id: string;
  label: string;
  node_type: string;
  description?: string | null;
  tags: string[];
  topic_ids: string[];
  aliases: string[];
  keywords: string[];
  related_node_ids: string[];
  document_count: number;
  heat: number;
  recent_document_ids: string[];
};

export type ResearchGraphSnapshot = {
  generated_at: string;
  active_node_ids: string[];
  nodes: ResearchGraphNode[];
  edges: ResearchGraphEdge[];
};

export type ResearchDigestListItem = {
  digest_id: string;
  title: string;
  status: string;
  publication_scope: string;
  generated_at: string;
  topic_ids: string[];
  topic_labels: string[];
  disagreement_score: number;
  citation_count: number;
};

export type ResearchDigestDetail = ResearchDigestListItem & {
  window_start?: string | null;
  window_end?: string | null;
  summary_markdown: string;
  key_takeaways: string[];
  supporting_documents: ResearchDigestDocumentRef[];
  council: ResearchCouncilPayload;
};

export type ResearchOpportunityEvidence = {
  document_id: string;
  citation_key: string;
  title: string;
  source_kind?: string | null;
  topic_labels: string[];
  why_it_matters: string;
};

export type ResearchOpportunityArtifactSpec = {
  artifact_kind: string;
  title: string;
  summary: string;
  suggested_path?: string | null;
  target_hint?: "github_issue" | "docs_draft" | "benchmark_task" | null;
};

export type ResearchOpportunityActionPayload = {
  human_gate: boolean;
  digest_id?: string | null;
  objective: string;
  why_now: string;
  discovery_question: string;
  artifact_spec: ResearchOpportunityArtifactSpec;
  evidence_bundle: ResearchOpportunityEvidence[];
  proposed_steps: string[];
  acceptance_gates: string[];
  open_questions: string[];
  evidence_gaps: string[];
  next_experiments: string[];
  measurable_outcomes: string[];
  promotion_guardrails: string[];
  suggested_target: "github_issue" | "docs_draft" | "benchmark_task";
  council_confidence: string;
  council_personas: string[];
  theme_snapshot: string[];
  promoted_by_user_id?: string | null;
  last_promotion_target?: "github_issue" | "docs_draft" | "benchmark_task" | null;
  promotion_artifact_path?: string | null;
};

export type ResearchOpportunity = {
  opportunity_id: string;
  opportunity_type: string;
  title: string;
  summary: string;
  status: string;
  confidence_score: number;
  topic_ids: string[];
  topic_labels: string[];
  supporting_document_ids: string[];
  related_rationale_codes: string[];
  related_trial_ids: string[];
  action_payload: ResearchOpportunityActionPayload;
  promotion_target?: string | null;
  promoted_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type ResearchCaseBriefTopic = {
  topic_id: string;
  label: string;
  rationale: string;
};

export type ResearchCaseBriefDocument = {
  document_id: string;
  title: string;
  citation_key: string;
  url?: string | null;
  relevance_reason: string;
};

export type ResearchCaseBrief = {
  case_id: string;
  summary: string;
  matched_topics: ResearchCaseBriefTopic[];
  supporting_documents: ResearchCaseBriefDocument[];
  suggested_benchmark_gaps: string[];
  suggested_rule_updates: string[];
  suggested_trial_updates: string[];
};

export type ResearchDocumentFilters = {
  source_kind?: string;
  topic?: string;
  q?: string;
  limit?: number;
  offset?: number;
};

const API_BASE = process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const API_USER_ID = process.env.PANCREATIC_SIGNAL_API_USER_ID;
const API_USER_NAME = process.env.PANCREATIC_SIGNAL_API_USER_NAME;
const API_USER_ROLE = process.env.PANCREATIC_SIGNAL_API_USER_ROLE;
const API_USER_SITES = process.env.PANCREATIC_SIGNAL_API_USER_SITES;
const API_TRUSTED_IDENTITY = process.env.PANCREATIC_SIGNAL_API_TRUSTED_IDENTITY;
const API_TRUSTED_IDENTITY_B64 = process.env.PANCREATIC_SIGNAL_API_TRUSTED_IDENTITY_B64;
const API_TRUSTED_IDENTITY_HEADER_NAME =
  process.env.PANCREATIC_SIGNAL_API_TRUSTED_IDENTITY_HEADER_NAME || "X-Trusted-Identity";

export class ApiRequestError extends Error {
  status: number;
  runId: number | null;

  constructor(message: string, status: number, runId: number | null = null) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.runId = runId;
    Object.setPrototypeOf(this, ApiRequestError.prototype);
  }
}

function buildQuery(filters: CaseFilters = {}): string {
  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === "") continue;
    params.set(key, String(value));
  }

  const query = params.toString();
  return query ? `?${query}` : "";
}

function buildAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};

  if (API_USER_ID) {
    headers["X-User-ID"] = API_USER_ID;
  }
  if (API_USER_NAME) {
    headers["X-User-Name"] = API_USER_NAME;
  }
  if (API_USER_ROLE) {
    headers["X-User-Role"] = API_USER_ROLE;
  }
  if (API_USER_SITES) {
    headers["X-User-Sites"] = API_USER_SITES;
  }
  if (API_TRUSTED_IDENTITY_B64 || API_TRUSTED_IDENTITY) {
    headers[API_TRUSTED_IDENTITY_HEADER_NAME] = API_TRUSTED_IDENTITY_B64 || API_TRUSTED_IDENTITY || "";
  }

  return headers;
}

function buildRequestInit(init: RequestInit = {}): RequestInit {
  const headers = new Headers(init.headers);

  for (const [name, value] of Object.entries(buildAuthHeaders())) {
    if (!headers.has(name)) {
      headers.set(name, value);
    }
  }

  return {
    ...init,
    headers,
    cache: init.cache ?? "no-store",
  };
}

async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`${API_BASE}${path}`, buildRequestInit(init));
}

async function buildApiRequestError(res: Response, fallbackMessage: string): Promise<ApiRequestError> {
  const contentType = res.headers.get("content-type") || "";
  let detail = fallbackMessage;

  try {
    if (contentType.includes("application/json")) {
      const body: unknown = await res.json();
      if (body && typeof body === "object" && "detail" in body) {
        const apiDetail = (body as { detail?: unknown }).detail;
        if (typeof apiDetail === "string" && apiDetail.trim()) {
          detail = apiDetail.trim();
        } else if (Array.isArray(apiDetail)) {
          const messages = apiDetail
            .map((item) => {
              if (item && typeof item === "object" && "msg" in item) {
                const message = (item as { msg?: unknown }).msg;
                return typeof message === "string" ? message : "";
              }
              return "";
            })
            .filter(Boolean);
          if (messages.length > 0) {
            detail = messages.join("; ");
          }
        }
      }
    } else {
      const text = (await res.text()).trim();
      if (text) {
        detail = text;
      }
    }
  } catch {
    detail = fallbackMessage;
  }

  const runIdHeader = res.headers.get("x-import-run-id");
  const parsedRunId = runIdHeader ? Number(runIdHeader) : Number.NaN;

  return new ApiRequestError(detail, res.status, Number.isInteger(parsedRunId) ? parsedRunId : null);
}

export async function getCases(filters: CaseFilters = {}): Promise<CaseListItem[]> {
  const res = await apiFetch(`/api/v1/cases${buildQuery(filters)}`);
  if (!res.ok) return [];
  return res.json();
}

export async function getCase(caseId: string): Promise<CaseDetail | null> {
  const res = await apiFetch(`/api/v1/cases/${caseId}`);
  if (!res.ok) return null;
  return res.json();
}

export async function getResearchCase(caseId: string): Promise<ResearchCaseDetail | null> {
  const res = await apiFetch(`/api/v1/cases/${caseId}/research`);
  if (!res.ok) return null;
  return res.json();
}

export async function submitReviewAction(caseId: string, payload: ReviewActionPayload): Promise<void> {
  const res = await apiFetch(`/api/v1/cases/${caseId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Failed to submit review action for case ${caseId}`);
  }
}

export async function getTrialMatches(caseId: string): Promise<TrialMatchResponse | null> {
  const res = await apiFetch(`/api/v1/trials/match/${caseId}`);
  if (!res.ok) return null;
  return res.json();
}

export async function getHybridAnalysis(caseId: string): Promise<HybridAnalysis | null> {
  const res = await apiFetch(`/api/v1/cases/${caseId}/hybrid`);
  if (!res.ok) return null;
  return res.json();
}

export async function getEvaluationComparison(): Promise<EvaluationComparison | null> {
  const res = await apiFetch("/api/v1/metrics/evaluation/compare");
  if (!res.ok) return null;
  return res.json();
}

export async function getEvaluationSweep(): Promise<ThresholdSweepSummary | null> {
  const res = await apiFetch("/api/v1/metrics/evaluation/sweep");
  if (!res.ok) return null;
  return res.json();
}

export async function getFeedbackSummary(): Promise<FeedbackSummary | null> {
  const res = await apiFetch("/api/v1/metrics/feedback");
  if (!res.ok) return null;
  return res.json();
}

export async function submitReviewFeedback(caseId: string, payload: ReviewFeedbackPayload): Promise<void> {
  const res = await apiFetch(`/api/v1/cases/${caseId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Failed to submit reviewer feedback for case ${caseId}`);
  }
}

export async function getFeedbackRecommendation(caseId: string): Promise<FeedbackRecommendation | null> {
  const res = await apiFetch(`/api/v1/cases/${caseId}/feedback/recommendation`);
  if (!res.ok) return null;
  return res.json();
}

export async function getCurrentUser(): Promise<CurrentUser | null> {
  const res = await apiFetch("/api/v1/auth/me");
  if (!res.ok) return null;
  return res.json();
}

export async function submitReportImport(file: File): Promise<ReportImportSummary> {
  const formData = new FormData();
  formData.set("file", file, file.name);

  const res = await apiFetch("/api/v1/imports/reports", {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw await buildApiRequestError(res, `Failed to import ${file.name || "report file"}.`);
  }

  return res.json();
}

export async function submitFhirDiagnosticReportImport(
  payload: Record<string, unknown> | Array<Record<string, unknown>>,
): Promise<ReportImportSummary> {
  const res = await apiFetch("/api/v1/imports/fhir/diagnostic-reports", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw await buildApiRequestError(res, "Failed to import FHIR DiagnosticReport payload.");
  }

  return res.json();
}

export async function submitHl7OruImport(payload: string): Promise<ReportImportSummary> {
  const res = await apiFetch("/api/v1/imports/hl7/oru", {
    method: "POST",
    headers: { "Content-Type": "text/plain; charset=utf-8" },
    body: payload,
  });

  if (!res.ok) {
    throw await buildApiRequestError(res, "Failed to import HL7 ORU payload.");
  }

  return res.json();
}

export async function getImportRuns({
  limit = 12,
  offset = 0,
}: {
  limit?: number;
  offset?: number;
} = {}): Promise<ImportRunSummary[]> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  const res = await apiFetch(`/api/v1/imports/runs?${params.toString()}`);
  if (!res.ok) return [];
  return res.json();
}

export async function getImportRun(runId: number): Promise<ImportRunDetail | null> {
  const res = await apiFetch(`/api/v1/imports/runs/${runId}`);
  if (!res.ok) return null;
  return res.json();
}

export async function getResearchSources(): Promise<ResearchSource[]> {
  const res = await apiFetch("/api/v1/research-intel/sources");
  if (!res.ok) return [];
  return res.json();
}

export async function getResearchRuns(limit = 12): Promise<ResearchRunSummary[]> {
  const res = await apiFetch(`/api/v1/research-intel/runs?limit=${limit}`);
  if (!res.ok) return [];
  return res.json();
}

export async function getResearchDocuments(filters: ResearchDocumentFilters = {}): Promise<ResearchDocument[]> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === "") continue;
    params.set(key, String(value));
  }
  const query = params.toString();
  const res = await apiFetch(`/api/v1/research-intel/documents${query ? `?${query}` : ""}`);
  if (!res.ok) return [];
  return res.json();
}

export async function getResearchTopics(): Promise<ResearchTopic[]> {
  const res = await apiFetch("/api/v1/research-intel/topics");
  if (!res.ok) return [];
  return res.json();
}

export async function getResearchGraph(): Promise<ResearchGraphSnapshot | null> {
  const res = await apiFetch("/api/v1/research-intel/graph");
  if (!res.ok) return null;
  return res.json();
}

export async function getResearchDigests(): Promise<ResearchDigestListItem[]> {
  const res = await apiFetch("/api/v1/research-intel/digests");
  if (!res.ok) return [];
  return res.json();
}

export async function getResearchDigest(digestId: string): Promise<ResearchDigestDetail | null> {
  const res = await apiFetch(`/api/v1/research-intel/digests/${digestId}`);
  if (!res.ok) return null;
  return res.json();
}

export async function getResearchOpportunities(params?: {
  opportunity_type?: string;
  status?: string;
  topic?: string;
}): Promise<ResearchOpportunity[]> {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params || {})) {
    if (value === undefined || value === null || value === "") continue;
    query.set(key, String(value));
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const res = await apiFetch(`/api/v1/research-intel/opportunities${suffix}`);
  if (!res.ok) return [];
  return res.json();
}

export async function runResearchIngest(payload?: {
  source_ids?: string[];
  include_disabled?: boolean;
  write_artifacts?: boolean;
  mode?: "auto" | "seeded" | "fixture" | "live";
  max_documents_per_source?: number;
}): Promise<ResearchRunDetail> {
  const res = await apiFetch("/api/v1/research-intel/runs/ingest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  if (!res.ok) {
    throw await buildApiRequestError(res, "Failed to trigger research ingest.");
  }
  const body: { run: ResearchRunDetail } = await res.json();
  return body.run;
}

export async function runResearchDigest(payload?: {
  publish?: boolean;
  write_artifacts?: boolean;
}): Promise<ResearchRunDetail> {
  const res = await apiFetch("/api/v1/research-intel/runs/digest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  if (!res.ok) {
    throw await buildApiRequestError(res, "Failed to trigger research digest.");
  }
  const body: { run: ResearchRunDetail } = await res.json();
  return body.run;
}

export async function promoteResearchOpportunity(
  opportunityId: string,
  target: "github_issue" | "docs_draft" | "benchmark_task",
): Promise<{
  ok: boolean;
  opportunity_id: string;
  status: string;
  promotion_target: string;
  artifact_path?: string | null;
}> {
  const res = await apiFetch(`/api/v1/research-intel/opportunities/${opportunityId}/promote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target }),
  });
  if (!res.ok) {
    throw await buildApiRequestError(res, "Failed to promote research opportunity.");
  }
  return res.json();
}

export async function getResearchBrief(caseId: string): Promise<ResearchCaseBrief | null> {
  const res = await apiFetch(`/api/v1/research-intel/cases/${caseId}/brief`);
  if (!res.ok) return null;
  return res.json();
}
