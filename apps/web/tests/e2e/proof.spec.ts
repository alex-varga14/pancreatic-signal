import { test, expect } from "@playwright/test";

test.describe("/proof", () => {
  test("renders the published demo benchmark snapshot", async ({ page }) => {
    await page.goto("/proof");

    await expect(
      page.getByRole("heading", { name: /a reproducible proof surface/i }),
    ).toBeVisible();

    await expect(page.getByText("Rules F1").first()).toBeVisible();
    await expect(page.getByText("Hybrid F1").first()).toBeVisible();
  });

  test("links back to the worklist", async ({ page }) => {
    await page.goto("/proof");

    const worklistLink = page.getByRole("link", { name: /open worklist/i });
    await expect(worklistLink).toBeVisible();
    await expect(worklistLink).toHaveAttribute("href", "/cases");
  });
});
