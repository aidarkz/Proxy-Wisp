import asyncio, subprocess, re, sys, pathlib, os, datetime, http.client

BASE      = pathlib.Path(__file__).parent
TEMPLATE  = BASE / "playlist_template.m3u8"
OUTPUT    = BASE / "playlist.m3u8"

PORTAL    = os.getenv("PORTAL" , "http://portal.wisp.cat")
CH_ID     = os.getenv("CHANNEL", "3920")
PY        = sys.executable

# ────────────────────────── получить токен ──────────────────────────
async def fetch_token() -> str:
    proc = await asyncio.create_subprocess_exec(
        PY, "get_token.py",
        "--portal", PORTAL,
        "--ch", CH_ID,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out_b, err_b = await proc.communicate()
    out, err = out_b.decode(), err_b.decode()

    if proc.returncode != 0:
        raise RuntimeError(f"get_token.py failed ({proc.returncode}): {err.strip()}")

    m = re.search(r"token=([0-9a-f]{32})", out)
    if not m:
        raise RuntimeError("token not found in output:\n" + out.strip())
    return m.group(1)

# ────────────────────────── keep‑awake ping ─────────────────────────
def keep_awake():
    try:
        conn = http.client.HTTPConnection("lb.wisp.cat", timeout=3)
        conn.request("HEAD", "/")
        conn.close()
    except Exception:
        pass

# ────────────────────────── основной цикл ───────────────────────────
async def main():
    while True:
        try:
            token = await fetch_token()
            text  = TEMPLATE.read_text(encoding="utf-8").replace("{TOKEN}", token)
            OUTPUT.write_text(text, encoding="utf-8")
            print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] playlist updated")
        except Exception as e:
            print("UPDATE ERROR:", e, file=sys.stderr)

        keep_awake()          # лёгкий ping каждые 5 минут
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())
