"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { promoteAutoresearchRun } from "../../lib/api";

function readField(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value.trim() : "";
}

export async function promoteAutoresearchRunAction(formData: FormData): Promise<void> {
  const runId = readField(formData, "run_id");
  if (!runId) {
    redirect("/autoresearch?error=Run+id+is+required");
  }

  const result = await promoteAutoresearchRun(runId);
  if (!result.ok) {
    redirect(
      `/autoresearch/${encodeURIComponent(runId)}?error=${encodeURIComponent(result.detail ?? "Promotion failed")}`,
    );
  }

  revalidatePath("/autoresearch");
  revalidatePath(`/autoresearch/${runId}`);
  redirect(`/autoresearch/${encodeURIComponent(runId)}?info=Promoted`);
}
