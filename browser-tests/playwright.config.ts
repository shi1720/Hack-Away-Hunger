import { defineConfig, devices } from "@playwright/test";

const selectedBrowser = process.env.PANTRY_BROWSER || "chromium";
if (!["chromium", "firefox", "webkit"].includes(selectedBrowser)) {
  throw new Error("PANTRY_BROWSER must be chromium, firefox or webkit");
}
const browserName = selectedBrowser as "chromium" | "firefox" | "webkit";
const device =
  browserName === "webkit"
    ? "Desktop Safari"
    : browserName === "firefox"
      ? "Desktop Firefox"
      : "Desktop Chrome";

export default defineConfig({
  testDir: ".",
  testMatch: "*.spec.ts",
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  retries: 0,
  reporter: process.env.PLAYWRIGHT_JSON_OUTPUT_NAME
    ? [["list"], ["html", { open: "never" }], ["json"]]
    : [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.BASE_URL || "http://127.0.0.1:8010",
    viewport: { width: 1440, height: 1000 },
    actionTimeout: 10000,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: browserName,
      use: {
        ...devices[device],
        browserName,
        viewport: { width: 1440, height: 1000 },
      },
    },
  ],
});
