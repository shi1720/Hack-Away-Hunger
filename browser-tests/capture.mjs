import { chromium } from "@playwright/test";
import fs from "node:fs/promises";
const base = process.env.BASE_URL || "http://127.0.0.1:8010";
const dir = "../artifacts/screenshots";
await fs.mkdir(dir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({
  viewport: { width: 1440, height: 1000 },
  deviceScaleFactor: 1,
});
await page.goto(base);
await page.getByRole("button", { name: "Explore the live demo" }).waitFor();
await page.screenshot({ path: `${dir}/landing.png`, fullPage: true });
await page.getByRole("button", { name: "Explore the live demo" }).click();
await page.getByRole("heading", { name: "Every connection counts." }).waitFor();
await page.screenshot({ path: `${dir}/overview.png`, fullPage: true });
await page.getByRole("button", { name: "Relay planner", exact: true }).click();
console.log(await page.locator("main").innerText());
await page.screenshot({ path: `${dir}/planner-initial.png`, fullPage: true });
await browser.close();
