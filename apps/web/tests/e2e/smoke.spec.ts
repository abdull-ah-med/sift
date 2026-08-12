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
  await expect(page.getByRole("heading", { name: "Upload", exact: true })).toBeVisible();
});

test("landing canvas is pure black with a pill navbar", async ({ page }) => {
  await page.goto("/");
  const background = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  expect(background).toBe("rgb(0, 0, 0)");
  const radius = await page.locator("header > div").first().evaluate((el) => {
    return getComputedStyle(el).borderRadius;
  });
  expect(Number.parseFloat(radius)).toBeGreaterThan(20);
  await expect(page.getByText("© 2026 sift")).toBeVisible();
});

test("primary fill is #1b6986 with light text", async ({ page }) => {
  await page.goto("/");
  const cta = page.getByRole("link", { name: "Get started" }).first();
  const styles = await cta.evaluate((el) => {
    const computed = getComputedStyle(el);
    return { background: computed.backgroundColor, color: computed.color };
  });
  expect(styles.background).toBe("rgb(27, 105, 134)");
  expect(styles.color).toBe("rgb(238, 238, 238)");
});

test("landing does not load watermelon CDN, Google auth, or fake uptime", async ({ page }) => {
  await page.goto("/");
  const srcs = await page.locator("img").evaluateAll((els) =>
    els.map((el) => el.getAttribute("src") ?? ""),
  );
  expect(srcs.join("\n")).not.toMatch(/watermelon\.sh/i);
  await expect(page.getByText("99.99%")).toHaveCount(0);
  await expect(page.getByRole("button", { name: /google/i })).toHaveCount(0);
});

test("Lenis attaches on marketing and not on the app shell", async ({ page }) => {
  await page.goto("/");
  await expect.poll(async () => page.locator("html").getAttribute("class")).toMatch(/lenis/);
  await seedApiKey(page);
  await mockWorkspace(page);
  await page.goto("/home");
  await expect(page.getByRole("heading", { name: "Home" })).toBeVisible();
  await expect(page.locator("html")).not.toHaveClass(/lenis/);
});

test("Lenis does not attach when the user prefers reduced motion", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Document intelligence you can trust/i })).toBeVisible();
  await expect(page.locator("html")).not.toHaveClass(/lenis/);
});

test("login and signup chrome render", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Save API key" })).toBeVisible();
  await expect(page.getByLabel("API key")).toBeVisible();
  await expect(page.getByRole("button", { name: /google/i })).toHaveCount(0);
  await expect(page.locator("img[src*='watermelon']")).toHaveCount(0);
  const panel = page.locator("aside").first();
  await expect(panel).toBeVisible();
  await expect(panel).toHaveCSS("background-image", /noise-gradient\.png/);

  await page.goto("/signup");
  await expect(page.getByRole("heading", { name: "Get started" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Continue to sign in" })).toBeVisible();
});

test("login and signup stylesheets return 200", async ({ page, request }) => {
  for (const path of ["/login", "/signup"] as const) {
    const nav = await page.goto(path);
    expect(nav?.ok(), path).toBeTruthy();
    const hrefs = await page.evaluate(() =>
      [...document.querySelectorAll('link[rel="stylesheet"], link[rel="preload"][as="style"]')]
        .map((el) => (el as HTMLLinkElement).href)
        .filter((href) => href.includes("/_next/")),
    );
    expect(hrefs.length, `${path} stylesheet links`).toBeGreaterThan(0);
    for (const href of hrefs) {
      const res = await request.get(href);
      expect(res.status(), `${path} ${href}`).toBe(200);
    }
    const color = await page.locator("h1").first().evaluate((el) => getComputedStyle(el).color);
    expect(color, path).toBe("rgb(238, 238, 238)");
  }
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
