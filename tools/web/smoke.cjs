// Browser smoke test for the built page (T14), run by .github/workflows/web-smoke.yml.
//   NODE_PATH=<dir with playwright> node tools/web/smoke.cjs http://localhost:8000/ shot.png
// Loads the page in Chromium, waits for "ready" (Pyodide and Phaser loaded,
// first frame drawn), holds D (seat A runs right) for 2 s, and checks that
// the frame counter advanced and that the console logged no errors.
"use strict";
const { chromium } = require("playwright");

async function main() {
  const url = process.argv[2] || "http://localhost:8000/";
  const shot = process.argv[3] || "web-smoke.png";
  const errors = [];
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on("console", (m) => { if (m.type() === "error") errors.push("console: " + m.text()); });
  page.on("pageerror", (e) => errors.push("page: " + e.message));
  await page.goto(url);
  await page.waitForSelector('#status[data-state="ready"], #status[data-state="error"]',
    { timeout: 180000 });
  const state = await page.getAttribute("#status", "data-state");
  if (state !== "ready") {
    errors.push("status: " + (await page.textContent("#status")));
  }
  const before = Number(await page.textContent("#frames"));
  await page.click("#game");
  await page.keyboard.down("KeyD");
  await page.waitForTimeout(2000);
  await page.keyboard.up("KeyD");
  const after = Number(await page.textContent("#frames"));
  await page.screenshot({ path: shot, fullPage: true });
  await browser.close();
  console.log(`frames ${before} -> ${after}; screenshot ${shot}`);
  if (!(after > before + 12)) {
    errors.push(`frame counter did not advance enough: ${before} -> ${after}`);
  }
  if (errors.length) {
    console.error(errors.join("\n"));
    process.exit(1);
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
