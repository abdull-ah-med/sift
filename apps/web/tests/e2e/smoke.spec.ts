import { test, expect, type Page } from "@playwright/test";

async function seedApiKey(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem("sift_api_key", "sift_test_e2e");
  });
}

async function mockWorkspace(page: Page, collections: unknown[] = []) {
  await page.route("**/v1/collections", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(collections),
      });
      return;
    }
    await route.continue();
  });
  await page.route("**/v1/tenants", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });
  await page.route("**/chat/sessions**", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
      return;
    }
    await route.continue();
  });
}

test("landing sections and skip link render", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator('a[href="#main"]')).toHaveText("Skip to content");
  await expect(page.getByRole("link", { name: "sift" }).first()).toBeVisible();
  await expect(
    page.getByRole("heading", { name: /Document intelligence you can trust/i }),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "How it works" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Open a collection/i })).toBeVisible();
});

test("login and signup chrome render", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Save API key" })).toBeVisible();
  await expect(page.getByLabel("API key")).toBeVisible();

  await page.goto("/signup");
  await expect(page.getByRole("heading", { name: "Get started" })).toBeVisible();
});

test("unauthenticated /home redirects to login", async ({ page }) => {
  await page.goto("/home");
  await page.waitForURL("**/login");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

test("unauthenticated /collections redirects to login", async ({ page }) => {
  await page.goto("/collections");
  await page.waitForURL("**/login");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

test("API key save lands on home", async ({ page }) => {
  await mockWorkspace(page);
  await page.goto("/login");
  await page.getByLabel("API key").fill("sift_test_e2e");
  await page.getByRole("button", { name: "Save API key" }).click();
  await page.waitForURL("**/home");
  await expect(page.getByRole("heading", { name: "Home" })).toBeVisible();
});

test("collections empty state", async ({ page }) => {
  await seedApiKey(page);
  await mockWorkspace(page, []);
  await page.goto("/collections");
  await expect(page.getByRole("heading", { name: "Collections" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Create", exact: true })).toBeVisible();
  await expect(page.getByText("No collections yet")).toBeVisible();
});

test("collections table header with rows", async ({ page }) => {
  await seedApiKey(page);
  await mockWorkspace(page, [{ id: "col_1", name: "Acme", slug: "acme" }]);
  await page.goto("/collections");
  await expect(page.getByRole("columnheader", { name: "Name" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Slug" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "Acme", exact: true })).toBeVisible();
});

test("chat route shell mounts when signed in", async ({ page }) => {
  await seedApiKey(page);
  await mockWorkspace(page);
  await page.goto("/collections/demo/chat?id=col_demo");
  await expect(page.getByRole("heading", { name: /Chat/i })).toBeVisible();
  await expect(page.getByText("Sessions", { exact: true })).toBeVisible();
  await expect(page.getByText("Citations", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Ask this collection" })).toBeVisible();
});
