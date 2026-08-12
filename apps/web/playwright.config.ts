import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  use: {
    baseURL: "http://127.0.0.1:3000",
  },
  webServer: {
    // apps/web uses output: "standalone" — build it, then run the Node server.
    command: "pnpm exec next build && node .next/standalone/apps/web/server.js",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
    env: {
      PORT: "3000",
      HOSTNAME: "127.0.0.1",
    },
  },
});
