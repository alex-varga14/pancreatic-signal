import { readFile } from "fs/promises";
import path from "path";
import type {
  EvaluationComparison,
  EvaluationSummary,
  ExternalThresholdSweepSummary,
  ThresholdSweepSummary,
} from "./api";

export type PublishedBenchmarkBucketSummary = {
  bucket: string;
  case_count: number;
  positive_count: number;
  escalation_count: number;
};

export type PublishedBenchmarkDatasetSummary = {
  report_count: number;
  positive_count: number;
  escalation_count: number;
  bucket_counts: PublishedBenchmarkBucketSummary[];
};

export type PublishedBenchmarkQueueEntry = {
  case_id: string;
  report_id: string;
  benchmark_bucket?: string | null;
  score: number;
  outcome: string;
};

export type DemoBenchmarkQueuePreview = {
  top_k: number;
  rules: PublishedBenchmarkQueueEntry[];
  hybrid: PublishedBenchmarkQueueEntry[];
};

export type DemoBenchmarkCaseMode = {
  score: number;
  flagged: boolean;
  outcome: string;
  rationale_codes: string[];
};

export type DemoBenchmarkCasebookEntry = {
  case_id: string;
  report_id: string;
  benchmark_bucket?: string | null;
  reviewer_focus?: string | null;
  label_notes?: string | null;
  expected_positive: boolean;
  expected_escalation: boolean;
  expected_rationale_codes: string[];
  hybrid_lift: number;
  rules: DemoBenchmarkCaseMode;
  hybrid: DemoBenchmarkCaseMode;
};

export type DemoBenchmarkSnapshot = {
  generated_at: string;
  dataset: {
    reports_path: string;
    labels_path: string;
  };
  dataset_summary: PublishedBenchmarkDatasetSummary;
  queue_preview: DemoBenchmarkQueuePreview;
  comparison: EvaluationComparison;
  sweep: ThresholdSweepSummary;
  casebook: DemoBenchmarkCasebookEntry[];
};

export const PUBLISHED_DEMO_PROOF_PATH = "docs/examples/demo-benchmark-current.json";
export const PUBLISHED_RETROSPECTIVE_SAMPLE_PROOF_PATH =
  "docs/examples/retrospective-benchmark-sample-current.json";

export type ExternalBenchmarkQueuePreview = {
  top_k: number;
  external: PublishedBenchmarkQueueEntry[];
};

export type ExternalBenchmarkCaseMode = {
  score: number;
  flagged: boolean;
  outcome: string;
  rationale_codes: string[];
  false_negative_bucket?: string | null;
};

export type ExternalBenchmarkCasebookEntry = {
  case_id: string;
  report_id: string;
  report_excerpt?: string | null;
  benchmark_bucket?: string | null;
  reviewer_focus?: string | null;
  label_notes?: string | null;
  expected_positive: boolean;
  expected_escalation: boolean;
  expected_rationale_codes: string[];
  external: ExternalBenchmarkCaseMode;
};

export type ExternalBenchmarkSubmission = {
  evaluation_command: string;
  notable_strengths: string[];
  known_limitations: string[];
};

export type RetrospectiveBenchmarkSnapshot = {
  generated_at: string;
  dataset: {
    dataset_name: string;
    dataset_split: string;
    deidentified: boolean;
    label_schema_version: string;
    labels_path: string;
    predictions_path: string;
  };
  dataset_summary: PublishedBenchmarkDatasetSummary;
  queue_preview: ExternalBenchmarkQueuePreview;
  evaluation: EvaluationSummary;
  sweep: ExternalThresholdSweepSummary;
  casebook: ExternalBenchmarkCasebookEntry[];
  submission?: ExternalBenchmarkSubmission | null;
};

function candidateRoots(): string[] {
  const cwd = process.cwd();
  return [cwd, path.resolve(cwd, ".."), path.resolve(cwd, "..", "..")].filter(
    (value, index, array) => array.indexOf(value) === index,
  );
}

async function readPublishedSnapshot<T>(publishedPath: string): Promise<T | null> {
  for (const root of candidateRoots()) {
    const snapshotPath = path.join(root, publishedPath);

    try {
      const raw = await readFile(snapshotPath, "utf8");
      return JSON.parse(raw) as T;
    } catch (error) {
      const code = (error as NodeJS.ErrnoException).code;
      if (code === "ENOENT") {
        continue;
      }
    }
  }

  return null;
}

export async function getDemoBenchmarkSnapshot(): Promise<DemoBenchmarkSnapshot | null> {
  return readPublishedSnapshot<DemoBenchmarkSnapshot>(PUBLISHED_DEMO_PROOF_PATH);
}

export async function getRetrospectiveBenchmarkSnapshot(): Promise<RetrospectiveBenchmarkSnapshot | null> {
  return readPublishedSnapshot<RetrospectiveBenchmarkSnapshot>(PUBLISHED_RETROSPECTIVE_SAMPLE_PROOF_PATH);
}
