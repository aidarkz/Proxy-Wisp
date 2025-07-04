#!/bin/bash
echo "[Docker] START  ($PORTAL  ch=$CH_ID  every ${UPDATE_INTERVAL}s)"

# старт get_token.py однократно
echo "[Docker] starting get_token.py …"
python3 get_token.py --portal "$PORTAL" --ch "$CH_ID"

# запуск update_playlist.py в фоне по интервалу
(
  while true; do
    echo "[Docker] Обновление плейлиста..."
    python3 update_playlist.py
    sleep "$UPDATE_INTERVAL"
  done
) &

# запускаем HTTP сервер как основной процесс
exec python3 -m http.server 80 --bind 0.0.0.0
