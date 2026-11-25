"""Shadow Masque online play (T13): one authoritative server, one browser per rival.

`server.match` is the whole game logic and imports no network code; `server.app`
adds the WebSocket and HTTP layer (the `online` extra). See docs/final/ONLINE_PLAY.md.
"""
