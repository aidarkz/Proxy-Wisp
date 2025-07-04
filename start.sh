#!/bin/bash
# Запуск обновления плейлиста в фоне + старт прокси

# Обновление плейлиста каждые 5 минут
while true; do
    python update_playlist.py
    sleep 300
done &

# Запуск aiohttp-прокси
python proxy_server.py