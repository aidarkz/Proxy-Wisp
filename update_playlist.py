import asyncio, os, pathlib, subprocess, sys, time, tempfile

PORTAL   = os.environ["PORTAL"]
CH_ID    = os.environ["CH_ID"]
TPL_PATH = pathlib.Path(os.environ.get("PLAYLIST_TEMPLATE", "playlist_template.m3u8"))
OUT_PATH = pathlib.Path(os.environ.get("PLAYLIST_OUT",       "playlist.m3u8"))

async def get_stream_url() -> str:
    """Запускаем get_token.py и читаем STDOUT."""
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "get_token.py",
        "--portal", PORTAL, "--ch", CH_ID,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"get_token.py failed ({proc.returncode}):\n{stderr.decode()}")
    return stdout.decode().strip()

async def main() -> None:
    url = await get_stream_url()

    text = TPL_PATH.read_text(encoding="utf‑8").replace("__URL__", url)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf‑8") as tmp:
        tmp.write(text)
        tmp.flush()
        os.replace(tmp.name, OUT_PATH)   # atomic
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] playlist updated")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"UPDATE ERROR: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
