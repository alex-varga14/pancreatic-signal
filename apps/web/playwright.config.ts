import { defineConfig, devices } from "@playwright/test";

const PORT = Number(process.env.WEB_E2E_PORT || 3100);
const MOCK_API_PORT = Number(process.env.WEB_E2E_MOCK_API_PORT || 3199);
const MOCK_API_BASE = `http://127.0.0.1:${MOCK_API_PORT}`;
const BASE_URL = `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? [["github"], ["list"]] : [["list"]],
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: `node tests/e2e/mock-api-server.cjs`,
      url: `${MOCK_API_BASE}/health`,
      env: {
        MOCK_API_PORT: String(MOCK_API_PORT),
      },
      reuseExistingServer: !process.env.CI,
      stdout: "pipe",
      stderr: "pipe",
      timeout: 30_000,
    },
    {
      command: `npx --no-install next dev --hostname 127.0.0.1 --port ${PORT}`,
      url: BASE_URL,
      env: {
        API_BASE_URL: MOCK_API_BASE,
        NEXT_PUBLIC_API_BASE_URL: MOCK_API_BASE,
        NEXT_TELEMETRY_DISABLED: "1",
      },
      reuseExistingServer: !process.env.CI,
      stdout: "pipe",
      stderr: "pipe",
      timeout: 120_000,
    },
  ],
});
