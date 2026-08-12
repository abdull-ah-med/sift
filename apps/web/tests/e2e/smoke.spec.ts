import { test, expect } from "@playwright/test";

test("landing and auth chrome render", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: "sift" }).first()).toBeVisible();
  await expect(
    page.getByRole("heading", { name: /Document intelligence/i }),
  ).toBeVisible();

  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Save API key" })).toBeVisible();

  await page.goto("/signup");
  await expect(page.getByRole("heading", { name: "Get started" })).toBeVisible();
});

test("app shell collections with API key from env", async ({ page }) => {
  const key = process.env.SIFT_API_KEY;
  test.skip(!key, "SIFT_API_KEY required");
  await page.goto("/login");
  await page.getByLabel("API key").fill(key!);
  await page.getByRole("button", { name: "Save API key" }).click();
  await page.goto("/collections");
  await expect(page.getByRole("heading", { name: "Collections" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Search/i })).toBeVisible();
});

test("chat route shell mounts", async ({ page }) => {
  await page.goto("/collections/demo/chat?id=col_demo");
  await expect(page.getByRole("heading", { name: /Chat/i })).toBeVisible();
  await expect(page.getByText("Sessions", { exact: true })).toBeVisible();
  await expect(page.getByText("Citations", { exact: true })).toBeVisible();
});
