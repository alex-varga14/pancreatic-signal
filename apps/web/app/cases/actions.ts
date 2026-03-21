"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { submitReviewAction as postReviewAction, submitReviewFeedback as postReviewFeedback } from "../../lib/api";

function readField(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value.trim() : "";
}

export async function submitReviewAction(formData: FormData): Promise<void> {
  const caseId = readField(formData, "case_id");
  const action = readField(formData, "action");
  const note = readField(formData, "note");
  const assignedTo = readField(formData, "assigned_to");

  if (!caseId || !action) {
    throw new Error("Case and action are required.");
  }

  await postReviewAction(caseId, {
    action,
    note: note || undefined,
    assigned_to: assignedTo || undefined,
  });

  revalidatePath("/cases");
  revalidatePath(`/cases/${caseId}`);
  redirect(`/cases/${caseId}`);
}

export async function submitCaseFeedback(formData: FormData): Promise<void> {
  const caseId = readField(formData, "case_id");
  const label = readField(formData, "feedback_label");
  const disposition = readField(formData, "feedback_disposition");
  const errorBucket = readField(formData, "feedback_error_bucket");
  const notes = readField(formData, "feedback_notes");

  if (!caseId || !label || !disposition) {
    throw new Error("Case, label, and disposition are required.");
  }

  await postReviewFeedback(caseId, {
    label,
    disposition,
    error_bucket: errorBucket || undefined,
    notes: notes || undefined,
  });

  revalidatePath("/cases");
  revalidatePath(`/cases/${caseId}`);
  redirect(`/cases/${caseId}`);
}
