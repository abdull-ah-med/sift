import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  use: {
    baseURL: "http://127.0.0.1:3010",
  },
  webServer: {
    // Standalone output does not include `_next/static`; copy it like the Dockerfile.
    command:
      "pnpm exec next build && mkdir -p .next/standalone/apps/web/.next && rm -rf .next/standalone/apps/web/.next/static .next/standalone/apps/web/public && cp -R .next/static .next/standalone/apps/web/.next/static && cp -R public .next/standalone/apps/web/public && node .next/standalone/apps/web/server.js",
    url: "http://127.0.0.1:3010",
    reuseExistingServer: false,
    timeout: 180_000,
    env: {
      PORT: "3010",
      HOSTNAME: "127.0.0.1",
    },
  },
});
