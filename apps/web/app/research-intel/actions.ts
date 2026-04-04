"use server";

import { revalidatePath } from "next/cache";

import {
  promoteResearchOpportunity,
  runResearchDigest,
  runResearchIngest,
  runResearchOpportunityExperiment,
  runResearchWatchtower,
} from "../../lib/api";


export async function triggerResearchWatchtowerAction(): Promise<void> {
  await runResearchWatchtower({ write_artifacts: true, only_due: true, digest_policy: "new_documents" });
  revalidatePath("/research-intel");
  revalidatePath("/research-intel/documents");
  revalidatePath("/research-intel/digests");
  revalidatePath("/research-intel/opportunities");
  revalidatePath("/research-intel/schedule");
}


export async function triggerResearchIngestAction(): Promise<void> {
  await runResearchIngest({ write_artifacts: true });
  revalidatePath("/research-intel");
  revalidatePath("/research-intel/documents");
  revalidatePath("/research-intel/digests");
  revalidatePath("/research-intel/opportunities");
  revalidatePath("/research-intel/schedule");
}


export async function triggerDueResearchIngestAction(): Promise<void> {
  await runResearchIngest({ write_artifacts: true, only_due: true });
  revalidatePath("/research-intel");
  revalidatePath("/research-intel/documents");
  revalidatePath("/research-intel/digests");
  revalidatePath("/research-intel/opportunities");
  revalidatePath("/research-intel/schedule");
}


export async function triggerResearchDigestAction(): Promise<void> {
  await runResearchDigest({ publish: true, write_artifacts: true });
  revalidatePath("/research-intel");
  revalidatePath("/research-intel/digests");
  revalidatePath("/research-intel/opportunities");
  revalidatePath("/research-intel/schedule");
}


export async function promoteResearchOpportunityAction(formData: FormData): Promise<void> {
  const opportunityId = String(formData.get("opportunity_id") || "").trim();
  const target = String(formData.get("target") || "docs_draft").trim();

  if (!opportunityId) {
    throw new Error("Opportunity id is required.");
  }
  if (!["github_issue", "docs_draft", "benchmark_task"].includes(target)) {
    throw new Error("Unsupported promotion target.");
  }

  await promoteResearchOpportunity(
    opportunityId,
    target as "github_issue" | "docs_draft" | "benchmark_task",
  );
  revalidatePath("/research-intel");
  revalidatePath("/research-intel/opportunities");
  revalidatePath("/research-intel/schedule");
}


export async function runResearchOpportunityExperimentAction(formData: FormData): Promise<void> {
  const opportunityId = String(formData.get("opportunity_id") || "").trim();
  const experimentKind = String(formData.get("experiment_kind") || "").trim();
  if (!opportunityId) {
    throw new Error("Opportunity id is required.");
  }

  await runResearchOpportunityExperiment(opportunityId, {
    write_artifacts: true,
    experiment_kind: experimentKind
      ? (experimentKind as
          | "benchmark_readiness"
          | "benchmark_stress_test"
          | "rule_explainability"
          | "rule_stress_test")
      : undefined,
  });
  revalidatePath("/research-intel");
  revalidatePath("/research-intel/opportunities");
  revalidatePath("/research-intel/schedule");
}
