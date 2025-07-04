import asyncio, os, time, subprocess, sys, pathlib, shutil, tempfile

PORTAL   = os.getenv("PORTAL")
CH_ID    = os.getenv("CH_ID")
INTERVAL = int(os.getenv("UPDATE_INTERVAL", "300"))   # сек

TEMPLATE = pathlib.Path("playlist_template.m3u8")
OUTPUT   = pathlib.Path("playlist.m3u8")

if not PORTAL or not CH_ID:
    sys.exit("ENV PORTAL / CH_ID не заданы")

async def get_stream_url() -> str:
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "get_token.py",
        "--portal", PORTAL, "--ch", str(CH_ID),
        stdout=asyncio.subprocess.PIPE
    )
    out, _ = await proc.communicate()
    if proc.returncode:
        raise RuntimeError("get_token.py exit %s" % proc.returncode)
    return out.decode().strip()

def render_playlist(stream_url: str):
    tmp = OUTPUT.with_suffix(".tmp")
    txt = TEMPLATE.read_text(encoding="utf-8")
    tmp.write_text(txt.replace("__URL__", stream_url), encoding="utf-8")
    tmp.replace(OUTPUT)

async def main():
    while True:
        try:
            url = await get_stream_url()
            render_playlist(url)
            print(f"[{time.strftime('%F %T')}] playlist updated → {url}")
        except Exception as e:
            print(f"[UPDATE‑ERROR] {e}", file=sys.stderr)
        await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
