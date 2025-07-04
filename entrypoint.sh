#!/usr/bin/env bash
set -euo pipefail

log() { printf '[Docker] %s\n' "$*"; }

log "START  ($PORTAL  ch=$CH_ID  every ${UPDATE_INTERVAL}s)"

# ─── 1. поднимаем лёгкий HTTP‑сервер (порт 80) ────────────────────────────────
python3 -m http.server 80 --bind 0.0.0.0 &
HTTP_PID=$!

# ─── 2. запускаем get_token.py в фоне и следим, чтобы он жил ──────────────────
start_auth() {
    log "starting get_token.py …"
    python3 get_token.py --portal "$PORTAL" --ch "$CH_ID" &
    AUTH_PID=$!
}
start_auth

# ─── 3. вечный цикл: обновляем плейлист, ресайкл авторизацию при падении ──────
while true; do
    if ! kill -0 "$AUTH_PID" 2>/dev/null; then
        log "get_token.py is dead → restart"
        start_auth
    fi

    python3 update_playlist.py
    sleep "$UPDATE_INTERVAL"
done
