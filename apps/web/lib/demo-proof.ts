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
  description?: string | null;
};

export type PublishedBenchmarkCohortSummary = {
  cohort: string;
  case_count: number;
  positive_count: number;
  flagged_count: number;
  missed_positive_count: number;
  description?: string | null;
};

export type PublishedBenchmarkDatasetSummary = {
  report_count: number;
  positive_count: number;
  escalation_count: number;
  bucket_counts: PublishedBenchmarkBucketSummary[];
  cohort_counts?: PublishedBenchmarkCohortSummary[];
};

export type PublishedBenchmarkQueueEntry = {
  case_id: string;
  report_id: string;
  cohort?: string | null;
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
export const PUBLISHED_EXTERNAL_BENCHMARK_REGISTRY_PATH =
  "docs/examples/published-external-benchmarks.json";

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
  cohort?: string | null;
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
  notes?: string | null;
};

export type ExternalBenchmarkDatasetContext = {
  dataset_description?: string | null;
  labeling_policy?: string | null;
  notes?: string | null;
};

export type ExternalBenchmarkSnapshot = {
  generated_at: string;
  dataset: {
    dataset_name: string;
    dataset_split: string;
    deidentified: boolean;
    label_schema_version: string;
    labels_path: string;
    predictions_path: string;
    manifest_path?: string | null;
  };
  dataset_context?: ExternalBenchmarkDatasetContext | null;
  dataset_summary: PublishedBenchmarkDatasetSummary;
  queue_preview: ExternalBenchmarkQueuePreview;
  evaluation: EvaluationSummary;
  sweep: ExternalThresholdSweepSummary;
  casebook: ExternalBenchmarkCasebookEntry[];
  submission?: ExternalBenchmarkSubmission | null;
};

export type RetrospectiveBenchmarkSnapshot = ExternalBenchmarkSnapshot;

export type PublishedExternalBenchmarkDescriptor = {
  id: string;
  label: string;
  title: string;
  description: string;
  snapshot_path: string;
  build_command?: string | null;
  refresh_command?: string | null;
  submission_path?: string | null;
};

export type PublishedExternalBenchmarkEntry = {
  descriptor: PublishedExternalBenchmarkDescriptor;
  snapshot: ExternalBenchmarkSnapshot | null;
};

const LEGACY_EXTERNAL_BENCHMARK_DESCRIPTOR: PublishedExternalBenchmarkDescriptor = {
  id: "retrospective-sample",
  label: "Retrospective Sample",
  title: "A broader multi-cohort external casebook now sits beside the demo proof.",
  description:
    "This sample is still intentionally bounded, but it now shows the same proof shape across multiple deidentified retrospective-style cohorts instead of only a single undifferentiated pack.",
  snapshot_path: "docs/examples/retrospective-benchmark-sample-current.json",
  build_command: "make benchmark-external-sample",
  refresh_command: "make refresh-external-sample-proof",
  submission_path: "docs/examples/retrospective-benchmark-sample-current-submission.json",
};

function expectRecord(value: unknown, fieldPath: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`Invalid published benchmark registry at ${fieldPath}: expected an object.`);
  }

  return value as Record<string, unknown>;
}

function expectTrimmedString(value: unknown, fieldPath: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`Invalid published benchmark registry at ${fieldPath}: expected a non-empty string.`);
  }

  return value.trim();
}

function expectOptionalTrimmedString(value: unknown, fieldPath: string): string | null {
  if (value === undefined || value === null) {
    return null;
  }

  return expectTrimmedString(value, fieldPath);
}

function expectRelativeJsonPath(value: unknown, fieldPath: string): string {
  const normalized = expectTrimmedString(value, fieldPath);

  if (path.isAbsolute(normalized) || !normalized.endsWith(".json")) {
    throw new Error(
      `Invalid published benchmark registry at ${fieldPath}: expected a relative path to a JSON file.`,
    );
  }

  return normalized;
}

function normalizePublishedExternalBenchmarkDescriptor(
  value: unknown,
  index: number,
): PublishedExternalBenchmarkDescriptor {
  const fieldPath = `registry[${index}]`;
  const descriptor = expectRecord(value, fieldPath);

  return {
    id: expectTrimmedString(descriptor.id, `${fieldPath}.id`),
    label: expectTrimmedString(descriptor.label, `${fieldPath}.label`),
    title: expectTrimmedString(descriptor.title, `${fieldPath}.title`),
    description: expectTrimmedString(descriptor.description, `${fieldPath}.description`),
    snapshot_path: expectRelativeJsonPath(descriptor.snapshot_path, `${fieldPath}.snapshot_path`),
    build_command: expectOptionalTrimmedString(descriptor.build_command, `${fieldPath}.build_command`),
    refresh_command: expectOptionalTrimmedString(descriptor.refresh_command, `${fieldPath}.refresh_command`),
    submission_path:
      descriptor.submission_path === undefined || descriptor.submission_path === null
        ? null
        : expectRelativeJsonPath(descriptor.submission_path, `${fieldPath}.submission_path`),
  };
}

function validatePublishedExternalBenchmarkRegistry(
  value: unknown,
): PublishedExternalBenchmarkDescriptor[] {
  if (!Array.isArray(value)) {
    throw new Error("Invalid published benchmark registry: expected an array of benchmark descriptors.");
  }

  const seenIds = new Set<string>();
  const normalizedDescriptors = value.map((descriptor, index) =>
    normalizePublishedExternalBenchmarkDescriptor(descriptor, index),
  );

  normalizedDescriptors.forEach((descriptor, index) => {
    if (seenIds.has(descriptor.id)) {
      throw new Error(
        `Invalid published benchmark registry at registry[${index}].id: duplicate id "${descriptor.id}".`,
      );
    }

    seenIds.add(descriptor.id);
  });

  return normalizedDescriptors;
}

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

export async function getPublishedExternalBenchmarkDescriptors(): Promise<
  PublishedExternalBenchmarkDescriptor[]
> {
  const registry = await readPublishedSnapshot<unknown>(
    PUBLISHED_EXTERNAL_BENCHMARK_REGISTRY_PATH,
  );

  if (!registry) {
    return [LEGACY_EXTERNAL_BENCHMARK_DESCRIPTOR];
  }

  const normalizedRegistry = validatePublishedExternalBenchmarkRegistry(registry);

  if (normalizedRegistry.length === 0) {
    return [LEGACY_EXTERNAL_BENCHMARK_DESCRIPTOR];
  }

  return normalizedRegistry;
}

export async function getPublishedExternalBenchmarkEntries(): Promise<PublishedExternalBenchmarkEntry[]> {
  const descriptors = await getPublishedExternalBenchmarkDescriptors();

  return Promise.all(
    descriptors.map(async (descriptor) => ({
      descriptor,
      snapshot: await readPublishedSnapshot<ExternalBenchmarkSnapshot>(descriptor.snapshot_path),
    })),
  );
}

export async function getRetrospectiveBenchmarkSnapshot(): Promise<RetrospectiveBenchmarkSnapshot | null> {
  const entries = await getPublishedExternalBenchmarkEntries();
  return entries[0]?.snapshot ?? null;
}
