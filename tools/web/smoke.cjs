// Browser smoke test for the built page (T14), run by .github/workflows/web-smoke.yml.
//   NODE_PATH=<dir with playwright> node tools/web/smoke.cjs http://localhost:8000/ shot.png
// Loads the page in Chromium, picks a mode on the chooser (T22-fix1, #92), waits for "ready" (Pyodide and Phaser loaded,
// first frame drawn), holds D (seat A runs right) for 2 s, and checks that
// the frame counter advanced, that the console logged no errors, and that the
// key reached the engine: the human seat's position (window.__smLast, the
// page's test-only readout) changed and the canvas picture differs before and
// after. A page whose key handler is dead fails here (QA-T14-1).
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
  // Decision #92: the page opens on the mode chooser. Check it lists the three modes, then pick
  // the baseline: the click reloads the page with ?play=baseline and the game starts.
  await page.waitForSelector("#modes a.mode", { timeout: 60000 });
  const modeCount = await page.locator("#modes a.mode").count();
  if (modeCount !== 3) {
    errors.push(`the mode chooser lists ${modeCount} modes, expected 3`);
  }
  await Promise.all([
    page.waitForURL(/[?&]play=baseline/),
    page.click('#modes a.mode[href="?play=baseline"]'),
  ]);
  await page.waitForSelector('#status[data-state="ready"], #status[data-state="error"]',
    { timeout: 180000 });
  const state = await page.getAttribute("#status", "data-state");
  if (state !== "ready") {
    errors.push("status: " + (await page.textContent("#status")));
  }
  const before = Number(await page.textContent("#frames"));
  const readout = () => page.evaluate(() => window.__smLast || null);
  const canvas = page.locator("#game canvas");
  const posBefore = await readout();
  const picBefore = await canvas.screenshot();
  await page.click("#game");
  await page.keyboard.down("KeyD");
  await page.waitForTimeout(2000);
  const posHeld = await readout();
  const picAfter = await canvas.screenshot();
  await page.keyboard.up("KeyD");
  const after = Number(await page.textContent("#frames"));
  await page.screenshot({ path: shot, fullPage: true });
  await browser.close();
  console.log(`frames ${before} -> ${after}; screenshot ${shot}`);
  if (!(after > before + 12)) {
    errors.push(`frame counter did not advance enough: ${before} -> ${after}`);
  }
  const where = (p) => (p ? `${p.me.room}/${p.me.row}/${p.me.col}` : "none");
  console.log(`position ${where(posBefore)} -> ${where(posHeld)}`);
  if (!posBefore || !posHeld) {
    errors.push("position readout window.__smLast is missing");
  } else if (where(posBefore) === where(posHeld)) {
    errors.push(`position did not change after holding D: ${where(posBefore)}`);
  }
  if (Buffer.compare(picBefore, picAfter) === 0) {
    errors.push("canvas pixels did not change after holding D");
  }
  if (errors.length) {
    console.error(errors.join("\n"));
    process.exit(1);
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
