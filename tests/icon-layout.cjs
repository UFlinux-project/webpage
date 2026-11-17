"use strict";
// Optional browser regression. Serve dist first; Playwright is a QA dependency only.
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({
    ...(process.env.TEST_CHROMIUM ? { executablePath: process.env.TEST_CHROMIUM } : {}),
    args: ["--no-sandbox"]
  });
  try {
    for (const width of [320, 1280]) {
      for (const route of ["/", "/downloads/", "/downloads/choose/", "/cs/"]) {
        const page = await browser.newPage({ viewport: { width, height: 1000 } });
        // Keep the unrelated Ubuntu swap out of this icon-specific measurement.
        await page.route("https://fonts.googleapis.com/**", request => request.abort());
        let allowCSS, allowFonts;
        const cssGate = new Promise(resolve => { allowCSS = resolve; });
        const fontGate = new Promise(resolve => { allowFonts = resolve; });
        await page.route("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/**", async request => {
          await (request.request().url().includes("/webfonts/") ? fontGate : cssGate);
          await request.continue();
        });
        const measure = () => page.evaluate(() => Array.from(document.querySelectorAll(
          ".site-icon,.button,.option,.download-row,.language-select,.header,.release-pill"
        ), element => {
          const box = element.getBoundingClientRect();
          return [box.x, box.y, box.width, box.height];
        }));
        await page.goto((process.env.SITE_URL || "http://localhost:8000") + route, { waitUntil: "domcontentloaded" });
        const initial = await measure();
        allowCSS();
        await page.waitForFunction(() => Array.from(document.querySelectorAll("link[id^=fa-]")).every(link => link.media === "all"));
        assert.deepEqual(await measure(), initial, `Icon CSS moved layout: ${width} ${route}`);
        allowFonts();
        await page.evaluate(() => document.fonts.ready);
        assert.deepEqual(await measure(), initial, `Icon font moved layout: ${width} ${route}`);
        console.log(`Stable before CSS, after CSS, and after fonts: ${width} ${route}`);
        await page.close();
      }
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
