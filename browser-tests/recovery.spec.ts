import { test, expect } from "@playwright/test";
import {
  advanceFixture,
  demo,
  dismissToast,
  mutate,
  nav,
  refresh,
  reserveFixture,
  workspace,
} from "./helpers";

test("cancel a committed relay, release stock and close the mistaken need", async ({
  page,
}) => {
  const before = await demo(page);
  const transfer = await reserveFixture(page);
  await refresh(page);
  await nav(page, "Pantries & needs");
  const category =
    transfer.category[0].toUpperCase() + transfer.category.slice(1);
  const need = page
    .locator(".service-table tbody tr")
    .filter({
      hasText: before.sites.find((s) => s.id === transfer.destination_id)!.name,
    })
    .filter({ hasText: category })
    .first();
  await need.getByRole("button", { name: "Close", exact: true }).click();
  await page
    .getByLabel("Reason for closing", { exact: true })
    .fill("An operator entered the wrong service date.");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Close service need", exact: true })
    .click();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText(
    "Resolve all active transfers",
  );
  await page.keyboard.press("Escape");
  await nav(page, "Deliveries");
  await page.getByRole("button", { name: "Cancel relay", exact: true }).click();
  await page
    .getByLabel("Reason for cancellation", { exact: true })
    .fill("Correcting the receiving service request.");
  await page
    .getByRole("button", { name: "Cancel transfer", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden();
  const after = await workspace(page);
  expect(after.metrics.active_transfers).toBe(0);
  expect(after.lots.find((l) => l.id === transfer.lot_id)?.available_lb).toBe(
    before.lots.find((l) => l.id === transfer.lot_id)?.available_lb,
  );
  await nav(page, "Pantries & needs");
  await need.getByRole("button", { name: "Close", exact: true }).click();
  await page
    .getByLabel("Reason for closing", { exact: true })
    .fill("Closed the mistaken request after releasing its commitment.");
  await page
    .getByRole("button", { name: "Close service need", exact: true })
    .click();
  await expect(need).toContainText("Closed");
});

test("reject a complete cold shipment without inventing a temperature or received weight", async ({
  page,
}) => {
  await demo(page);
  const transfer = await reserveFixture(page, "dairy");
  await advanceFixture(page, transfer, "arrived");
  await refresh(page);
  await nav(page, "Deliveries");
  await page
    .getByRole("button", { name: "Confirm receipt", exact: true })
    .click();
  await page.getByLabel("Actual food received (lb)", { exact: true }).fill("0");
  const temperature = page.getByLabel("Measured food temperature (°F)", {
    exact: true,
  });
  await expect(temperature).not.toHaveAttribute("required", "");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirm receipt", exact: true })
    .click();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText(
    "Explain the difference",
  );
  await page
    .getByLabel("Exception note", { exact: true })
    .fill(
      "Shipment rejected in full after packaging damage. No food accepted.",
    );
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirm receipt", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden();
  const after = await workspace(page);
  expect(after.metrics.received_lb).toBe(0);
  expect(after.metrics.active_transfers).toBe(0);
  expect(after.needs.find((n) => n.id === transfer.need_id)?.remaining_lb).toBe(
    transfer.quantity_lb,
  );
  await nav(page, "Impact & reports");
  await expect(page.locator("tbody")).toContainText("0 lb");
  await expect(page.locator("tbody")).toContainText(
    "Shipment rejected in full",
  );
});

test("an unsafe positive cold receipt stays blocked and can recover to a valid receipt", async ({
  page,
}) => {
  await demo(page);
  const transfer = await reserveFixture(page, "dairy");
  await advanceFixture(page, transfer, "arrived");
  await refresh(page);
  await nav(page, "Deliveries");
  await page
    .getByRole("button", { name: "Confirm receipt", exact: true })
    .click();
  await page
    .getByLabel("Measured food temperature (°F)", { exact: true })
    .fill("60");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirm receipt", exact: true })
    .click();
  await expect(page.getByRole("dialog").getByRole("alert")).toBeVisible();
  expect((await workspace(page)).metrics.received_lb).toBe(0);
  await page
    .getByLabel("Measured food temperature (°F)", { exact: true })
    .fill("38");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Confirm receipt", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden();
  expect((await workspace(page)).metrics.received_lb).toBe(
    transfer.quantity_lb,
  );
});

test("failed dispatch records the loss without a false arrival or restoring source stock", async ({
  page,
}) => {
  const before = await demo(page);
  const transfer = await reserveFixture(page);
  await advanceFixture(page, transfer, "in_transit");
  await refresh(page);
  await nav(page, "Deliveries");
  await page
    .getByRole("button", { name: "Report failed delivery", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toContainText(
    "will not be returned to inventory",
  );
  await page
    .getByLabel("Reason for delivery failure", { exact: true })
    .fill(
      "Vehicle breakdown. Food could not reach the destination and was discarded under local policy.",
    );
  await page
    .getByRole("button", { name: "Report delivery failure", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden();
  const after = await workspace(page);
  expect(after.transfers.find((t) => t.id === transfer.id)?.status).toBe(
    "failed",
  );
  expect(after.metrics.active_transfers).toBe(0);
  expect(after.metrics.received_lb).toBe(0);
  expect(after.lots.find((l) => l.id === transfer.lot_id)?.quantity_lb).toBe(
    before.lots.find((l) => l.id === transfer.lot_id)!.quantity_lb -
      transfer.quantity_lb,
  );
  expect(after.events.some((e) => e.action === "transfer.arrived")).toBe(false);
  await page.getByRole("button", { name: /^All activity/ }).click();
  await expect(page.locator(".delivery-card")).toContainText("Failed");
  await expect(page.locator(".delivery-card")).toContainText("not received");
});

test("stale inventory does not overwrite a teammate and offers a reload recovery", async ({
  page,
}) => {
  const before = await demo(page);
  const lot = before.lots.find(
    (l) => l.food_name === "Harvest apples & carrots",
  )!;
  await nav(page, "Inventory");
  const row = page.locator("tbody tr").filter({ hasText: lot.food_name });
  await row.getByRole("button", { name: "Adjust", exact: true }).click();
  await mutate(
    page,
    `/lots/${lot.id}`,
    { version: lot.version, quantity_lb: lot.quantity_lb + 5 },
    "PATCH",
  );
  await page
    .getByLabel("Stock on hand (lb)", { exact: true })
    .fill(String(lot.quantity_lb + 2));
  await page
    .getByRole("button", { name: "Save adjustment", exact: true })
    .click();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText(
    "Stock changed since you opened this form",
  );
  await page
    .getByRole("button", { name: "Close and reload latest stock", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden();
  await row.getByRole("button", { name: "Adjust", exact: true }).click();
  await expect(
    page.getByLabel("Stock on hand (lb)", { exact: true }),
  ).toHaveValue(String(lot.quantity_lb + 5));
});

test("a saved mutation followed by a failed refresh is not submitted twice", async ({
  page,
}) => {
  const before = await demo(page);
  await nav(page, "Inventory");
  await page
    .getByRole("button", { name: "Add food lot", exact: true })
    .first()
    .click();
  await page
    .getByLabel("Pantry", { exact: true })
    .selectOption(before.sites[0].id);
  await page
    .getByLabel("Food name", { exact: true })
    .fill("Refresh recovery fixture");
  await page.getByLabel("Stock on hand (lb)", { exact: true }).fill("1");
  await page.route(
    "**/api/workspace",
    (route) =>
      route.fulfill({
        status: 503,
        json: { detail: "Temporary refresh outage" },
      }),
    { times: 1 },
  );
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Add food lot", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden();
  await expect(page.getByRole("alert")).toContainText("Your change was saved");
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.getByRole("alert")).toBeHidden();
  await expect(
    page.locator("tbody tr").filter({ hasText: "Refresh recovery fixture" }),
  ).toHaveCount(1);
  expect(
    (await workspace(page)).lots.filter(
      (l) => l.food_name === "Refresh recovery fixture",
    ),
  ).toHaveLength(1);
});

test("planner reservation remains clearly saved when its refresh fails", async ({
  page,
}) => {
  await demo(page);
  await nav(page, "Relay planner");
  await page.getByRole("button", { name: "Find matches", exact: true }).click();
  await expect(page.locator(".proposal-card").first()).toBeVisible();
  await page.route(
    "**/api/workspace",
    (route) =>
      route.fulfill({
        status: 503,
        json: { detail: "Temporary refresh outage" },
      }),
    { times: 1 },
  );
  await page
    .getByRole("button", { name: "Reserve this relay", exact: true })
    .first()
    .click();
  await expect(page.getByRole("alert")).toContainText(
    "Your relay was reserved",
  );
  await expect(
    page.getByRole("button", { name: "Reserve this relay", exact: true }),
  ).toHaveCount(0);
  await refresh(page);
  await nav(page, "Deliveries");
  await expect(page.locator(".delivery-card")).toHaveCount(1);
});

test("empty matching result explains constraints and recovers when the range is widened", async ({
  page,
}) => {
  await demo(page);
  await nav(page, "Relay planner");
  await page.getByLabel("Maximum distance (miles)", { exact: true }).fill("1");
  await page.getByRole("button", { name: "Find matches", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: "No workable matches right now",
      exact: true,
    }),
  ).toBeVisible();
  await page.getByLabel("Maximum distance (miles)", { exact: true }).fill("50");
  await page.getByRole("button", { name: "Find matches", exact: true }).click();
  await expect(page.locator(".proposal-card")).toHaveCount(3);
});

test("expired session while downloading a report returns to authentication", async ({
  page,
  context,
}) => {
  await demo(page);
  await nav(page, "Impact & reports");
  await context.clearCookies();
  await page
    .getByRole("button", { name: "Export receipts", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("alert")).toContainText(
    "Your session has expired",
  );
});

test("mobile navigation traps focus, closes with Escape and leaves hidden links inert", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await demo(page);
  await dismissToast(page);
  const open = page.getByRole("button", {
    name: "Open navigation",
    exact: true,
  });
  await open.click();
  const drawer = page.getByRole("dialog", {
    name: "Workspace navigation",
    exact: true,
  });
  await expect(drawer).toBeVisible();
  await expect(page.locator(".app-main")).toHaveAttribute("inert", "");
  await expect(
    page.getByRole("button", { name: "Close navigation", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(
    page.getByRole("button", { name: "Sign out", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("button", { name: "Close navigation", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(drawer).toHaveCount(0);
  await expect(open).toBeFocused();
  await expect(page.locator(".sidebar")).toHaveAttribute("inert", "");
  await nav(page, "Deliveries");
  await expect(
    page.getByRole("heading", {
      name: "Every handoff, accounted for.",
      exact: true,
    }),
  ).toBeVisible();
});

for (const width of [320, 390]) {
  test(`all operational screens fit a ${width}px mobile viewport`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 844 });
    await demo(page);
    for (const view of [
      "Overview",
      "Relay planner",
      "Inventory",
      "Pantries & needs",
      "Deliveries",
      "Impact & reports",
      "Your team",
    ]) {
      await nav(page, view);
      await expect
        .poll(
          () =>
            page.evaluate(
              () => document.documentElement.scrollWidth <= window.innerWidth,
            ),
          { message: `${view} should not overflow ${width}px` },
        )
        .toBeTruthy();
      await expect(page.locator(".page-heading h1")).toBeVisible();
    }
  });
}

test("inventory search and categories keep restricted stock clearly unshareable", async ({
  page,
}) => {
  await demo(page);
  await nav(page, "Inventory");
  await page
    .getByRole("textbox", { name: "Search food or pantry", exact: true })
    .fill("turkey");
  const rows = page.locator("tbody tr");
  await expect(rows).toHaveCount(1);
  await expect(rows).toContainText("Restricted");
  await expect(rows.locator("td").nth(4)).toHaveText("0 lb");
  await page
    .getByRole("combobox", { name: "Filter by category", exact: true })
    .selectOption("dairy");
  await expect(
    page.getByRole("heading", {
      name: "No food matches this search",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("textbox", { name: "Search food or pantry", exact: true })
    .fill("");
  await expect(rows).toHaveCount(1);
  await expect(rows).toContainText("Fresh milk");
});

test("print manifest includes actual locations, deadlines and the sample data notice", async ({
  page,
}) => {
  await demo(page);
  const transfer = await reserveFixture(page);
  await refresh(page);
  await nav(page, "Deliveries");
  await page.evaluate(() => {
    (window as unknown as { printCount: number }).printCount = 0;
    window.print = () => {
      (window as unknown as { printCount: number }).printCount += 1;
    };
  });
  await page
    .getByRole("button", { name: "Print manifest", exact: true })
    .click();
  await expect
    .poll(() =>
      page.evaluate(
        () => (window as unknown as { printCount: number }).printCount,
      ),
    )
    .toBe(1);
  await page.emulateMedia({ media: "print" });
  const manifest = page.locator(".print-manifest");
  await expect(manifest).toBeVisible();
  await expect(manifest).toContainText(transfer.id);
  await expect(manifest).toContainText("Receiving service:");
  await expect(manifest).toContainText("Operational use-by cutoff:");
  await expect(manifest).toContainText("120 lb");
  await expect(manifest).toContainText(
    "Fictitious organizations and sample data.",
  );
  await expect(page.locator(".sidebar")).toBeHidden();
});

test("temporary API failure preserves form input and gives a readable retry message", async ({
  page,
}) => {
  await demo(page);
  await nav(page, "Pantries & needs");
  await page.getByRole("button", { name: "Add pantry", exact: true }).click();
  await page
    .getByLabel("Pantry name", { exact: true })
    .fill("Retry fixture pantry");
  await page.getByLabel("City", { exact: true }).fill("Des Moines");
  await page
    .getByLabel("Street address", { exact: true })
    .fill("300 Fixture Street");
  await page.getByLabel("Latitude", { exact: true }).fill("41.6");
  await page.getByLabel("Longitude", { exact: true }).fill("-93.6");
  await page.route("**/api/sites", (route) => route.abort("failed"), {
    times: 1,
  });
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Add pantry", exact: true })
    .click();
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText(
    "Could not reach Pantry Relay",
  );
  await expect(page.getByLabel("Pantry name", { exact: true })).toHaveValue(
    "Retry fixture pantry",
  );
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Add pantry", exact: true })
    .click();
  await expect(page.getByRole("dialog")).toBeHidden();
  await expect(
    page.getByRole("heading", { name: "Retry fixture pantry", exact: true }),
  ).toBeVisible();
});

test("signing out from the mobile drawer restores page scrolling and clears navigation", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await demo(page);
  await page
    .getByRole("button", { name: "Open navigation", exact: true })
    .click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Explore the live demo", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("dialog", { name: "Workspace navigation", exact: true }),
  ).toHaveCount(0);
  expect(await page.evaluate(() => document.body.style.overflow)).not.toBe(
    "hidden",
  );
});

for (const viewport of [
  { width: 1600, height: 800 },
  { width: 1280, height: 600 },
]) {
  test(`desktop sidebar remains reachable after recording scroll sequence at ${viewport.width}x${viewport.height}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await demo(page);
    const transfer = await reserveFixture(page);
    await advanceFixture(page, transfer, "arrived");
    await mutate(page, `/transfers/${transfer.id}/receive`, {
      received_lb: 112,
      temperature_f: null,
      receiver_name: "Recording fixture receiver",
      exception_reason: "8 lb damaged in transit, sample scenario.",
    });
    await refresh(page);
    await nav(page, "Pantries & needs");
    await page.locator(".service-table").scrollIntoViewIfNeeded();
    await nav(page, "Inventory");
    await page
      .getByRole("row")
      .filter({ hasText: "Harvest apples & carrots" })
      .filter({ hasText: "112 lb" })
      .last()
      .scrollIntoViewIfNeeded();
    await nav(page, "Impact & reports");
    await expect(page.locator(".impact-hero")).toContainText("112");
    const signOut = page.getByRole("button", { name: "Sign out", exact: true });
    await signOut.scrollIntoViewIfNeeded();
    await expect(signOut).toBeInViewport({ ratio: 1 });
    await signOut.click();
    await expect(
      page.getByRole("button", { name: "Start a network", exact: true }),
    ).toBeVisible();
  });
}
