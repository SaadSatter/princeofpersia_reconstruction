# Online play (T13)

Two people on two computers on the same Wi-Fi play one arena duel. Decisions:
#35 (build it), #36 (Saad's laptop, same LAN), #37 (`websockets`, the `online`
extra), #38 (pause 15 s, then forfeit), #41 (a Rematch button in the game's
style), #25 (rematch keeps the seed). The server holds the only `GameState`.

## Run it on a LAN

On the host machine (Saad's Mac):

```sh
uv run --extra online python -m server            # two humans
uv run --extra online python -m server --rival baseline   # you alone vs the scripted baseline on seat B
```

Options: `--host` (default `0.0.0.0`), `--port` (default 8765), `--seed`
(default 0; the seed is never sent to a client), `--rival baseline`,
`--neutral` (label the AI seat just "Rival"), `--trace-dir` (default
`traces/online/`).

It prints the URL to give the players, for example
`http://192.168.1.23:8765/`.

### Play with a room code (T18, decision #52)

Many duels can run on one server at once, one per room.

1. Both players open the URL. The page offers **Create room** and **Join room**.
2. Player 1 presses **Create room**. The page shows a 4-letter code (capital
   letters, no I and no O, for example `KTWM`) and Player 1 takes seat A (WASD,
   F, G, T, left Shift). Read the code to Player 2.
3. Player 2 types the code (any case) and presses **Join room**, and takes seat
   B (arrows, `.`, `/`, `'`, right Shift). The duel starts.
4. A wrong or expired code says "No room with that code"; a room that already
   has two players says "That room is full". You can retry. After 10 failed
   joins in a minute on one connection the server refuses and closes it ("Too
   many tries"). *Proposal for Saad:* the number 10 a minute.
5. With `--rival baseline`, **Create room** gives you seat A at once and the
   scripted baseline is seat B. Nobody needs to join (a Join is told the room is
   full).

Each room has its own duel, tick loop, pause and forfeit (#38), rematch (#41)
and trace file (`duel-<CODE>-NNN-seed<seed>.json`); a slow or stalled player in
one room never delays another, and an error in one room (an unwritable `--trace-dir`, say) is logged on the server with the room code, never sent to a client, and ends only that room (decision #63). Seat tokens belong to one room: a token from
room X is refused by room Y. Seat tokens and the room code live in the tab's
`sessionStorage`, so a refreshed tab rejoins its room and seat, and two tabs on
one machine are two seats. The one exception: if Player 1 refreshes before
Player 2 has joined, the seat is freed (T13 behaviour), so the old code may
no longer hold Player 1; create a new room.

A room expires when both players have been gone for 15 s (the forfeit window,
#38) or 10 minutes after it was created with no second player (a baseline room
never waits for one). Its code can be used again only after that. The server
holds at most 50 rooms (*proposal for Saad*; Create then says "The server is
full"). The code comes from the operating system's random source
(`random.SystemRandom`), never from the duel's seed. The page and the server
tell a client nothing about any other room: no list, no count.
**The default room (decision #56).** `python -m server` also keeps one room with
no code, for scripted clients and the T13 flow. A `{"type":"join"}` with no
code and no `create` flag enters it: first is seat A, second seat B, the third is
told "That room is full", and it resets when everyone has left. It never
expires, has no code, and does not count toward the 50 rooms. The page has no
button for it (Create and Join only); coded rooms and the default room share
nothing (separate seats, tokens and messages). Its traces are named
`duel-HOME-NNN-seed<seed>.json`. A token from one is refused by the other.
Limits as built are approved (#57): 10 failed joins per connection per minute,
50 rooms, expiry 10 min or 15 s, no per-IP limit.

**Internet is needed.** The page loads Phaser from the pinned CDN
(`web/versions.json`, decision #25), so the host's players and the page's
browsers need internet access. The game channel itself stays on the LAN.

### Find the Mac's IP

The server prints it. By hand: System Settings, Wi-Fi, Details, "IP address";
or `ipconfig getifaddr en0` in Terminal.

### macOS firewall

The first run may show "Do you want the application Python to accept incoming
network connections?" Choose Allow. If players cannot connect, check System
Settings, Network, Firewall, and that both machines are on the same Wi-Fi (guest
or "client isolation" networks block it).

## What each player sees

The page (`web/online.html`, `web/online.js`) draws only its own seat's view
with `web/draw.js`, a copy of the hosted page's Phaser drawer (kept separate because `tests/test_gate_t14_qa_main_contract.py` loads `main.js` alone). It shows:
status (connecting, waiting for rival, playing, paused, duel over), the HUD,
its own key hints, the build hash and the outcome. It sends only the keys held
(`{"type":"keys"}`), a `join` (with a room code and optional token, or `create: true`) and `{"type":"rematch"}`.
It contains no game rules and publishes no test hook (`window.__smLast` is
only in the hosted page).

Labels: in human vs human the opponent is just "Rival". With `--rival baseline`
the web build's label is kept ("AI rival: ...") unless `--neutral`.
*Flag for Saad:* whether the default for `--rival baseline` should be neutral
is his call.

## The tick loop

The server steps the duel 12 times a second with an injectable clock (wall
time is only used for pacing, never inside the engine). Each tick uses each
seat's latest held keys (none held before a message). The inputs are resolved
by `web/bridge.py` (`seat_input`, the in-air LUNGE to KICK swap, the
`legal_actions` filter), not copied. A stall catches up at most 3 ticks. With
`--rival baseline` the AI seat answers within 0.04 s or its tick is a labelled
WAIT, so a slow controller never stalls the human's loop.

The server serves only `online.html`, its four scripts, `art/*` and
`manifest.json`. It never serves `game.zip`, `index.html`, `main.js` or any
engine or agent code (the arena layout and guard scripts are in `game.zip`).
The rival is chosen by `--rival` on the command line only; the page passes no
option through and cannot learn the AI seat's kind. The AI seat's fallbacks
(a slow answer replaced by WAIT, or a failed controller) are counted in the
server-side trace as `{"source": "fallback", "seat": "B", ...}` and
summarised in the server log; they are never sent to the human's client.
Online play only logs these fallbacks (`"source": "fallback"`) and never aborts a
live duel because of one (decision #49). Each duel's trace (including after a
rematch) carries exactly its own fallbacks. `traces/online/` is git-ignored.

## Disconnect and rematch

* A dropped socket mid-duel pauses the duel for both players (the server just
  stops ticking). The other player sees "Rival disconnected, waiting up to 15
  s"; the dropped page shows "Reconnecting" and rejoins with its token. Back
  within 15 s: play resumes from the same frame. Otherwise the dropped seat
  loses; the end screens read "Rival disconnected" (winner) and "You
  disconnected" (loser). Rule row: `docs/RULE_SOURCE_MAP.md` R-S01 (`design`,
  decision #38). A wrong token never takes a seat.
* A silent drop (Wi-Fi gone, lid shut) is noticed by an explicit keepalive: a
  ping every 3 s, 3 s to answer (decision #48), so about 6 s. The seat's held
  keys are cleared at once, then the 15 s grace starts. A client that stops
  reading is handled the same way: each seat has its own outgoing queue, stale
  frames are dropped, and a send that takes over 2 s closes only that socket
  (a disconnect). The tick loop and the other seat never wait on a socket.
* A reconnect with the token gets its `hello` immediately; the old socket is
  closed in the background. If the new socket dies before it hears `hello`, the
  seat is released as a disconnect. A tab whose seat was taken by a newer tab
  with the same token shows "This seat was opened in another tab" and does not
  reconnect.
* A WebSocket whose `Origin` host differs from the `Host` header is refused
  (403); this is a LAN-only server. Clients with no `Origin` are accepted.
* When the duel ends a **Rematch** button pops up on each screen (click, R or
  Enter). The first press shows "Waiting for rival…"; the other player sees
  "Rival wants a rematch". When both have pressed, the duel restarts with the
  same seed (#25). In the `--rival baseline` and hosted modes one press
  restarts. *Still Saad's:* confirming the "both players press" reading of #41.
* The button is CSS drawn from the generated granite tile (`art/tiles.png`),
  hard pixel edges, no smoothing, no stock widget look (`web/ui.js`). No new
  art was added.

## Knowledge boundary and how it is tested

A client receives only: `hello` (its own seat, token and room code), `state` (its own
seat's `seat_view`, `draw`, `hud`, `outcome`, and the AI label when there is
one) and `status` (fixed text chosen by connection state alone), or `error`
(`full`, `bad_token`, `no_room`, `expired`, `rate_limited`, `busy`). Never sent: the `GameState`, the other seat's
observation, payload, keys or token, input counts, the seed, trap ownership,
guard scripts, or whether a figure is a disguised rival (R-V25). The input
trace stays on the server (written to `--trace-dir` after each duel).

Tests: `tests/test_online_boundary.py` (every message to A over a duel where B
disguises and rigs is allow-listed; B's rig and disguise change none of A's
bytes; a disguised rival and a real guard give byte-identical messages;
statuses are equal for every hidden state; no `websockets` import outside
`server/app.py`), `tests/test_server_match.py` (seats, tokens, junk, pacing,
determinism by replaying the trace through `VersusEpisode`, disconnect,
rematch), `tests/test_server_ws.py` (the same over real sockets with a fake
clock; the page served by the same port, with an allow-list), and
`tests/test_online_web.py`.

Limits: a message over 512 characters, binary, malformed or from another seat is
ignored; a frame over 1 MiB closes that socket (library limit) and counts as a
drop for that seat.

## What was and was not verified

Verified: the test suite above; a scripted run of `python -m server` on
localhost with three WebSocket clients (seats A and B, "full" for the third,
about 12 state messages a second, the page served on the same port).

**Not verified:** a real browser (the page, the Phaser drawing, the button's
look, key handling); two machines; the firewall prompt; Wi-Fi drops. A wired
drop is simulated only by closing sockets in tests. The visual check of the
button is for QA or Saad.
