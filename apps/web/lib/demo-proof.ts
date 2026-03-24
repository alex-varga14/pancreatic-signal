import { readFile } from "fs/promises";
import path from "path";
import type { EvaluationComparison, ThresholdSweepSummary } from "./api";

export type DemoBenchmarkSnapshot = {
  generated_at: string;
  dataset: {
    reports_path: string;
    labels_path: string;
  };
  comparison: EvaluationComparison;
  sweep: ThresholdSweepSummary;
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
