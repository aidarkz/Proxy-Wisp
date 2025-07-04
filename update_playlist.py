import os
import time

TEMPLATE_FILE = os.getenv("PLAYLIST_TEMPLATE", "playlist_template.m3u8")
OUTPUT_FILE = os.getenv("PLAYLIST_OUT", "playlist.m3u8")
TOKEN_FILE = "token.txt"

def read_token():
    try:
        with open(TOKEN_FILE) as f:
            token = f.read().strip()
            if not token:
                raise ValueError("Empty token")
            return token
    except Exception as e:
        print(f"[ERROR] Can't read token: {e}")
        return None

def update_playlist():
    token = read_token()
    if not token:
        print("[ERROR] Can't update playlist — token is missing.")
        return

    try:
        with open(TEMPLATE_FILE) as f:
            template = f.read()

        playlist = template.replace("{TOKEN}", token)

        with open(OUTPUT_FILE, "w") as f:
            f.write(playlist)

        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] playlist updated")

    except Exception as e:
        print(f"[ERROR] Failed to update playlist: {e}")

if __name__ == "__main__":
    update_playlist()
