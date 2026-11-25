// Shadow Masque online page (T13): one browser per rival, one authoritative server.
// No game logic and no Python in the browser here. The page sends which keys are held and
// rematch requests, and draws the payload for its own seat that the server
// sends (see docs/final/ONLINE_PLAY.md). It never sends outcomes or positions.
/* global Phaser, SMKeys, SMDraw, SMUi */
"use strict";

(function () {
  const PANEL_W = 320;
  const PANEL_H = 200;
  const ZOOM = 3;
  const RETRY_MS = 1000;
  const TOKEN_KEY = "sm-seat-token"; // sessionStorage: one seat per tab

  // Physical key names of each seat (web/bridge.py KEY_MAP); the server enforces them.
  const SEAT_KEYS = {
    A: ["a", "d", "w", "s", "f", "g", "t", "lshift"],
    B: ["left", "right", "up", "down", ".", "/", "'", "rshift"],
  };

  const statusEl = document.getElementById("status");
  const hudEl = document.getElementById("hud");
  const outcomeEl = document.getElementById("outcome");
  const rivalEl = document.getElementById("rival");
  const buildEl = document.getElementById("build");
  const keysEl = document.getElementById("keys");

  let ws = null;
  let seat = null;
  let held = {};
  let sentKeys = "";
  let rematchState = "none";
  let drawer = null;
  let latest = null;
  let stopped = false;
  let everJoined = false;

  const rematchButton = SMUi.createRematch(document, document.body, function () {
    send({ type: "rematch" });
  });
  rematchButton.update(SMUi.rematchView(null, "none"));

  function setStatus(text, state) {
    statusEl.textContent = text;
    statusEl.dataset.state = state;
  }

  function send(msg) {
    if (ws !== null && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  }

  function sendKeys() {
    const mine = SEAT_KEYS[seat] || [];
    const names = Object.keys(held).filter(function (k) { return mine.indexOf(k) >= 0; }).sort();
    const text = names.join(",");
    if (text !== sentKeys) {
      sentKeys = text;
      send({ type: "keys", keys: names });
    }
  }

  window.addEventListener("keydown", function (e) {
    if (SMKeys.shouldPrevent(e.code)) {
      e.preventDefault();
    }
    if ((SMKeys.keyName(e.code) === "r" || e.code === "Enter") && !e.repeat) {
      rematchButton.press();
      return;
    }
    held = SMKeys.applyKey(held, e.code, true);
    sendKeys();
  });
  window.addEventListener("keyup", function (e) {
    held = SMKeys.applyKey(held, e.code, false);
    sendKeys();
  });
  window.addEventListener("blur", function () {
    held = {};
    sendKeys();
  });

  const END_WORDS = { won: "You win", lost: "You lose", draw: "Draw" };
  const END_REASONS = { rival_disconnected: "Rival disconnected", you_disconnected: "You disconnected" };

  function show(p) {
    hudEl.textContent = p.hud.text;
    rivalEl.textContent = p.rival || "Rival";
    if (p.outcome.status === "terminal") {
      const why = END_REASONS[p.outcome.reason] || p.outcome.reason;
      outcomeEl.textContent = (END_WORDS[p.outcome.result] || p.outcome.result) + " (" + why + ")";
    } else {
      outcomeEl.textContent = "";
    }
    rematchButton.update(SMUi.rematchView(p.outcome, rematchState));
    if (drawer !== null) {
      drawer.frame([p]);
    }
  }

  const STATUS_WORDS = {
    waiting: "Waiting for rival to join",
    playing: "Playing",
    paused: "Paused",
    ended: "Duel over",
  };

  function onMessage(msg) {
    if (msg.type === "hello") {
      seat = msg.seat;
      everJoined = true;
      try { sessionStorage.setItem(TOKEN_KEY, msg.token); } catch (e) { /* private mode */ }
      keysEl.textContent = SMKeys.keyHints("human_vs_ai", seat);
      setStatus("Connected as seat " + seat, "ready");
    } else if (msg.type === "error") {
      if (msg.code === "bad_token") {
        try { sessionStorage.removeItem(TOKEN_KEY); } catch (e) { /* ignore */ }
        everJoined = false;
        return; // the close handler reconnects without a token
      }
      stopped = true;
      setStatus(msg.text, "error");
    } else if (msg.type === "status") {
      rematchState = msg.rematch;
      setStatus(msg.text || STATUS_WORDS[msg.state] || msg.state, msg.state);
      if (latest !== null) {
        show(latest);
      }
    } else if (msg.type === "state") {
      latest = msg;
      show(msg);
    }
  }

  function connect() {
    const proto = window.location.protocol === "https:" ? "wss://" : "ws://";
    ws = new WebSocket(proto + window.location.host + "/ws");
    ws.addEventListener("open", function () {
      let token = null;
      try { token = sessionStorage.getItem(TOKEN_KEY); } catch (e) { /* ignore */ }
      sentKeys = "";
      const joinMsg = { type: "join" };
      if (token) { joinMsg.token = token; }
      send(joinMsg);
    });
    ws.addEventListener("message", function (e) {
      onMessage(JSON.parse(e.data));
    });
    ws.addEventListener("close", function () {
      if (stopped) {
        return;
      }
      setStatus(everJoined ? "Reconnecting" : "Connecting", "loading");
      window.setTimeout(connect, RETRY_MS);
    });
  }

  async function main() {
    const manifest = await (await fetch("manifest.json")).json();
    buildEl.textContent = manifest.build;
    keysEl.textContent = SMKeys.keyHints("human_vs_ai", "A");
    setStatus("Connecting", "loading");
    new Phaser.Game({
      type: Phaser.AUTO,
      parent: "game",
      width: PANEL_W,
      height: PANEL_H,
      zoom: ZOOM,
      pixelArt: true,
      backgroundColor: "#000000",
      scene: {
        preload: function () {
          manifest.sheets.forEach(function (s) { this.load.image(s, "art/" + s + ".png"); }, this);
        },
        create: function () {
          drawer = SMDraw.makeDrawer(this, PANEL_W, 0);
          if (latest !== null) {
            show(latest);
          }
          connect();
        },
      },
    });
  }

  main().catch(function (err) {
    setStatus("error: " + err, "error");
    console.error(err);
  });
})();
