import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  use: {
    baseURL: process.env.BASE_URL || "http://127.0.0.1:4173",
    browserName: "chromium",
  },
  webServer: process.env.BASE_URL
    ? undefined
    : {
        command: "node serve.mjs",
        url: "http://127.0.0.1:4173",
        reuseExistingServer: !process.env.CI,
      },
});
