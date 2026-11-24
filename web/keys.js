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

  // Page options from the query string:
  //   ?mode=local|ai&seat=A|B&seed=N&rival=baseline|idle|random&label=neutral
  // rival defaults to the scripted baseline; label=neutral shows the rival as
  // just "Rival" (blind playtest sessions).
  function parseOptions(search) {
    const q = new URLSearchParams(search || "");
    const mode = q.get("mode") === "local" ? "local_two_players" : "human_vs_ai";
    const seat = q.get("seat") === "B" ? "B" : "A";
    const n = parseInt(q.get("seed") || "0", 10);
    const seed = Number.isFinite(n) && n >= 0 ? n : 0;
    const r = q.get("rival");
    const rival = r === "random" || r === "idle" ? r : "baseline";
    return { mode: mode, seat: seat, seed: seed, rival: rival, neutral: q.get("label") === "neutral" };
  }

  // The key hints for the seat actually played (text only; the keys themselves
  // are mapped by KEY_MAP in web/bridge.py).
  const HINT_A = "A/D run (Shift: careful step), W up / jump, S down, F attack " +
    "(with W: throw, with S: sweep; in the air: dive kick), G draw or sheathe, T take a uniform.";
  const HINT_B = "Arrow keys move (right Shift: careful step; up: jump), . attack " +
    "(with up: throw, with down: sweep; in the air: dive kick), / draw or sheathe, ' take a uniform.";

  function keyHints(mode, seat) {
    if (mode === "local_two_players") {
      return "Seat A: " + HINT_A + " Seat B: " + HINT_B + " R: rematch.";
    }
    return "You are seat " + seat + ". " + (seat === "B" ? HINT_B : HINT_A) + " R: rematch.";
  }

  return Object.freeze({
    keyHints: keyHints,
    CODE_TO_KEY: CODE_TO_KEY,
    keyName: keyName,
    shouldPrevent: shouldPrevent,
    applyKey: applyKey,
    stepClock: stepClock,
    parseOptions: parseOptions,
  });
});
