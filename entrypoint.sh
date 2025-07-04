#!/usr/bin/env bash
set -euo pipefail

echo "[Docker] START: $PORTAL CH=$CH_ID, interval ${UPDATE_INTERVAL}s"

# 1) бесконечно крутим get_token.py (чтобы всегда был запущен)
( while true; do
      python -u get_token.py --portal "$PORTAL" --ch "$CH_ID" || true
      sleep "$UPDATE_INTERVAL"
  done ) &
GET_TOKEN_PID=$!

# 2) периодически вызываем update_playlist.py
while true; do
    python -u update_playlist.py
    sleep "$UPDATE_INTERVAL"
done &

# 3) ждём детей (Ctrl‑C/<kill> корректно завершают всё благодаря tini)
wait -n
