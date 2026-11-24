// Node unit tests for web/keys.js (run: node web/keys.test.js; tests/test_web_js.py runs it).
"use strict";
const assert = require("node:assert/strict");
const K = require("./keys.js");

let passed = 0;
function test(name, fn) {
  fn();
  passed += 1;
}

test("physical keys map to play.py names", () => {
  assert.equal(K.keyName("KeyA"), "a");
  assert.equal(K.keyName("ArrowLeft"), "left");
  assert.equal(K.keyName("Period"), ".");
  assert.equal(K.keyName("Slash"), "/");
  assert.equal(K.keyName("Quote"), "'");
  assert.equal(K.keyName("ShiftLeft"), "lshift");
  assert.equal(K.keyName("ShiftRight"), "rshift");
  assert.equal(K.keyName("KeyZ"), null);
  assert.equal(K.keyName("toString"), null);
});

test("applyKey holds and releases without mutating", () => {
  const a = {};
  const b = K.applyKey(a, "KeyD", true);
  assert.deepEqual(a, {});
  assert.deepEqual(b, { d: true });
  const c = K.applyKey(b, "ShiftLeft", true);
  assert.deepEqual(c, { d: true, lshift: true });
  assert.deepEqual(K.applyKey(c, "KeyD", false), { lshift: true });
  assert.deepEqual(K.applyKey(c, "KeyZ", true), c);
  assert.deepEqual(K.applyKey(c, "KeyR", true), c); // R is the rematch key, not held
});

test("game keys suppress browser defaults; others do not", () => {
  assert.equal(K.shouldPrevent("ArrowUp"), true);
  assert.equal(K.shouldPrevent("Quote"), true);
  assert.equal(K.shouldPrevent("F5"), false);
});

test("stepClock runs 12 ticks per second and caps catch-up", () => {
  let r = K.stepClock(0, 1000, 12, 100);
  assert.equal(r.steps, 12);
  r = K.stepClock(0, 50, 12, 3);
  assert.equal(r.steps, 0);
  assert.ok(Math.abs(r.acc - 50) < 1e-9);
  r = K.stepClock(r.acc, 40, 12, 3);
  assert.equal(r.steps, 1);
  r = K.stepClock(0, 10000, 12, 3);
  assert.deepEqual(r, { steps: 3, acc: 0 });
  r = K.stepClock(10, -5, 12, 3);
  assert.equal(r.steps, 0);
});

test("parseOptions defaults to human vs AI as seat A", () => {
  assert.deepEqual(K.parseOptions(""), { mode: "human_vs_ai", seat: "A", seed: 0, rival: "idle" });
  assert.deepEqual(K.parseOptions("?mode=local&seed=7"),
    { mode: "local_two_players", seat: "A", seed: 7, rival: "idle" });
  assert.deepEqual(K.parseOptions("?seat=B&seed=-3&rival=random"),
    { mode: "human_vs_ai", seat: "B", seed: 0, rival: "random" });
  assert.equal(K.parseOptions("?seed=abc").seed, 0);
});

console.log(`keys.test.js: ${passed} passed`);
