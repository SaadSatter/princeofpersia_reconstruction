// Shadow Masque web page (T14): load Pyodide, run web/bridge.py, blit its draw list with Phaser.
// No game logic here: keys go to the bridge as physical key names, and every
// picture, number and message drawn comes from the bridge's payload.
/* global loadPyodide, Phaser, SMKeys, SMUi */
"use strict";

(function () {
  const TICKS_PER_SECOND = 12;
  const MAX_CATCH_UP = 3;
  const PANEL_W = 320;
  const PANEL_H = 200;
  const GAP = 4;
  const ZOOM = 3;

  const opts = SMKeys.parseOptions(window.location.search);
  const statusEl = document.getElementById("status");
  const framesEl = document.getElementById("frames");
  const hudEl = document.getElementById("hud");
  const outcomeEl = document.getElementById("outcome");
  const labelEl = document.getElementById("label");
  const rivalEl = document.getElementById("rival");
  const buildEl = document.getElementById("build");
  const keysEl = document.getElementById("keys");

  let held = {};
  let frames = 0;
  let game = null; // the Python WebGame (a Pyodide proxy)
  let pyodide = null;
  let payload = null;
  let acc = 0;

  // The shared Rematch button (web/ui.js, decision #41): one press restarts here,
  // with the same seed (#25). Absent (null) where ui.js is not loaded.
  const rematchButton = (typeof SMUi !== "undefined" && document.body)
    ? SMUi.createRematch(document, document.body, function () {
      game.rematch();
      frames = 0;
    }) : null;

  function setStatus(text, state) {
    statusEl.textContent = text;
    statusEl.dataset.state = state;
  }

  window.addEventListener("error", function (e) {
    setStatus("error: " + e.message, "error");
  });
  window.addEventListener("unhandledrejection", function (e) {
    setStatus("error: " + e.reason, "error");
    console.error(e.reason);
  });

  window.addEventListener("keydown", function (e) {
    if (SMKeys.shouldPrevent(e.code)) {
      e.preventDefault();
    }
    if (SMKeys.keyName(e.code) === "r" && !e.repeat && game !== null) {
      game.rematch();
      frames = 0;
      return;
    }
    if (e.code === "Enter" && !e.repeat && rematchButton !== null && rematchButton.press()) {
      return;
    }
    held = SMKeys.applyKey(held, e.code, true);
  });
  window.addEventListener("keyup", function (e) {
    held = SMKeys.applyKey(held, e.code, false);
  });
  window.addEventListener("blur", function () {
    held = {};
  });

  async function startPython() {
    pyodide = await loadPyodide({ indexURL: window.SM_CONFIG.pyodideUrl });
    const zip = await (await fetch("game.zip")).arrayBuffer();
    pyodide.unpackArchive(zip, "zip", { extractDir: "/home/pyodide/game" });
    pyodide.runPython("import sys\nsys.path.insert(0, '/home/pyodide/game')");
    const make = pyodide.runPython(
      "from web.bridge import make_game\n" +
      "def make(mode, seat, seed, rival, neutral, honest):\n" +
      "    return make_game(mode, seat, seed, rival, neutral, honest)\n" +
      "make");
    game = make(opts.mode, opts.seat, opts.seed, opts.rival, opts.neutral, true);   // honest names (#88)
    make.destroy();
  }

  function stepGame() {
    const keys = pyodide.toPy(held);
    game.press(keys);
    keys.destroy();
    payload = JSON.parse(game.tick_json());
    frames += 1;
    framesEl.textContent = String(frames);
    exposeForTests();
  }

  // Test-only readout for tools/web/smoke.cjs: proves a held key reached the
  // engine. Position of the human seat (seat A in local mode), taken from the payload.
  function exposeForTests() {
    const v = payload.mode === "local_two_players" ? payload.seats.A.seat_view : payload.seat_view;
    window.__smLast = { frame: frames, me: { room: v.room, row: v.me.row, col: v.me.col } };
  }

  // --- drawing: pooled Phaser objects, one per draw entry, depth = list order ---
  function makeDrawer(scene) {
    const pools = { img: [], rect: [], line: [] };
    const used = { img: 0, rect: 0, line: 0 };

    function take(kind, create) {
      let obj = pools[kind][used[kind]];
      if (obj === undefined) {
        obj = create();
        pools[kind].push(obj);
      }
      used[kind] += 1;
      obj.setVisible(true);
      return obj;
    }

    function frameKey(sheet, src) {
      const key = src.join(",");
      const tex = scene.textures.get(sheet);
      if (!tex.has(key)) {
        tex.add(key, 0, src[0], src[1], src[2], src[3]);
      }
      return key;
    }

    function colour(hex) {
      return parseInt(hex.slice(1), 16);
    }

    function draw(list, dx, depth0) {
      list.forEach(function (d, i) {
        const depth = depth0 + i;
        if (d.img !== undefined) {
          const im = take("img", function () { return scene.add.image(0, 0, d.img); });
          im.setTexture(d.img, frameKey(d.img, d.src));
          im.setFlipX(d.flip);
          im.setDisplaySize(d.w, d.h);
          im.setOrigin(d.ox / d.w, d.oy / d.h);
          im.setPosition(dx + d.x + d.ox, d.y + d.oy);
          im.setAngle(d.rot);
          if (d.tint) { im.setTint(colour(d.tint)); } else { im.clearTint(); }
          im.setDepth(depth);
        } else if (d.rect !== undefined) {
          const r = take("rect", function () { return scene.add.rectangle(0, 0, 1, 1, 0).setOrigin(0, 0); });
          r.setPosition(dx + d.rect[0], d.rect[1]);
          r.setSize(d.rect[2], d.rect[3]);
          r.setFillStyle(colour(d.color));
          r.setDepth(depth);
        } else if (d.line !== undefined) {
          const l = take("line", function () { return scene.add.line(0, 0, 0, 0, 1, 1, 0).setOrigin(0, 0).setLineWidth(1); });
          l.setPosition(dx + 0.5, 0.5);
          l.setTo(d.line[0], d.line[1], d.line[2], d.line[3]);
          l.setStrokeStyle(1, colour(d.color));
          l.setDepth(depth);
        }
      });
      return depth0 + list.length;
    }

    return {
      frame: function (panels) {
        used.img = 0; used.rect = 0; used.line = 0;
        let depth = 0;
        panels.forEach(function (p, k) {
          depth = draw(p.draw, k * (PANEL_W + GAP), depth);
        });
        ["img", "rect", "line"].forEach(function (kind) {
          for (let i = used[kind]; i < pools[kind].length; i += 1) {
            pools[kind][i].setVisible(false);
          }
        });
      },
    };
  }

  function showText(p) {
    const local = p.mode === "local_two_players";
    const panels = local ? [p.seats.A, p.seats.B] : [p];
    hudEl.textContent = panels.map(function (s, k) {
      return (local ? (k === 0 ? "A: " : "B: ") : "") + s.hud.text;
    }).join("   |   ");
    labelEl.textContent = local ? p.label : "";
    rivalEl.textContent = local ? "" : p.rival;
    if (p.outcome.status === "terminal") {
      const r = local ? p.outcome.reason : p.outcome.result;
      const words = { won: "You win", lost: "You lose", draw: "Draw" };
      const vs = local || !p.rival ? "" : " vs " + p.rival;   // the honest mode name (#88)
      outcomeEl.textContent = (words[r] || r) + vs + " (" + p.outcome.reason + "). Press R for a rematch.";
    } else {
      outcomeEl.textContent = "";
    }
    if (rematchButton !== null) {
      rematchButton.update(SMUi.rematchView(p.outcome, "none"));
    }
    return panels;
  }

  // The mode buttons: the shared list from manifest.json, the same three modes and names as
  // the menu and the online lobby. The current one is marked. Built as one string (the labels
  // are the build's own fixed text, escaped anyway).
  function esc(t) {
    return String(t).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function showModes(list) {
    const box = document.getElementById("modes");
    if (!box || !Array.isArray(list)) {
      return;
    }
    const now = SMKeys.currentPlay(opts);
    box.innerHTML = list.map(function (m) {
      return '<a class="mode' + (m.id === now ? " current" : "") + '" href="?play=' +
        esc(m.id) + '">' + esc(m.label) + "</a>";
    }).join("");
  }

  async function main() {
    const manifest = await (await fetch("manifest.json")).json();
    buildEl.textContent = manifest.build;
    showModes(manifest.modes);
    keysEl.textContent = SMKeys.keyHints(opts.mode, opts.seat);
    setStatus("loading Python", "loading");
    await startPython();
    const panels = opts.mode === "local_two_players" ? 2 : 1;
    let drawer = null;
    new Phaser.Game({
      type: Phaser.AUTO,
      parent: "game",
      width: panels * PANEL_W + (panels - 1) * GAP,
      height: PANEL_H,
      zoom: ZOOM,
      pixelArt: true,
      backgroundColor: "#000000",
      scene: {
        preload: function () {
          manifest.sheets.forEach(function (s) { this.load.image(s, "art/" + s + ".png"); }, this);
        },
        create: function () {
          drawer = makeDrawer(this);
          stepGame();
          drawer.frame(showText(payload));
          setStatus("ready", "ready");
        },
        update: function (time, delta) {
          const due = SMKeys.stepClock(acc, delta, TICKS_PER_SECOND, MAX_CATCH_UP);
          acc = due.acc;
          if (due.steps === 0) {
            return;
          }
          for (let i = 0; i < due.steps; i += 1) {
            stepGame();
          }
          drawer.frame(showText(payload));
        },
      },
    });
  }

  main().catch(function (err) {
    setStatus("error: " + err, "error");
    console.error(err);
  });
})();
