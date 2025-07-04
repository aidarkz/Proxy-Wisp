#!/bin/sh
set -e

echo "[Docker] START  ($PORTAL  ch=$CH_ID  every ${UPDATE_INTERVAL}s)"

# 1) поднимем статический HTTP‑сервер (файлы лежат в /app)
python -m http.server 80 --directory /app &
HTTP_PID=$!

# 2) бесконечный цикл обновления плейлиста
while true; do
    echo "[Docker] Обновление плейлиста..."
    python /app/update_playlist.py \
           --portal "$PORTAL" \
           --ch "$CH_ID" \
           --template "$PLAYLIST_TEMPLATE" \
           --output   "$PLAYLIST_OUT" \
           || echo "[WARN] update_playlist.py failed, retry in ${UPDATE_INTERVAL}s"

    sleep "$UPDATE_INTERVAL"
done
