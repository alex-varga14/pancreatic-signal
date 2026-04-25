import { test, expect } from "@playwright/test";

test.describe("/imports", () => {
  test("renders the import workspace headline", async ({ page }) => {
    await page.goto("/imports");

    await expect(page.getByRole("heading", { name: /import workspace/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: /CSV, JSON, or JSONL/i })).toBeVisible();
  });

  test("shows the error banner when the API rejects an empty upload", async ({ page }) => {
    await page.goto("/imports?error=Mock+API+rejected+the+upload+because+the+payload+was+empty.");

    await expect(
      page.getByText("Mock API rejected the upload because the payload was empty.", {
        exact: false,
      }),
    ).toBeVisible();
  });
});
