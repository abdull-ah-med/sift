import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function seedApiKey(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem("sift_api_key", "sift_test_e2e");
  });
}

async function mockWorkspace(page: Page) {
  await page.route("**/v1/collections", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });
  await page.route("**/v1/tenants", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });
  await page.route("**/chat/sessions**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });
}

async function expectNoSeriousAxe(page: Page) {
  const results = await new AxeBuilder({ page }).analyze();
  const serious = results.violations.filter(
    (v) => v.impact === "serious" || v.impact === "critical",
  );
  expect(serious, JSON.stringify(serious, null, 2)).toEqual([]);
}

test("landing has no serious a11y violations", async ({ page }) => {
  await page.goto("/");
  await expectNoSeriousAxe(page);
});

test("login has no serious a11y violations", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await expectNoSeriousAxe(page);
});

test("home shell has no serious a11y violations", async ({ page }) => {
  await seedApiKey(page);
  await mockWorkspace(page);
  await page.goto("/home");
  await expect(page.getByRole("heading", { name: "Home" })).toBeVisible();
  await expectNoSeriousAxe(page);
});

test("chat shell has no serious a11y violations", async ({ page }) => {
  await seedApiKey(page);
  await mockWorkspace(page);
  await page.goto("/collections/demo/chat?id=col_demo");
  await expect(page.getByRole("heading", { name: /Chat/i })).toBeVisible();
  await expectNoSeriousAxe(page);
});
