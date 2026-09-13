import fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const root = path.dirname(new URL(import.meta.url).pathname);
const qa = path.join(root, "qa");
fs.mkdirSync(qa, { recursive: true });

const browser = await chromium.launch();
const results = [];
try {
  for (const width of [1440, 390]) {
    for (const theme of ["light", "dark"]) {
      const page = await browser.newPage({ viewport: { width, height: 1100 }, colorScheme: theme });
      const errors = [];
      page.on("pageerror", (error) => errors.push(error.message));
      page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });
      await page.goto("http://127.0.0.1:61342/");
      await page.locator("h1").first().waitFor();
      await page.waitForTimeout(1400);
      assert.equal(errors.length, 0, errors.join("\n"));
      assert.equal(await page.locator(".recharts-wrapper").count(), 4);
      assert.equal(await page.locator("svg.recharts-surface").count(), 4);
      const sizes = await page.locator("svg.recharts-surface").evaluateAll((nodes) => nodes.map((node) => {
        const rect = node.getBoundingClientRect();
        return { width: rect.width, height: rect.height, marks: node.querySelectorAll("path,rect,circle").length };
      }));
      assert(sizes.every((size) => size.width > 100 && size.height > 100 && size.marks > 0), JSON.stringify(sizes));
      const body = await page.locator("body").innerText();
      for (const token of ["87.40%", "+16.88%", "451.00万", "3 Lucky Chong Tian Pao", "提现增长是TC升高的直接原因", "161款游戏完整汇总"]) {
        assert(body.includes(token), `missing ${token}`);
      }
      assert(!body.includes("Creating report"));
      assert(!body.includes("NaN"));
      const pageOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
      assert(!pageOverflow, `page overflow at ${width}`);
      const tableOverflowContained = await page.locator('[data-component-id="game-table"] .table-wrap').evaluate((node) => node.scrollWidth >= node.clientWidth);
      assert(tableOverflowContained);
      const screenshot = path.join(qa, `report-${width}-${theme}.png`);
      await page.screenshot({ path: screenshot, fullPage: true });
      results.push({ width, theme, screenshot, sizes, pageOverflow, tableOverflowContained });
      await page.close();
    }
  }
} finally {
  await browser.close();
}
const receipt = { status: "passed", checkedAt: new Date().toISOString(), views: results };
fs.writeFileSync(path.join(qa, "visual-verification.json"), JSON.stringify(receipt, null, 2));
console.log(JSON.stringify({ status: "passed", views: results.length, charts: 4 }));
