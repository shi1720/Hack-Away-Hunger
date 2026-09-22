import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs/promises";
import { createOperationalFixture, demo, nav, workspace } from "./helpers";
test("complete actual receipt workflow and reload persistence", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await demo(page);
  await nav(page, "Relay planner");
  await page.getByRole("button", { name: "Find matches", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Reserve this relay" }).first(),
  ).toBeVisible();
  const proposal = page
    .locator(".proposal-card")
    .filter({ hasText: "120" })
    .first();
  await proposal.getByRole("button", { name: "Reserve this relay" }).click();
  await expect(page.getByRole("status")).toContainText("120 lb reserved");
  await nav(page, "Deliveries");
  const card = page.locator(".delivery-card").first();
  await card.getByRole("button", { name: "Accept at destination" }).click();
  await page.getByLabel("Receiver’s name").fill("Jordan (demo receiver)");
  await page
    .getByRole("button", { name: "Accept transfer", exact: true })
    .click();
  await card.getByRole("button", { name: "Record pickup" }).click();
  if (await page.getByLabel("Measured food temperature").count())
    await page.getByLabel("Measured food temperature").fill("38");
  await page.getByRole("checkbox", { name: /Condition checked/ }).check();
  await page
    .getByRole("button", { name: "Confirm pickup", exact: true })
    .click();
  await card.getByRole("button", { name: "Mark arrived", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Mark arrived", exact: true })
    .click();
  await card
    .getByRole("button", { name: "Confirm receipt", exact: true })
    .click();
  await page.getByLabel("Actual food received (lb)").fill("112");
  if (await page.getByLabel("Measured food temperature").count())
    await page.getByLabel("Measured food temperature").fill("38");
  await page
    .getByLabel("Exception note")
    .fill("8 lb damaged in transit (sample scenario).");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirm receipt", exact: true })
    .click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await nav(page, "Impact & reports");
  await expect(page.locator(".impact-hero")).toContainText("112");
  await expect(page.locator("tbody")).toContainText("8 lb");
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export receipts" }).click();
  const receiptDownload = await download;
  expect(receiptDownload.suggestedFilename()).toContain("receipts");
  const exported = await fs.readFile((await receiptDownload.path())!, "utf8");
  expect(exported).toContain("dispatched_lb,received_lb,rejected_lb");
  expect(exported).toContain("120.0,112.0,8.0");
  expect(exported).toContain("8 lb damaged in transit (sample scenario).");
  await page.reload();
  await expect(page.locator(".impact-hero")).toContainText("112");
  await nav(page, "Pantries & needs");
  await expect(page.locator(".service-table")).toContainText("8 lb");
  expect(errors).toEqual([]);
});
test("real account onboarding, stock, need, and closing mistaken request", async ({
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Start a network", exact: true })
    .click();
  await page.getByLabel("Your full name").fill("Pilot Tester");
  await page
    .getByLabel("Network name", { exact: true })
    .fill("Isolated QA Network");
  const email = `qa-${Date.now()}@example.org`;
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel(/^Password/).fill("Test only passphrase 2026!");
  await page
    .getByRole("button", { name: "Create network", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: /Add your first pantry/ }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Add your first pantry/ }).click();
  await page.getByLabel("Pantry name").fill("QA West");
  await page.getByLabel("City", { exact: true }).fill("Des Moines");
  await page.getByLabel("Street address").fill("100 Example Street");
  await page.getByLabel("Latitude").fill("41.6");
  await page.getByLabel("Longitude").fill("-93.6");
  await page.getByRole("button", { name: "Add pantry", exact: true }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await nav(page, "Inventory");
  await page
    .getByRole("button", { name: "Add food lot", exact: true })
    .first()
    .click();
  await page
    .getByLabel("Pantry", { exact: true })
    .selectOption({ label: "QA West" });
  await page.getByLabel("Food name").fill("Apples");
  await page.getByLabel("Stock on hand").fill("50");
  await page.getByLabel("Protected reserve").fill("20");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Add food lot", exact: true })
    .click();
  await expect(page.locator("tbody")).toContainText("30 lb");
  await nav(page, "Pantries & needs");
  await page
    .getByRole("button", { name: "Add service need", exact: true })
    .click();
  await page.getByLabel("Receiving pantry").selectOption({ label: "QA West" });
  await page.getByLabel("Total need (lb)").fill("10");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Add service need", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Close", exact: true })
    .first()
    .click();
  await page
    .getByRole("dialog")
    .locator("textarea")
    .fill("Service entered in error");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Close service need", exact: true })
    .click();
  await expect(page.locator(".service-table")).toContainText("Closed");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByLabel("Email address").fill(email);
  await page.getByLabel(/^Password/).fill("Test only passphrase 2026!");
  await page
    .getByRole("button", { name: "Sign in", exact: true })
    .last()
    .click();
  await expect(
    page.getByRole("heading", { name: "Every connection counts." }),
  ).toBeVisible();
});
test("mobile layout and keyboard-accessible dialog", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await demo(page);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await nav(page, "Inventory");
  await page
    .getByRole("button", { name: "Add food lot", exact: true })
    .first()
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
});
test("landing and all workspace screens meet automated WCAG A/AA checks", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Explore the live demo" }).waitFor();
  for (const view of [
    "landing",
    "overview",
    "planner",
    "Inventory",
    "Pantries & needs",
    "Deliveries",
    "Impact & reports",
    "Your team",
  ]) {
    if (view === "overview") {
      await page.getByRole("button", { name: "Explore the live demo" }).click();
      await page
        .getByRole("heading", { name: "Every connection counts." })
        .waitFor();
    }
    if (view === "planner") {
      await nav(page, "Relay planner");
      await page
        .getByRole("button", { name: "Find matches", exact: true })
        .click();
      await page
        .getByRole("button", { name: "Reserve this relay" })
        .first()
        .waitFor();
    }
    if (
      [
        "Inventory",
        "Pantries & needs",
        "Deliveries",
        "Impact & reports",
        "Your team",
      ].includes(view)
    ) {
      await nav(page, view);
      if (view === "Your team")
        await expect(page.locator(".team-member").first()).toBeVisible();
    }
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    await testInfo.attach(
      `axe-${view.toLowerCase().replace(/[^a-z]+/g, "-")}`,
      {
        body: JSON.stringify(results.violations, null, 2),
        contentType: "application/json",
      },
    );
    expect(results.violations, view).toEqual([]);
  }
});
test("invited driver joins with separate credentials and sees transport actions only", async ({
  browser,
  page,
}) => {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Start a network", exact: true })
    .click();
  await page.getByLabel("Your full name").fill("Invitation Admin");
  await page
    .getByLabel("Network name", { exact: true })
    .fill("Invite QA Network");
  await page
    .getByLabel("Email address")
    .fill(`admin-${Date.now()}@example.org`);
  await page.getByLabel(/^Password/).fill("A private test passphrase2026");
  await page
    .getByRole("button", { name: "Create network", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Every connection counts." }),
  ).toBeVisible();
  await nav(page, "Your team");
  await page
    .getByRole("button", { name: "Invite teammate", exact: true })
    .click();
  await page.getByLabel("Team member role").selectOption("driver");
  await page
    .getByRole("button", { name: "Create invitation", exact: true })
    .click();
  const invite = await page.getByLabel("Private invitation link").inputValue();
  const transfer = await createOperationalFixture(page);
  const context = await browser.newContext();
  const driver = await context.newPage();
  await driver.goto(invite);
  await driver.getByLabel("Your full name").fill("Volunteer Driver");
  await driver
    .getByLabel("Email address")
    .fill(`driver-${Date.now()}@example.org`);
  await driver.getByLabel(/^Password/).fill("Another private test2026");
  await driver
    .getByRole("button", { name: "Join network", exact: true })
    .click();
  await expect(
    driver.getByRole("heading", { name: "Your delivery board." }),
  ).toBeVisible();
  await expect(
    driver.getByRole("button", { name: "Inventory", exact: true }),
  ).toHaveCount(0);
  await expect(
    driver.getByRole("button", { name: "Your team", exact: true }),
  ).toHaveCount(0);
  await expect(
    driver.getByRole("button", { name: "Accept at destination", exact: true }),
  ).toHaveCount(0);
  await driver
    .getByRole("button", { name: "Record pickup", exact: true })
    .click();
  await driver.getByRole("checkbox", { name: /Condition checked/ }).check();
  await driver
    .getByRole("button", { name: "Confirm pickup", exact: true })
    .click();
  await driver
    .getByRole("button", { name: "Mark arrived", exact: true })
    .click();
  await driver
    .getByRole("dialog")
    .getByRole("button", { name: "Mark arrived", exact: true })
    .click();
  await expect(driver.getByRole("dialog")).toBeHidden();
  await expect(
    driver.getByRole("button", { name: "Confirm receipt", exact: true }),
  ).toHaveCount(0);
  await expect(driver.locator(".delivery-card")).toContainText(
    "Awaiting coordinator receipt",
  );
  expect(
    (await workspace(page)).transfers.find((t) => t.id === transfer.id)?.status,
  ).toBe("arrived");
  await context.close();
});
test("expired authenticated session returns to sign-in instead of trapping workspace", async ({
  page,
  context,
}) => {
  await demo(page);
  await context.clearCookies();
  await page
    .getByRole("button", { name: "Refresh workspace", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Explore the live demo" }),
  ).toBeVisible();
});
