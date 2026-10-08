import { test, expect } from "@playwright/test";
import { analyticsAllowed, sanitizeEvent } from "../analytics.js";

test("analytics is production-only and honors privacy signals", () => {
  const location = { hostname: "sideword.vercel.app", protocol: "https:" };
  expect(analyticsAllowed(location, {})).toBe(true);
  expect(analyticsAllowed(location, { doNotTrack: "1" })).toBe(false);
  expect(analyticsAllowed(location, { globalPrivacyControl: true })).toBe(
    false,
  );
  expect(analyticsAllowed({ ...location, hostname: "localhost" }, {})).toBe(
    false,
  );
  expect(
    analyticsAllowed({ ...location, hostname: "preview.vercel.app" }, {}),
  ).toBe(false);
  expect(analyticsAllowed({ ...location, protocol: "http:" }, {})).toBe(false);
});

test("analytics strips URL input and rejects unknown pages", () => {
  expect(
    sanitizeEvent({
      type: "pageview",
      url: "https://sideword.vercel.app/zh/?email=test#secret",
    }),
  ).toEqual({ type: "pageview", url: "https://sideword.vercel.app/zh/" });
  expect(
    sanitizeEvent({ url: "https://sideword.vercel.app/private" }),
  ).toBeNull();
  expect(sanitizeEvent({ url: "invalid" })).toBeNull();
});

test("privacy opt-out does not break the demo", async ({ page }) => {
  await page.addInitScript(() =>
    Object.defineProperty(navigator, "globalPrivacyControl", { value: true }),
  );
  await page.goto("/");
  await page.locator(".remember").click();
  await expect(page.locator(".demo-count")).toContainText("2");
  await expect(page.locator('script[src*="insights"]')).toHaveCount(0);
});
