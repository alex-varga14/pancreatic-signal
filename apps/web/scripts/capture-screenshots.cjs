/* One-off helper to refresh README/docs screenshots against a locally
 * seeded stack. Usage:
 *   node scripts/capture-screenshots.cjs <base-url> <out-dir>
 */
const path = require("node:path");
const { chromium } = require("@playwright/test");

const baseUrl = process.argv[2] || "http://127.0.0.1:3102";
const outDir = process.argv[3] || path.join(__dirname, "..", "..", "..", "docs", "media");

const pages = [
  { route: "/cases", file: "worklist.png" },
  { route: "/cases/C-001", file: "case-detail.png" },
  { route: "/proof", file: "proof.png" },
  { route: "/research-intel", file: "research-intel.png" },
];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });
  for (const { route, file } of pages) {
    await page.goto(baseUrl + route, { waitUntil: "networkidle" });
    await page.screenshot({ path: path.join(outDir, file) });
    console.log("captured", route, "->", file);
  }
  await browser.close();
})();
