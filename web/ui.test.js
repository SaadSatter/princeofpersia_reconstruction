// Node tests for web/ui.js (run by tests/test_online_web.py). No DOM needed.
"use strict";
const assert = require("assert");
const U = require("./ui.js");

assert.strictEqual(U.rematchView({ status: "ongoing" }, "none").visible, false);
assert.strictEqual(U.rematchView(null, "none").visible, false);
const ended = U.rematchView({ status: "terminal" }, "none");
assert.strictEqual(ended.visible, true);
assert.strictEqual(ended.label, "Rematch");
assert.ok(/Enter/.test(ended.hint));
const waiting = U.rematchView({ status: "terminal" }, "waiting");
assert.strictEqual(waiting.disabled, true);
assert.ok(waiting.label.startsWith("Waiting for rival"));
assert.strictEqual(U.rematchView({ status: "terminal" }, "rival_wants").note, "Rival wants a rematch");

// A minimal fake document: press() only fires while the button is showing.
function el() {
  return { children: [], className: "", textContent: "", appendChild(c) { this.children.push(c); return c; },
    addEventListener() {}, set disabled(v) { this._d = v; }, get disabled() { return this._d; } };
}
const doc = { createElement: el, head: el() };
let presses = 0;
const b = U.createRematch(doc, el(), function () { presses += 1; });
assert.strictEqual(b.press(), false);
b.update(ended);
assert.strictEqual(b.press(), true);
b.update(waiting);
assert.strictEqual(b.press(), false);
assert.strictEqual(presses, 1);
console.log("ui.test.js ok");
