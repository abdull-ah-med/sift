import { test, expect } from "@playwright/test";

test("home and login render", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/");
  await expect(page.getByRole("heading", { name: "sift" })).toBeVisible();
  await page.goto("http://127.0.0.1:3000/login");
  await expect(page.getByRole("heading", { name: "Login" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Save API key" })).toBeVisible();
});

test("collections with API key from env", async ({ page }) => {
  const key = process.env.SIFT_API_KEY;
  test.skip(!key, "SIFT_API_KEY required");
  await page.goto("http://127.0.0.1:3000/login");
  await page.getByLabel("API key").fill(key!);
  await page.getByRole("button", { name: "Save API key" }).click();
  await page.goto("http://127.0.0.1:3000/collections");
  await expect(page.getByRole("heading", { name: "Collections" })).toBeVisible();
});
