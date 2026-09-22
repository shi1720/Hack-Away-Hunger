import { expect, type Page } from "@playwright/test";
import type { Proposal, Transfer, Workspace } from "../frontend/src/types";

export const transport = {
  max_distance_miles: 50,
  vehicle_capacity_lb: 500,
  refrigerated: true,
};

export async function demo(page: Page) {
  await page.goto("/");
  await page
    .getByRole("button", { name: "Explore the live demo", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Every connection counts." }),
  ).toBeVisible();
  return workspace(page);
}

export async function nav(page: Page, name: string) {
  const toggle = page.getByRole("button", {
    name: "Open navigation",
    exact: true,
  });
  if (await toggle.isVisible()) await toggle.click();
  const button = page
    .getByRole("navigation", { name: "Main navigation", exact: true })
    .getByRole("button", { name, exact: true });
  await button.click();
  await expect(page.locator(".breadcrumb strong")).toHaveText(name);
  if (await toggle.isVisible())
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
}

export async function workspace(page: Page): Promise<Workspace> {
  const response = await page.request.get("/api/workspace");
  expect(response.ok(), await response.text()).toBeTruthy();
  return response.json();
}

export async function mutate<T>(
  page: Page,
  path: string,
  data: unknown,
  method = "POST",
): Promise<T> {
  const auth = await (await page.request.get("/api/auth/me")).json();
  const response = await page.request.fetch(`/api${path}`, {
    method,
    data,
    headers: { "X-CSRF-Token": auth.csrf_token },
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  return response.json();
}

export async function reserveFixture(
  page: Page,
  category = "produce",
): Promise<Transfer> {
  const plan = await mutate<{ proposals: Proposal[] }>(
    page,
    "/planner",
    transport,
  );
  const proposal = plan.proposals.find((p) => p.category === category);
  expect(
    proposal,
    `A ${category} match must exist in this isolated fixture`,
  ).toBeTruthy();
  return mutate<Transfer>(page, "/transfers", {
    ...transport,
    lot_id: proposal!.lot_id,
    need_id: proposal!.need_id,
    quantity_lb: proposal!.quantity_lb,
  });
}

export async function advanceFixture(
  page: Page,
  transfer: Transfer,
  target: "accepted" | "in_transit" | "arrived",
) {
  await mutate(page, `/transfers/${transfer.id}/accept`, {
    receiver_name: "Fixture receiver",
  });
  if (target !== "accepted")
    await mutate(page, `/transfers/${transfer.id}/pickup`, {
      condition_confirmed: true,
      temperature_f:
        transfer.storage === "ambient"
          ? null
          : transfer.storage === "chilled"
            ? 38
            : -2,
    });
  if (target === "arrived")
    await mutate(page, `/transfers/${transfer.id}/arrive`, {});
}

export async function refresh(page: Page) {
  const response = page.waitForResponse(
    (r) => r.url().endsWith("/api/workspace") && r.request().method() === "GET",
  );
  await page
    .getByRole("button", { name: "Refresh workspace", exact: true })
    .click();
  expect((await response).ok()).toBeTruthy();
  await expect(page.getByRole("status")).toContainText(
    "Network is up to date.",
  );
}

export async function dismissToast(page: Page) {
  const close = page.getByRole("button", {
    name: "Dismiss notification",
    exact: true,
  });
  if (await close.isVisible()) await close.click();
}

export async function createOperationalFixture(page: Page) {
  const source = await mutate<{ id: string }>(page, "/sites", {
    name: "Driver fixture source",
    city: "Des Moines",
    address: "100 Fixture Street",
    lat: 41.6,
    lng: -93.6,
    storage_types: ["ambient"],
    capacity_lb: 1000,
    notes: "Fictitious test location",
  });
  const destination = await mutate<{ id: string }>(page, "/sites", {
    name: "Driver fixture destination",
    city: "Des Moines",
    address: "200 Fixture Street",
    lat: 41.62,
    lng: -93.62,
    storage_types: ["ambient"],
    capacity_lb: 1000,
    notes: "Fictitious test location",
  });
  await mutate(page, "/lots", {
    site_id: source.id,
    food_name: "Driver fixture apples",
    category: "produce",
    storage: "ambient",
    quantity_lb: 100,
    reserve_lb: 20,
    expires_at: new Date(Date.now() + 5 * 86400000).toISOString(),
    restricted: false,
    notes: "Browser test fixture",
  });
  await mutate(page, "/needs", {
    site_id: destination.id,
    category: "produce",
    quantity_lb: 50,
    service_at: new Date(Date.now() + 86400000).toISOString(),
    notes: "Browser test fixture",
  });
  const transfer = await reserveFixture(page);
  await advanceFixture(page, transfer, "accepted");
  return transfer;
}
