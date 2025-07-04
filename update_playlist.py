#!/usr/bin/env python3
"""Заменяет {TOKEN} в плейлисте‑шаблоне и пишет готовый .m3u8."""

import os, datetime
from pathlib import Path

TPL  = Path(os.getenv("PLAYLIST_TEMPLATE", "playlist_template.m3u8"))
OUT  = Path(os.getenv("PLAYLIST_OUT",      "playlist.m3u8"))
TOK  = Path("token.txt")

def log(msg):  # красивый тайм‑стемп
    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)

def main() -> None:
    try:
        token = TOK.read_text(encoding="utf-8").strip()
        if not token:
            raise ValueError("token is empty")
    except Exception as e:
        log(f"[ERROR] Can't read token: {e}")
        return

    try:
        text_out = TPL.read_text(encoding="utf-8").replace("{TOKEN}", token)
        OUT.write_text(text_out, encoding="utf-8")
        log("playlist updated")
    except Exception as e:
        log(f"[ERROR] Can't update playlist: {e}")

if __name__ == "__main__":
    main()
