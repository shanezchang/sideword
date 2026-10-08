// Deterministically rasterize our vector brand; no external rendering service.
import { chromium } from "@playwright/test";
import { readFile, mkdir } from "node:fs/promises";
const browser = await chromium.launch();
try {
  const page = await browser.newPage({
    viewport: { width: 1200, height: 630 },
    deviceScaleFactor: 1,
  });
  const font = (
    await readFile(
      "node_modules/@fontsource-variable/manrope/files/manrope-latin-wght-normal.woff2",
    )
  ).toString("base64");
  const mark = await readFile("public/assets/mark.svg", "utf8");
  await page.setContent(
    `<style>@font-face{font-family:Manrope;src:url(data:font/woff2;base64,${font})}*{box-sizing:border-box}body{margin:0;background:#f7faf8;color:#163630;font-family:Manrope,sans-serif}.canvas{padding:70px 78px;width:1200px;height:630px}.brand{display:flex;align-items:center;gap:12px;font-size:38px;font-weight:750;letter-spacing:-1.5px}.brand svg{width:50px;height:50px}h1{font-size:76px;line-height:1.1;letter-spacing:-3px;font-weight:650;margin:50px 0 30px}p{font-size:23px;color:#51665e}.command{position:absolute;right:78px;bottom:78px;border:1px solid #bfd8cb;padding:14px 24px;border-radius:7px;color:#14776b;font-size:21px}</style><div class="canvas"><div class="brand">${mark}sideword</div><h1>A few words.<br>Right in your terminal.</h1><p>Open-source English learning. At your own pace.</p><div class="command">$ sideword</div></div>`,
  );
  await page.evaluate(() => document.fonts.ready);
  await mkdir("public/assets", { recursive: true });
  await page.screenshot({ path: "public/assets/social.png" });
  await page.setViewportSize({ width: 180, height: 180 });
  await page.setContent(
    `<style>body{margin:0;background:#e3f2ec;display:grid;place-items:center;width:180px;height:180px}svg{width:130px;height:130px}</style>${mark}`,
  );
  await page.screenshot({ path: "public/assets/apple-touch-icon.png" });
} finally {
  await browser.close();
}
