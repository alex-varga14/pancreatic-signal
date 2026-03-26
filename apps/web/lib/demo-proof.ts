import { readFile } from "fs/promises";
import path from "path";
import type { EvaluationComparison, ThresholdSweepSummary } from "./api";

export type DemoBenchmarkBucketSummary = {
  bucket: string;
  case_count: number;
  positive_count: number;
  escalation_count: number;
};

export type DemoBenchmarkDatasetSummary = {
  report_count: number;
  positive_count: number;
  escalation_count: number;
  bucket_counts: DemoBenchmarkBucketSummary[];
};

export type DemoBenchmarkQueueEntry = {
  case_id: string;
  report_id: string;
  benchmark_bucket?: string | null;
  score: number;
  outcome: string;
};

export type DemoBenchmarkQueuePreview = {
  top_k: number;
  rules: DemoBenchmarkQueueEntry[];
  hybrid: DemoBenchmarkQueueEntry[];
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
  dataset_summary: DemoBenchmarkDatasetSummary;
  queue_preview: DemoBenchmarkQueuePreview;
  comparison: EvaluationComparison;
  sweep: ThresholdSweepSummary;
  casebook: DemoBenchmarkCasebookEntry[];
};

export const PUBLISHED_DEMO_PROOF_PATH = "docs/examples/demo-benchmark-current.json";

function candidateRoots(): string[] {
  const cwd = process.cwd();
  return [cwd, path.resolve(cwd, ".."), path.resolve(cwd, "..", "..")].filter(
    (value, index, array) => array.indexOf(value) === index,
  );
}

export async function getDemoBenchmarkSnapshot(): Promise<DemoBenchmarkSnapshot | null> {
  for (const root of candidateRoots()) {
    const snapshotPath = path.join(root, PUBLISHED_DEMO_PROOF_PATH);

    try {
      const raw = await readFile(snapshotPath, "utf8");
      return JSON.parse(raw) as DemoBenchmarkSnapshot;
    } catch (error) {
      const code = (error as NodeJS.ErrnoException).code;
      if (code === "ENOENT") {
        continue;
      }
    }
  }

  return null;
}
