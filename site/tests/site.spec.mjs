import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
test("both languages and themes pass automated accessibility checks", async ({
  page,
}) => {
  for (const path of ["/", "/zh/"]) {
    await page.goto(path);
    for (const colorScheme of ["light", "dark"]) {
      await page.emulateMedia({ colorScheme });
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze();
      expect(results.violations).toEqual([]);
    }
  }
});
for (const [path, lang] of [
  ["/", "en"],
  ["/zh/", "zh-CN"],
]) {
  test(`${lang} has static SEO, correct links and working demo`, async ({
    page,
    request,
  }) => {
    const response = await request.get(path);
    const html = await response.text();
    expect(response.status()).toBe(200);
    expect(html).toContain("<h1>");
    expect(html).toContain("application/ld+json");
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(path);
    await expect(page.locator("html")).toHaveAttribute("lang", lang);
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.locator("link[rel=canonical]")).toHaveAttribute(
      "href",
      `https://sideword.vercel.app${path}`,
    );
    await expect(page.locator("link[hreflang]")).toHaveCount(3);
    await page.locator('[data-word="1"]').click();
    await expect(page.locator(".word")).toHaveText("maintain");
    await page.locator(".remember").click();
    await expect(page.locator('[data-word="1"]')).toBeDisabled();
    await page.locator(".remember").click();
    await page.locator(".remember").click();
    await expect(page.locator(".remember")).toBeDisabled();
    await expect(page.locator(".demo-count")).toContainText("0");
    await page.locator(".reset").click();
    await expect(page.locator(".word")).toHaveText("adapt");
    await page.locator(".theme").click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await page.locator(".language").click();
    await expect(page.locator("html")).toHaveAttribute(
      "lang",
      lang === "en" ? "zh-CN" : "en",
    );
    expect(errors).toEqual([]);
  });
  for (const width of [320, 390, 1440]) {
    test(`${lang} fits ${width}px and both themes`, async ({ page }) => {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(path);
      for (const scheme of ["light", "dark"]) {
        await page.emulateMedia({
          colorScheme: scheme,
          reducedMotion: "reduce",
        });
        await expect(page.locator("h1")).toBeVisible();
        expect(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
        ).toBe(true);
      }
    });
  }
}
test("copy command succeeds and failure stays recoverable", async ({
  page,
}) => {
  await page.goto("/zh/");
  await page.evaluate(() =>
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async (text) => {
          window.copied = text;
        },
      },
    }),
  );
  await page.locator(".copy").click();
  await expect(page.locator(".copy-status")).toHaveText("已复制");
  expect(await page.evaluate(() => window.copied)).toContain(
    "v0.4.0-beta.1/install.sh",
  );
  await page.evaluate(() =>
    Object.defineProperty(navigator, "clipboard", {
      value: {
        writeText: async () => {
          throw new Error("blocked");
        },
      },
    }),
  );
  await page.locator(".copy").click();
  await expect(page.locator(".copy-status")).toContainText("手动复制");
});
test("crawl assets and not-found response", async ({ request }) => {
  for (const path of [
    "/robots.txt",
    "/sitemap.xml",
    "/assets/mark.svg",
    "/assets/social.png",
    "/assets/manrope.woff2",
  ])
    expect((await request.get(path)).status()).toBe(200);
  expect((await request.get("/missing-page/")).status()).toBe(404);
  expect(await (await request.get("/robots.txt")).text()).toContain(
    "Sitemap: https://sideword.vercel.app/sitemap.xml",
  );
});
test("content and installation remain available without JavaScript", async ({
  browser,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto((process.env.BASE_URL || "http://127.0.0.1:4173") + "/zh/");
  await expect(page.locator("h1")).toBeVisible();
  await expect(page.locator(".install-command")).toContainText("curl");
  await page.locator(".faq summary").first().click();
  await expect(page.locator(".faq details").first()).toHaveAttribute(
    "open",
    "",
  );
  await context.close();
});
