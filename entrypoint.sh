#!/bin/bash

echo "[Docker] START  ($PORTAL  ch=$CH_ID  every ${UPDATE_INTERVAL}s)"
echo "[Docker] starting get_token.py …"

# Первый запуск get_token.py (для генерации токена в логе)
python3 get_token.py --portal "$PORTAL" --ch "$CH_ID" || true

# Запуск update_playlist.py как фонового процесса
python3 update_playlist.py
