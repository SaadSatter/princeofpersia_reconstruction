"""GATE-T14 QA: the JS-Python contract of web/main.js, run in Node with stubs.

The sandbox has no Pyodide or Phaser, so main.js is run in a vm with a fake
`loadPyodide` whose game replays payloads recorded from the real `WebGame`, a
fake `Phaser` that records every call, and a fake DOM. This checks that every
field main.js reads exists in the payload, that no call gets NaN or undefined,
that every texture it draws was loaded from the manifest, and that keys reach
`press` as physical key names. It does not test the real libraries.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node not installed")

HARNESS = r"""
"use strict";
const fs = require("fs"), vm = require("vm");
const [,, webDir, dataPath] = process.argv;
const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));
const SMKeys = require(webDir + "/keys.js");
const fail = (m) => { console.error("FAIL: " + m); process.exit(1); };

function run(label, search, payloads) {
  return new Promise((resolve) => {
    const listeners = {};
    const els = {};
    const el = (id) => els[id] || (els[id] = { id, textContent: "", dataset: {} });
    const calls = { press: [], rematch: 0, ticks: 0, images: [], rects: [], lines: [], loaded: [] };
    let cursor = 0;
    const chain = (rec) => new Proxy(rec, {
      get(t, p) {
        if (p in t) return t[p];
        return (...a) => { (t.calls = t.calls || []).push([p, a]); check(label, p, a); return t.self; };
      },
    });
    function check(lbl, name, args) {
      args.forEach((a) => {
        if (typeof a === "number" && !Number.isFinite(a)) fail(`${lbl}: ${name} got non-finite ${a}`);
        if (a === undefined) fail(`${lbl}: ${name} got undefined`);
      });
    }
    const textures = {};
    const scene = {
      load: { image(key, url) { calls.loaded.push(key); check(label, "load.image", [key, url]); } },
      textures: { get(sheet) {
        if (!calls.loaded.includes(sheet)) fail(`${label}: texture ${sheet} drawn but never loaded`);
        const frames = textures[sheet] = textures[sheet] || new Set();
        return { has: (k) => frames.has(k), add: (k, ...r) => { check(label, "tex.add", r); frames.add(k); } };
      } },
      add: {
        image(x, y, key) { const o = {}; o.self = chainWith(o, "img"); o.key = key; return o.self; },
        rectangle() { const o = {}; o.self = chainWith(o, "rect"); return o.self; },
        line() { const o = {}; o.self = chainWith(o, "line"); return o.self; },
      },
    };
    function chainWith(o, kind) {
      const p = new Proxy(o, {
        get(t, name) {
          if (name === "self") return p;
          if (name in t) return t[name];
          return (...a) => { check(label, kind + "." + String(name), a); (t.log = t.log || {})[name] = a; return p; };
        },
      });
      (calls[kind === "img" ? "images" : kind === "rect" ? "rects" : "lines"]).push(o);
      return p;
    }
    const game = {
      press(k) { calls.press.push(JSON.parse(JSON.stringify(k))); },
      tick_json() { calls.ticks += 1; calls.last = payloads[Math.min(cursor++, payloads.length - 1)]; return JSON.stringify(calls.last); },
      rematch() { calls.rematch += 1; },
    };
    const make = Object.assign(() => game, { destroy() {} });
    const sandbox = {
      SMKeys, console,
      window: null,
      document: { getElementById: el },
      fetch: async (u) => ({ json: async () => data.manifest, arrayBuffer: async () => new ArrayBuffer(1) }),
      loadPyodide: async () => ({
        unpackArchive() {}, runPython(src) { return src.includes("def make") ? make : undefined; },
        toPy: (o) => Object.assign({ destroy() {} }, o),
      }),
      Phaser: { AUTO: 0, Game: function (cfg) {
        calls.config = cfg;
        setTimeout(() => {
          cfg.scene.preload.call(scene);
          cfg.scene.create.call(scene);
          for (let i = 0; i < 40; i++) cfg.scene.update.call(scene, i * 84, 84);
          resolve({ calls, els, listeners, cfg });
        }, 0);
      } },
    };
    sandbox.window = { location: { search }, addEventListener: (n, f) => { (listeners[n] = listeners[n] || []).push(f); },
                       SM_CONFIG: { pyodideUrl: "x/" } };
    sandbox.window.window = sandbox.window;
    vm.runInNewContext(fs.readFileSync(webDir + "/main.js", "utf8"), sandbox);
  });
}

(async () => {
  for (const [label, search, key] of [["ai", "?mode=ai", "ai"], ["local", "?mode=local", "local"]]) {
    const r = await run(label, search, data[key]);
    const st = r.els.status;
    if (!st || st.dataset.state !== "ready") fail(`${label}: status ${st && st.textContent}`);
    if (r.calls.images.length === 0 || r.calls.rects.length === 0) fail(`${label}: nothing drawn`);
    if (r.calls.ticks < 20) fail(`${label}: clock ran ${r.calls.ticks} ticks in 40 updates`);
    if (!r.els.hud.textContent.includes("hearts")) fail(`${label}: hud text ${r.els.hud.textContent}`);
    const w = r.cfg.width, h = r.cfg.height;
    if (label === "ai" && (w !== 320 || h !== 200)) fail(`${label}: canvas ${w}x${h}`);
    if (label === "local" && w !== 644) fail(`${label}: canvas width ${w}`);
    if (label === "local" && !r.els.label.textContent.includes("Local test mode")) fail("local label missing");
    const last = r.calls.last;
    if (label === "ai" && r.els.rival.textContent !== last.rival) fail("rival label is not the payload's");
    if (label === "ai" && r.els.hud.textContent !== last.hud.text) fail("hud text is not the payload's");
    if (label === "local" && !r.els.hud.textContent.includes(last.seats.B.hud.text)) fail("local hud lacks seat B");
    // keys: D down -> press gets {d: true}; R -> rematch
    const down = r.listeners.keydown[0], up = r.listeners.keyup[0];
    down({ code: "KeyD", preventDefault() {}, repeat: false });
    down({ code: "ShiftLeft", preventDefault() {}, repeat: false });
    for (let i = 0; i < 3; i++) await new Promise((res) => setTimeout(res, 0));
    r.cfg.scene.update.call({}, 0, 0);
    down({ code: "KeyR", preventDefault() {}, repeat: false });
    if (r.calls.rematch !== 1) fail(`${label}: R did not call rematch`);
    up({ code: "KeyD", preventDefault() {} });
  }
  // terminal payload text
  const r = await run("terminal", "?mode=ai", [data.terminal]);
  if (!/You (win|lose)|Draw/.test(r.els.outcome.textContent)) fail("terminal text: " + r.els.outcome.textContent);
  if (!r.els.outcome.textContent.includes("rematch")) fail("rematch hint missing");
  console.log("ok");
})();
"""


@pytest.fixture(scope="module")
def recorded(tmp_path_factory):
    from tools.web import build as webbuild
    from web.bridge import RandomRival, WebGame
    out = tmp_path_factory.mktemp("dist")
    manifest = webbuild.build(out)

    def stream(game, script, n=70):
        ps = []
        for i in range(n):
            game.press(script(i))
            ps.append(game.tick())
        return ps

    def keys_a(i):
        return {"d": i % 20 < 12, "lshift": i % 30 > 25, "f": i % 17 == 0, "w": i % 23 == 0}

    def keys_ab(i):
        k = keys_a(i)
        k.update({"left": i % 14 < 5, "up": i % 19 == 0, ".": i % 11 == 0})
        return k

    ai = stream(WebGame(seed=1, rival=RandomRival(1)), keys_a)
    local = stream(WebGame(mode="local_two_players", seed=2), keys_ab)
    g = WebGame(seed=1, rival=RandomRival(1))
    while g.episode.outcome()["status"] != "terminal":
        terminal = g.tick()
    return {"manifest": manifest, "ai": ai, "local": local, "terminal": terminal}


def test_main_js_reads_only_what_the_payload_has(recorded, tmp_path):
    (tmp_path / "data.json").write_text(json.dumps(recorded))
    h = tmp_path / "harness.cjs"
    h.write_text(HARNESS)
    out = subprocess.run([NODE, str(h), str(ROOT / "web"), str(tmp_path / "data.json")],
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stdout + out.stderr
    assert out.stdout.strip() == "ok"
