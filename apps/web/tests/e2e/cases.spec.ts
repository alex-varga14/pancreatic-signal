import { test, expect } from "@playwright/test";

test.describe("/cases", () => {
  test("renders the worklist with mocked cases", async ({ page }) => {
    await page.goto("/cases");

    await expect(page.getByRole("heading", { name: /flagged cases/i })).toBeVisible();
    await expect(page.getByRole("link", { name: "C-E2E-1" })).toBeVisible();
    await expect(page.getByRole("link", { name: "C-E2E-2" })).toBeVisible();
  });

  test("submitting the urgency filter updates the URL", async ({ page }) => {
    await page.goto("/cases");

    await page.locator('select[name="urgency"]').selectOption("high");
    await page.getByRole("button", { name: /apply filters/i }).click();

    await page.waitForURL(/urgency=high/);
    await expect(page.getByRole("link", { name: "C-E2E-1" })).toBeVisible();
    await expect(page.getByRole("link", { name: "C-E2E-2" })).toHaveCount(0);
  });
});

test.describe("/cases/[caseId]", () => {
  test("shows case detail and accepts a reviewer action", async ({ page }) => {
    await page.goto("/cases/C-E2E-1");

    await expect(page.getByText("C-E2E-1", { exact: false })).toBeVisible();
    await expect(page.getByText(/abrupt cutoff of the pancreatic duct/i)).toBeVisible();

    const reviewForm = page
      .locator("form")
      .filter({ has: page.locator('select[name="action"]') })
      .first();
    await reviewForm.locator('select[name="action"]').selectOption("in_review");
    await reviewForm.getByRole("button", { name: /save action/i }).click();
    await page.waitForURL(/\/cases\/C-E2E-1/);
  });
});
