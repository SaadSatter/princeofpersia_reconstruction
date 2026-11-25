// The Rematch button (T13, decision #41), shared by the hosted page, the local
// page and the online page. No game rules here: it shows a button when the
// payload says the duel is over, and tells the page when it is pressed.
// Drawn from the generated dungeon art (art/tiles.png, granite) and the page
// palette, with hard pixel edges: no default browser button, no smoothing.
// Loaded by index.html and online.html as window.SMUi and by Node (ui.test.js).
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.SMUi = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const HINT = "R or Enter";

  // What the button shows. `outcome` is the payload's outcome; `rematch` is
  // "none", "waiting" (this player pressed) or "rival_wants" (the other did).
  function rematchView(outcome, rematch) {
    if (!outcome || outcome.status !== "terminal") {
      return { visible: false, label: "", hint: "", disabled: false, note: "" };
    }
    if (rematch === "waiting") {
      return { visible: true, label: "Waiting for rival…", hint: "", disabled: true, note: "" };
    }
    return {
      visible: true,
      label: "Rematch",
      hint: HINT,
      disabled: false,
      note: rematch === "rival_wants" ? "Rival wants a rematch" : "",
    };
  }

  // Hard-edged and stepped, so nothing looks like a stock widget.
  const CSS = [
    ".sm-rematch { display: none; margin: 12px 0; text-align: center; }",
    ".sm-rematch.sm-on { display: block; }",
    ".sm-rematch-note { color: #f0c040; font: bold 14px monospace; margin-bottom: 8px;",
    "  text-shadow: 2px 2px 0 #000; -webkit-font-smoothing: none; font-smooth: never; }",
    ".sm-rematch-btn { -webkit-appearance: none; appearance: none; cursor: pointer;",
    "  min-width: 224px; padding: 14px 24px 12px; border: 0; border-radius: 0;",
    "  background-color: #3a4256; background-image: url(art/tiles.png);",
    "  background-size: 256px 256px; background-position: -40px -120px;",
    "  image-rendering: pixelated; color: #f0c040; font: bold 20px monospace;",
    "  letter-spacing: 2px; text-transform: uppercase; text-shadow: 2px 2px 0 #000;",
    "  -webkit-font-smoothing: none; font-smooth: never;",
    "  box-shadow: 4px 0 0 #0d0e12, -4px 0 0 #0d0e12, 0 4px 0 #0d0e12, 0 -4px 0 #0d0e12,",
    "    inset 4px 4px 0 #8a93a8, inset -4px -4px 0 #1a1d28; }",
    ".sm-rematch-btn:hover:not(:disabled), .sm-rematch-btn:focus-visible {",
    "  color: #fff; outline: 4px solid #f0c040; outline-offset: 4px; }",
    ".sm-rematch-btn:active:not(:disabled) { transform: translate(2px, 2px); }",
    ".sm-rematch-btn:disabled { cursor: default; color: #9a968c; }",
    ".sm-rematch-hint { display: block; font-size: 11px; color: #d8d4c8; letter-spacing: 1px;",
    "  margin-top: 4px; text-shadow: 1px 1px 0 #000; }",
  ].join("\n");

  // Create the button inside `parent`. Returns { update(view), press() }.
  function createRematch(doc, parent, onPress) {
    const style = doc.createElement("style");
    style.textContent = CSS;
    doc.head.appendChild(style);
    const box = doc.createElement("div");
    box.className = "sm-rematch";
    const note = doc.createElement("div");
    note.className = "sm-rematch-note";
    const btn = doc.createElement("button");
    btn.type = "button";
    btn.className = "sm-rematch-btn";
    btn.addEventListener("click", function () { onPress(); });
    box.appendChild(note);
    box.appendChild(btn);
    parent.appendChild(box);
    let current = rematchView(null, "none");
    function update(view) {
      current = view;
      box.className = "sm-rematch" + (view.visible ? " sm-on" : "");
      note.textContent = view.note;
      btn.disabled = view.disabled;
      btn.textContent = view.label;
      if (view.hint) {
        const h = doc.createElement("span");
        h.className = "sm-rematch-hint";
        h.textContent = "(" + view.hint + ")";
        btn.appendChild(h);
      }
    }
    return {
      update: update,
      // Keyboard route (R or Enter) when the button is showing and enabled.
      press: function () {
        if (current.visible && !current.disabled) { onPress(); return true; }
        return false;
      },
    };
  }

  return Object.freeze({ rematchView: rematchView, createRematch: createRematch, CSS: CSS });
});
