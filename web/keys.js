// Pure helpers for the Shadow Masque page (T14): no DOM, no Phaser, no game rules.
// Loaded by index.html as window.SMKeys and by Node (web/keys.test.js) as a module.
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.SMKeys = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // KeyboardEvent.code (a physical key) -> the key name play.py --versus uses
  // (web/bridge.py KEY_MAP maps names to each seat's controls).
  const CODE_TO_KEY = Object.freeze({
    KeyA: "a", KeyD: "d", KeyW: "w", KeyS: "s", KeyF: "f", KeyG: "g", KeyT: "t",
    ShiftLeft: "lshift",
    ArrowLeft: "left", ArrowRight: "right", ArrowUp: "up", ArrowDown: "down",
    Period: ".", Slash: "/", Quote: "'", ShiftRight: "rshift",
    KeyR: "r",
  });

  function keyName(code) {
    return Object.prototype.hasOwnProperty.call(CODE_TO_KEY, code) ? CODE_TO_KEY[code] : null;
  }

  // Keys whose browser default (scrolling, quick find) must not fire while playing.
  function shouldPrevent(code) {
    return keyName(code) !== null;
  }

  // A new held-key object after one keydown/keyup; unknown keys change nothing.
  function applyKey(held, code, down) {
    const name = keyName(code);
    const out = Object.assign({}, held);
    if (name === null || name === "r") {
      return out;
    }
    if (down) {
      out[name] = true;
    } else {
      delete out[name];
    }
    return out;
  }

  // Fixed-step clock: how many game ticks are due after dtMs, never more than
  // maxSteps at once (a background tab does not fast-forward the duel).
  function stepClock(accMs, dtMs, ticksPerSecond, maxSteps) {
    const step = 1000 / ticksPerSecond;
    let acc = accMs + Math.max(0, dtMs);
    let steps = Math.floor(acc / step);
    acc -= steps * step;
    if (steps > maxSteps) {
      steps = maxSteps;
      acc = 0;
    }
    return { steps: steps, acc: acc };
  }

  // Page options from the query string: ?mode=local|ai&seat=A|B&seed=N&rival=idle|random
  function parseOptions(search) {
    const q = new URLSearchParams(search || "");
    const mode = q.get("mode") === "local" ? "local_two_players" : "human_vs_ai";
    const seat = q.get("seat") === "B" ? "B" : "A";
    const n = parseInt(q.get("seed") || "0", 10);
    const seed = Number.isFinite(n) && n >= 0 ? n : 0;
    const rival = q.get("rival") === "random" ? "random" : "idle";
    return { mode: mode, seat: seat, seed: seed, rival: rival };
  }

  return Object.freeze({
    CODE_TO_KEY: CODE_TO_KEY,
    keyName: keyName,
    shouldPrevent: shouldPrevent,
    applyKey: applyKey,
    stepClock: stepClock,
    parseOptions: parseOptions,
  });
});
