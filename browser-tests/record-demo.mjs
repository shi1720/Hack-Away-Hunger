// Record actual hosted interactions. Narration timing is applied in the edit, not faked in the UI.
import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const base = process.env.BASE_URL || "http://127.0.0.1:8010";
const scenes = JSON.parse(
  await fs.readFile(path.join(root, "tmp/video/scenes.json"), "utf8"),
);
const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1600, height: 800 },
  deviceScaleFactor: 1,
  timezoneId: "America/Chicago",
  recordVideo: {
    dir: path.join(root, "tmp/video/raw"),
    size: { width: 1600, height: 800 },
  },
});
const page = await context.newPage();
const started = Date.now();
const timeline = [];
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto(base);
await page
  .getByRole("button", { name: "Explore the live demo", exact: true })
  .waitFor();
async function nav(name) {
  await page
    .getByRole("navigation")
    .getByRole("button", { name, exact: true })
    .click();
}
async function hold(ms) {
  if (ms > 0) await page.waitForTimeout(ms);
}
async function scene(id, action) {
  const config = scenes.find((x) => x.id === id);
  const start = Date.now();
  console.log("Recording scene", id);
  await action();
  await hold(Math.max(1000, config.duration * 1000 - (Date.now() - start)));
  timeline.push({
    id,
    start: (start - started) / 1000,
    end: (Date.now() - started) / 1000,
    targetDuration: config.duration,
  });
  await page.screenshot({ path: path.join(root, `tmp/video/scene-${id}.png`) });
}
await scene("01", async () => {
  await hold(11000);
  await page
    .getByRole("button", { name: "Explore the live demo", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Every connection counts." })
    .waitFor();
});
await scene("02", async () => {
  await hold(5000);
  await page.mouse.move(1100, 660);
});
await scene("03", async () => {
  await nav("Relay planner");
  await page.getByRole("button", { name: "Find matches", exact: true }).click();
  await page
    .locator(".proposal-card")
    .filter({ hasText: "Harvest apples & carrots" })
    .first()
    .waitFor();
});
await scene("04", async () => {
  await hold(11000);
  await page
    .locator(".proposal-card")
    .filter({ hasText: "Harvest apples & carrots" })
    .first()
    .getByRole("button", { name: "Reserve this relay" })
    .click();
  await nav("Deliveries");
  await page.locator(".delivery-card").first().waitFor();
});
await scene("05", async () => {
  const card = page.locator(".delivery-card").first();
  await card.getByRole("button", { name: "Accept at destination" }).click();
  await page.getByLabel("Receiver’s name").fill("Jordan (demo receiver)");
  await hold(900);
  await page
    .getByRole("button", { name: "Accept transfer", exact: true })
    .click();
  await card.getByRole("button", { name: "Record pickup" }).click();
  if (await page.getByLabel("Measured food temperature").count())
    await page.getByLabel("Measured food temperature").fill("38");
  await page.getByRole("checkbox", { name: /Condition checked/ }).check();
  await hold(900);
  await page
    .getByRole("button", { name: "Confirm pickup", exact: true })
    .click();
  await card.getByRole("button", { name: "Mark arrived", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Mark arrived", exact: true })
    .click();
});
await scene("06", async () => {
  await page
    .locator(".delivery-card")
    .first()
    .getByRole("button", { name: "Confirm receipt", exact: true })
    .click();
  await hold(2000);
  await page.getByLabel("Actual food received (lb)").fill("112");
  if (await page.getByLabel("Measured food temperature").count())
    await page.getByLabel("Measured food temperature").fill("38");
  await page
    .getByLabel("Exception note")
    .fill("8 lb damaged in transit, sample scenario.");
  await hold(4500);
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirm receipt", exact: true })
    .click();
  await page.getByRole("dialog").waitFor({ state: "hidden" });
  await nav("Impact & reports");
  await page.locator(".impact-hero").filter({ hasText: "112" }).waitFor();
  await hold(4000);
  await nav("Pantries & needs");
  await hold(500);
  await page.locator(".service-table").scrollIntoViewIfNeeded();
  await hold(3000);
});
await scene("07", async () => {
  await nav("Inventory");
  await page
    .getByRole("row")
    .filter({ hasText: "Harvest apples & carrots" })
    .filter({ hasText: "112 lb" })
    .last()
    .scrollIntoViewIfNeeded();
  await hold(7000);
  await nav("Impact & reports");
});
await scene("08", async () => {
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await page
    .getByRole("button", { name: "Start a network", exact: true })
    .click();
  await page.getByLabel("Your full name").waitFor();
});
await scene("09", async () => {
  await page.goto("file://" + path.join(root, "tmp/video/card-09.html"));
});
await scene("10", async () => {
  await page.goto("file://" + path.join(root, "tmp/video/card-10.html"));
});
const video = page.video();
await context.close();
await video.saveAs(path.join(root, "tmp/video/raw-demo.webm"));
await browser.close();
await fs.writeFile(
  path.join(root, "tmp/video/recording.json"),
  JSON.stringify({ base, timeline, errors }, null, 2),
);
if (errors.length) throw new Error("Browser errors: " + errors.join("; "));
console.log("Recorded hosted workflow with no browser errors");
