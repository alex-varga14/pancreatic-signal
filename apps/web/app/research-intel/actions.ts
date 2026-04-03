"use server";

import { revalidatePath } from "next/cache";

import { promoteResearchOpportunity, runResearchDigest, runResearchIngest } from "../../lib/api";


export async function triggerResearchIngestAction(): Promise<void> {
  await runResearchIngest({ write_artifacts: true });
  revalidatePath("/research-intel");
  revalidatePath("/research-intel/documents");
  revalidatePath("/research-intel/digests");
  revalidatePath("/research-intel/opportunities");
}


export async function triggerResearchDigestAction(): Promise<void> {
  await runResearchDigest({ publish: true, write_artifacts: true });
  revalidatePath("/research-intel");
  revalidatePath("/research-intel/digests");
  revalidatePath("/research-intel/opportunities");
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
}
