"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import {
  ApiRequestError,
  type ReportImportSummary,
  submitFhirDiagnosticReportImport as postFhirDiagnosticReportImport,
  submitHl7OruImport as postHl7OruImport,
  submitReportImport as postReportImport,
} from "../../lib/api";

function readTextField(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value.trim() : "";
}

function buildImportsPath(params: Record<string, string | number | undefined>): string {
  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    searchParams.set(key, String(value));
  }

  const query = searchParams.toString();
  return query ? `/imports?${query}` : "/imports";
}

function refreshImportSurfaces(): void {
  revalidatePath("/imports");
  revalidatePath("/cases");
}

function redirectToImports(params: Record<string, string | number | undefined>): never {
  redirect(buildImportsPath(params));
}

function handleImportError(error: unknown): never {
  if (error instanceof ApiRequestError) {
    refreshImportSurfaces();
    if (error.runId) {
      redirectToImports({ run_id: error.runId });
    }
    redirectToImports({ error: error.message });
  }

  throw error;
}

function parseFhirPayload(payloadText: string): Record<string, unknown> | Array<Record<string, unknown>> {
  let payload: unknown;

  try {
    payload = JSON.parse(payloadText);
  } catch {
    redirectToImports({ error: "FHIR payload must be valid JSON." });
  }

  if (Array.isArray(payload)) {
    if (payload.some((item) => !item || typeof item !== "object" || Array.isArray(item))) {
      redirectToImports({ error: "FHIR payload arrays must contain JSON objects." });
    }
    return payload as Array<Record<string, unknown>>;
  }

  if (!payload || typeof payload !== "object") {
    redirectToImports({ error: "FHIR payload must be a JSON object or array of objects." });
  }

  return payload as Record<string, unknown>;
}

export async function submitReportFileImport(formData: FormData): Promise<void> {
  const file = formData.get("report_file");

  if (!(file instanceof File) || file.size === 0) {
    redirectToImports({ error: "Choose a CSV, JSON, or JSONL file to import." });
  }

  let summary: ReportImportSummary;
  try {
    summary = await postReportImport(file);
  } catch (error) {
    handleImportError(error);
  }

  refreshImportSurfaces();
  redirectToImports(summary.run_id ? { run_id: summary.run_id } : { info: "Import completed." });
}

export async function submitFhirDiagnosticReportImport(formData: FormData): Promise<void> {
  const payloadText = readTextField(formData, "fhir_payload");

  if (!payloadText) {
    redirectToImports({ error: "Paste a FHIR DiagnosticReport JSON payload to import." });
  }

  const payload = parseFhirPayload(payloadText);

  let summary: ReportImportSummary;
  try {
    summary = await postFhirDiagnosticReportImport(payload);
  } catch (error) {
    handleImportError(error);
  }

  refreshImportSurfaces();
  redirectToImports(summary.run_id ? { run_id: summary.run_id } : { info: "FHIR import completed." });
}

export async function submitHl7OruImport(formData: FormData): Promise<void> {
  const payloadText = readTextField(formData, "hl7_payload");

  if (!payloadText) {
    redirectToImports({ error: "Paste an HL7 ORU payload to import." });
  }

  let summary: ReportImportSummary;
  try {
    summary = await postHl7OruImport(payloadText);
  } catch (error) {
    handleImportError(error);
  }

  refreshImportSurfaces();
  redirectToImports(summary.run_id ? { run_id: summary.run_id } : { info: "HL7 import completed." });
}
