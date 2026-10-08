import { mkdir, readFile, writeFile, cp } from "node:fs/promises";
import { locales, words, repo, release, command } from "./content.mjs";

const origin = process.env.SITE_URL || "https://sideword.vercel.app";
const escape = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
await mkdir("dist/assets", { recursive: true });
await cp("public", "dist", { recursive: true });
await cp(
  "node_modules/@fontsource-variable/manrope/files/manrope-latin-wght-normal.woff2",
  "dist/assets/manrope.woff2",
);
await cp(
  "node_modules/@fontsource-variable/manrope/LICENSE",
  "dist/assets/Manrope-OFL.txt",
);
await cp("styles.css", "dist/assets/styles.css");
await cp("app.js", "dist/assets/app.js");
await cp("analytics.js", "dist/assets/analytics.js");
await cp(
  "node_modules/@vercel/analytics/dist/index.mjs",
  "dist/assets/vercel-analytics.mjs",
);
const mark = await readFile("public/assets/mark.svg", "utf8");
for (const [key, t] of Object.entries(locales)) {
  const schema = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "Sideword",
    url: origin + t.path,
    applicationCategory: "EducationalApplication",
    operatingSystem:
      "macOS 14+ (Apple Silicon binary); macOS and Linux (source)",
    softwareVersion: "0.4.0b1",
    description: t.description,
    isAccessibleForFree: true,
    license: repo + "/blob/main/LICENSE",
    downloadUrl: release,
    author: {
      "@type": "Person",
      name: "Shane Chang",
      url: "https://github.com/shanezchang",
    },
    offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
  };
  const html = `<!doctype html>
<html lang="${t.lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google-site-verification" content="oRful_sYpY7YjApxwjoJMXQQbFEZFEqeQG7a9V4vMcQ">
<title>${t.title}</title><meta name="description" content="${escape(t.description)}"><meta name="theme-color" content="#14776b">
<link rel="canonical" href="${origin + t.path}"><link rel="alternate" hreflang="en" href="${origin}/"><link rel="alternate" hreflang="zh-CN" href="${origin}/zh/"><link rel="alternate" hreflang="x-default" href="${origin}/">
<meta property="og:type" content="website"><meta property="og:site_name" content="Sideword"><meta property="og:title" content="${t.title}"><meta property="og:description" content="${escape(t.description)}"><meta property="og:url" content="${origin + t.path}"><meta property="og:image" content="${origin}/assets/social.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:locale" content="${key === "zh" ? "zh_CN" : "en_US"}"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/svg+xml" href="/assets/mark.svg"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png"><link rel="preload" href="/assets/manrope.woff2" as="font" type="font/woff2" crossorigin><link rel="stylesheet" href="/assets/styles.css">
<script type="application/ld+json">${JSON.stringify(schema)}</script><script type="module" src="/assets/app.js"></script></head>
<body><a class="skip" href="#main">${t.skip}</a>
<header class="wrap"><a class="brand" href="${t.path}" aria-label="Sideword">${mark}<span>sideword</span></a><nav aria-label="${key === "zh" ? "主导航" : "Main navigation"}"><a href="#learn">${t.nav[0]}</a><a href="#install">${t.nav[1]}</a><a href="${repo}">GitHub</a><a class="language" href="${t.switchPath}" lang="${key === "zh" ? "en" : "zh-CN"}" hreflang="${key === "zh" ? "en" : "zh-CN"}">${t.switch}</a><button class="theme" aria-label="${t.theme}" title="${t.theme}" aria-pressed="false">◐</button></nav></header>
<main id="main"><section class="hero wrap"><div class="hero-copy"><p class="intro">${t.intro}</p><h1>${t.hero.replace("\n", "<br>")}</h1><p class="lead">${t.lead}</p><div class="actions"><a class="button primary" href="#install">${t.cta}</a><a class="text-link" href="${repo}">${t.source}</a></div><p class="availability">${t.availability}</p></div>
<div class="demo-area"><div class="demo-heading"><span>${t.demo}</span><span class="demo-count">3 ${t.left}</span></div><div class="terminal"><div class="terminal-top"><span aria-hidden="true" class="window-dots">● ● ●</span><span>sideword --quiet</span><span aria-hidden="true">⌘</span></div><div class="word-tabs" aria-label="${t.select}">${words.map((w, i) => `<button data-word="${i}" aria-pressed="${i === 0}">${w.name}</button>`).join("")}</div><div class="word-content"><p class="word">${words[0].name}</p><p class="ipa" lang="en">/${words[0].ipa}/</p><p class="meaning" lang="zh-CN">${words[0].meaning}</p><div class="example"><p lang="en">${words[0].example}</p><p class="translation" lang="zh-CN">${words[0].translation}</p></div></div><div class="demo-controls"><button class="remember">${t.remember}<span aria-hidden="true"> ↵</span></button><button class="reset">${t.reset}</button></div><p class="demo-status" role="status" aria-live="polite"></p></div><p class="demo-note">${t.demoNote}</p><noscript><p>${key === "zh" ? "启用 JavaScript 可切换演示单词。安装与所有介绍仍可正常阅读。" : "Enable JavaScript to interact with this demo. Installation and all content remain available."}</p></noscript></div></section>
<section id="learn" class="learning wrap"><div><h2>${t.loopTitle.replace("\n", "<br>")}</h2><p class="section-lead">${t.loopLead}</p></div><ol class="steps">${t.steps.map(([title, body]) => `<li><h3>${title}</h3><p>${body}</p></li>`).join("")}</ol><div class="review-line"><ol>${t.timeline.map((item) => `<li><span aria-hidden="true"></span>${item}</li>`).join("")}</ol><p>${t.timelineNote}</p></div></section>
<section class="details wrap" aria-label="${key === "zh" ? "使用体验" : "Everyday use"}">${t.details.map(([title, body]) => `<div><h3>${title}</h3><p>${body}</p></div>`).join("")}</section>
<section id="install" class="install"><div class="wrap install-grid"><div><h2>${t.installTitle.replace("\n", "<br>")}</h2><p class="section-lead">${t.installLead}</p><p><a class="download" href="${release}">${t.download}</a></p><p class="small">${t.downloadNote}</p></div><div><div class="command-box"><div class="command-heading"><span>Terminal</span><button class="copy">${t.copy}</button></div><code class="install-command">${escape(command)}</code><p class="copy-status" role="status" aria-live="polite"></p></div><p>${t.start} <code>sideword</code>.<br>${t.startNow} <code>~/.local/bin/sideword</code>.</p><aside class="preview"><h3>${t.preview}</h3><p>${t.previewText}</p><a href="${repo}/blob/main/docs/install-macos.md">${t.installGuide}</a></aside><details class="source-install"><summary>${t.other}</summary><p>${t.otherText} <a href="${repo}#start-here">README</a></p></details></div></div></section>
<section class="faq wrap"><h2>${t.faqTitle}</h2><div>${t.faqs.map(([q, a]) => `<details><summary>${q}</summary><p>${a}</p></details>`).join("")}</div></section></main>
<footer class="wrap"><div><a class="brand" href="${t.path}">${mark}<span>sideword</span></a><p>${t.footer}</p></div><div class="footer-links"><a href="${repo}">GitHub</a><a href="${repo}/blob/main/docs/guide.md">${t.guide}</a><a href="${repo}/issues">${t.issues}</a><a href="${repo}/blob/main/LICENSE">MIT</a></div></footer>
<script id="demo-data" type="application/json">${JSON.stringify({ words, labels: t, command }).replaceAll("<", "\\u003c")}</script></body></html>`;
  const dir = key === "en" ? "dist" : "dist/zh";
  await mkdir(dir, { recursive: true });
  await writeFile(`${dir}/index.html`, html);
}
await writeFile(
  "dist/robots.txt",
  `User-agent: *\nAllow: /\nSitemap: ${origin}/sitemap.xml\n`,
);
await writeFile(
  "dist/sitemap.xml",
  `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${["/", "/zh/"].map((p) => `<url><loc>${origin + p}</loc></url>`).join("")}</urlset>`,
);
await writeFile(
  "dist/404.html",
  '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Page not found — Sideword</title><h1>Page not found</h1><p><a href="/">Sideword home</a> · <a href="/zh/">中文首页</a></p></html>',
);
console.log("Built English and Chinese pages, sitemap and robots.txt.");
