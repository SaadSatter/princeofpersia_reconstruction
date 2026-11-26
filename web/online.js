// Shadow Masque online page (T13, rooms T18): one browser per rival, one authoritative server.
// No game logic and no Python in the browser here. The page asks for a room (Create room, or
// Join room with a 4-letter code), sends which keys are held and rematch requests, and draws
// the payload for its own seat that the server sends (see docs/final/ONLINE_PLAY.md). It
// never sends outcomes or positions.
/* global Phaser, SMKeys, SMDraw, SMUi */
"use strict";

(function () {
  const PANEL_W = 320;
  const PANEL_H = 200;
  const ZOOM = 3;
  const RETRY_MS = 1000;
  const TOKEN_KEY = "sm-seat-token"; // sessionStorage: one seat per tab
  const CODE_KEY = "sm-room-code";   // sessionStorage: the room that seat belongs to
  const MODE_KEY = "sm-room-mode";   // sessionStorage: the mode of that room (a refresh keeps the code hidden in AI rooms)

  // Decision #55: either control set steers the player's own seat; the server accepts
  // the same 16 names (web/bridge.py ALL_KEY_NAMES) and renames them into the seat's set.

  const statusEl = document.getElementById("status");
  const hudEl = document.getElementById("hud");
  const outcomeEl = document.getElementById("outcome");
  const rivalEl = document.getElementById("rival");
  const buildEl = document.getElementById("build");
  const keysEl = document.getElementById("keys");
  const lobbyEl = document.getElementById("lobby");
  const lobbyMsgEl = document.getElementById("lobby-msg");
  const codeInput = document.getElementById("code-input");
  const createBtn = document.getElementById("create-room");
  const joinBtn = document.getElementById("join-room");
  const roomEl = document.getElementById("room");
  const roomCodeEl = document.getElementById("room-code");

  let ws = null;
  let seat = null;
  let held = {};
  let sentKeys = "";
  let rematchState = "none";
  let drawer = null;
  let latest = null;
  let stopped = false;
  let everJoined = false;
  let chosenMode = null; // one of manifest.modes: picked on the landing state
  let roomMode = null; // the mode of the room this tab is in (decides whether its code is shown)
  let starting = false; // a one-click AI or Baseline start is on its way: ignore a second click
  const humanLobbyEl = document.getElementById("human-lobby");
  let firstMsg = null; // what to send when a socket opens: create, or join with a typed code

  const rematchButton = SMUi.createRematch(document, document.body, function () {
    send({ type: "rematch" });
  });
  rematchButton.update(SMUi.rematchView(null, "none"));

  function setStatus(text, state) {
    statusEl.textContent = text;
    statusEl.dataset.state = state;
  }

  function store(key, value) {
    try {
      if (value === null) { sessionStorage.removeItem(key); } else { sessionStorage.setItem(key, value); }
    } catch (e) { /* private mode */ }
  }

  function load(key) {
    try { return sessionStorage.getItem(key); } catch (e) { return null; }
  }

  // Decision #95: Create room / Join room (and the code) are for Human vs Human only; AI Model
  // and Baseline start a private match with one click on their button.
  function applyLobbyView() {
    humanLobbyEl.style.display = SMKeys.lobbyView(chosenMode).showCreateJoin ? "block" : "none";
  }

  // The landing state: pick a mode (AI and Baseline start at once; Human vs Human then offers
  // Create room, or Join room with a 4-letter code).
  function showLobby(message) {
    starting = false;
    lobbyEl.style.display = "block";
    roomEl.style.display = "none";
    applyLobbyView();
    lobbyMsgEl.textContent = message || "";
    setStatus(message ? "" : "Pick a game mode", "ready");
    outcomeEl.textContent = "";
    hudEl.textContent = "";
    rematchButton.update(SMUi.rematchView(null, "none"));
  }

  function enterRoom(code) {
    lobbyEl.style.display = "none";
    starting = false;
    if (SMKeys.lobbyView(roomMode).showCode) {
      roomEl.style.display = "block";
      roomCodeEl.textContent = code;
    } else {
      roomEl.style.display = "none";           // a private AI match: no code on the page
      roomCodeEl.textContent = "";
    }
  }

  function leaveRoom(message) {
    store(TOKEN_KEY, null);
    store(CODE_KEY, null);
    store(MODE_KEY, null);
    roomMode = null;
    everJoined = false;
    seat = null;
    latest = null;
    showLobby(message);
  }

  function send(msg) {
    if (ws !== null && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  }

  function sendKeys() {
    const names = SMKeys.gameKeys(held);
    const text = names.join(",");
    if (text !== sentKeys) {
      sentKeys = text;
      send({ type: "keys", keys: names });
    }
  }

  window.addEventListener("keydown", function (e) {
    if (seat === null) {
      return; // on the landing state keys are for the code box, not the game
    }
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
    if (seat === null) {
      return;
    }
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
      const vs = p.rival ? " vs " + p.rival : "";     // the honest mode name (#88)
      outcomeEl.textContent = (END_WORDS[p.outcome.result] || p.outcome.result) + vs + " (" + why + ")";
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
      store(TOKEN_KEY, msg.token);
      if (msg.code) {
        store(CODE_KEY, msg.code);
        store(MODE_KEY, roomMode);
        enterRoom(msg.code);
      }
      keysEl.textContent = SMKeys.keyHints("human_vs_ai", seat);
      setStatus("Connected as seat " + seat, "ready");
    } else if (msg.type === "error") {
      // "No room with that code", "That room is full", a stale token or a room that expired:
      // back to the landing state with the server's words. The server keeps the socket open
      // for another try, except after "Too many tries" and an expired room.
      leaveRoom(msg.text);
      stopped = msg.code === "rate_limited" || msg.code === "expired";
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
      sentKeys = "";
      const token = load(TOKEN_KEY);
      const code = load(CODE_KEY);
      if (token && code) {
        send({ type: "join", code: code, token: token }); // refresh or reconnect: the same seat
      } else if (firstMsg !== null) {
        send(firstMsg);
      }
    });
    ws.addEventListener("message", function (e) {
      onMessage(JSON.parse(e.data));
    });
    ws.addEventListener("close", function (e) {
      if (e.code === 1000 && e.reason === "replaced") {
        // The server gave this seat to a newer tab with the same token. Do not fight for it.
        stopped = true;
        setStatus("This seat was opened in another tab", "error");
        return;
      }
      ws = null;
      if (stopped) {
        stopped = false;
        return;
      }
      if (!load(TOKEN_KEY)) {
        // Not in a room: stay on (or return to) the landing state.
        if (lobbyEl.style.display !== "none" && lobbyMsgEl.textContent === "") {
          showLobby("Connection closed. Try again.");
        }
        return;
      }
      setStatus(everJoined ? "Reconnecting" : "Connecting", "loading");
      window.setTimeout(connect, RETRY_MS);
    });
  }

  // Ask for a room. An open socket is reused (the server allows a few tries a minute).
  function begin(msg) {
    firstMsg = msg;
    roomMode = msg.create === true ? chosenMode : "human";   // a typed code is always a human room
    lobbyMsgEl.textContent = "";
    if (ws !== null && ws.readyState === WebSocket.OPEN) {
      send(msg);
    } else {
      setStatus("Connecting", "loading");
      connect();
    }
  }

  // The mode list from manifest.json (the shared mode list). Decision #95: a click on an AI
  // mode starts a private match at once (the server makes a room for this client only); the
  // human mode shows Create room / Join room and waits for a second player.
  function showModePicker(list) {
    const box = document.getElementById("mode-pick");
    function mark() {
      Array.prototype.forEach.call(box.children, function (b) {
        b.setAttribute("aria-pressed", String(b.dataset.mode === chosenMode));
      });
    }
    list.forEach(function (m) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "sm-rematch-btn";
      b.dataset.mode = m.id;
      b.textContent = m.label;
      b.addEventListener("click", function () {
        if (starting || seat !== null) { return; }
        chosenMode = m.id;
        mark();
        applyLobbyView();
        lobbyMsgEl.textContent = "";
        if (SMKeys.lobbyView(chosenMode).startsAtOnce) {
          starting = true;
          begin({ type: "join", create: true, mode: chosenMode });
        }
      });
      box.appendChild(b);
    });
    mark();
  }

  async function main() {
    const manifest = await (await fetch("manifest.json")).json();
    buildEl.textContent = manifest.build;
    keysEl.textContent = SMKeys.keyHints("human_vs_ai", "A");
    showModePicker(manifest.modes);
    createBtn.addEventListener("click", function () {
      if (chosenMode !== "human") { return; }
      begin({ type: "join", create: true, mode: chosenMode });
    });
    joinBtn.addEventListener("click", function () {
      const code = codeInput.value.trim();
      if (code.length !== 4) {
        lobbyMsgEl.textContent = "Type the 4-letter code";
        return;
      }
      begin({ type: "join", code: code });
    });
    codeInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { joinBtn.click(); }
    });
    showLobby("");
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
          if (load(TOKEN_KEY) && load(CODE_KEY)) {
            roomMode = load(MODE_KEY);
            setStatus("Connecting", "loading");
            connect(); // a refreshed tab rejoins its room and seat
          }
        },
      },
    });
  }

  main().catch(function (err) {
    setStatus("error: " + err, "error");
    console.error(err);
  });
})();
