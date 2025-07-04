#!/usr/bin/env python3
import asyncio, httpx, hashlib, argparse, random, time, sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# ─────────────────────────────────── настройки/константы ──────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) "
                  "AppleWebKit/533.3 (KHTML, like Gecko) "
                  "MAG250 stbapp ver: 2 rev: 250 Safari/533.3",
    "X-User-Agent": "Model: MAG250; Link: WiFi",
    "Accept": "*/*",
    "Pragma": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "",          # будет заполняться при запросе /c/
}

MAG_SN          = "0FC033179282C"
MAG_HW_VERSION  = "1.7-BD-00"
MAG_DEVICE_ID   = "5C7CA90674C7A31C8C663F7173CC7DB4D1CC5E99384871A090D3288CDAA465DE"
MAC_LIST        = ["00:1A:79:56:0B:99", "00:1A:79:A8:D9:68"]

# ──────────────────────────────  класс авторизации  ───────────────────────────
class PortalAuth:
    def __init__(self, portal: str, debug=False):
        self.portal      = portal.rstrip("/")
        self.base_url    = f"{self.portal}/stalker_portal"
        self.session_url = f"{self.base_url}/c/"
        self.api_url     = f"{self.base_url}/server/load.php"

        self.debug  = debug
        self.token  = ""
        self.mac    = ""
        self.client = httpx.AsyncClient(http2=False,
                                        follow_redirects=True,
                                        timeout=15.0)
        self.headers = HEADERS.copy()

    # ------------- вспомогательные запросы (session → handshake → profile) ----
    async def session(self) -> bool:
        if self.debug:
            print(f"[GET ] {self.session_url}")
        r = await self.client.get(self.session_url, headers=self.headers)
        ok = r.status_code == 200
        if not ok and self.debug:
            print(f"[FAIL] session {r.status_code}")
        return ok

    async def handshake(self) -> bool:
        data = {"type": "stb", "action": "handshake",
                "token": "", "JsHttpRequest": "1-xml"}
        r = await self.client.post(self.api_url, data=data, headers=self.headers)
        if self.debug:
            print(f"[POST] handshake → {r.status_code} [{len(r.content)}b]")
        if r.status_code != 200 or "js" not in r.json():
            return False
        self.token = r.json()["js"]["token"]
        self.headers["Authorization"] = f"Bearer {self.token}"
        return True

    async def get_profile(self) -> bool:
        ts        = int(time.time())
        rnd_hash  = hashlib.md5(str(random.random()).encode()).hexdigest()
        prehash   = hashlib.sha1(f"{self.mac}:{MAG_SN}:{ts}".encode()).hexdigest()
        signature = hashlib.sha256((self.token + self.mac).encode()).hexdigest()

        data = {
            "type": "stb", "action": "get_profile", "token": self.token,
            "JsHttpRequest": "1-xml",
            # ↓ поля, которые портал проверяет
            "hd": "1",
            "ver": "ImageDescription: 0.2.18-r23-250; PORTAL version: 5.5.0",
            "sn": MAG_SN,
            "stb_type": "MAG250",
            "client_type": "STB",
            "image_version": "218",
            "device_id": MAG_DEVICE_ID,
            "device_id2": MAG_DEVICE_ID,
            "signature": signature,
            "auth_second_step": "1",
            "hw_version": MAG_HW_VERSION,
            "not_valid_token": "0",
            "metrics": f'{{"mac":"{self.mac}","sn":"{MAG_SN}",'
                       f'"type":"STB","model":"MAG250","uid":"",'
                       f'"random":"{rnd_hash}"}}',
            "timestamp": str(ts),
            "prehash": prehash,
            "api_signature": "262",
        }
        r = await self.client.post(self.api_url, data=data, headers=self.headers)
        if self.debug:
            print(f"[POST] get_profile → {r.status_code} [{len(r.content)}b]")
        return r.status_code == 200

    # -------------------- запрашиваем прямую ссылку на канал ------------------
    async def create_link(self, ch_id: int) -> str | None:
        data = {
            "type": "itv", "action": "create_link",
            "cmd": f"ffrt http:///ch/{ch_id}",
            "series": "0", "forced_storage": "0",
            "disable_ad": "0", "download": "0",
            "force_ch_link_check": "0",
            "JsHttpRequest": "1-xml",
        }
        r = await self.client.post(self.api_url, data=data, headers=self.headers)
        if self.debug:
            print(f"[POST] create_link → {r.status_code} [{len(r.content)}b]")
        if r.status_code == 200 and b"http" in r.content:
            return r.json()["js"]["cmd"]
        if r.status_code == 200 and r.text.strip() == "Authorization failed.":
            print(f"[FAIL] {self.mac}: Authorization failed.")
        return None

    # ------------------ полный цикл авторизации для списка MAC ----------------
    async def get_token_url(self, ch_id: int) -> str:
        for mac in MAC_LIST:
            self.mac = mac
            # сессионные куки
            self.client.cookies.clear()
            self.client.cookies.update(
                {"mac": mac, "stb_lang": "en", "timezone": "Europe/Paris"}
            )

            if not await self.session():   continue
            if not await self.handshake(): continue

            print(f"[AUTH] {mac} -> {self.token}")

            if not await self.get_profile():
                continue

            link = await self.create_link(ch_id)
            if link:
                return link

        raise RuntimeError("Ни один MAC не прошёл")

# ──────────────────────────────── main() ─────────────────────────────────────―
async def main() -> str | None:
    p = argparse.ArgumentParser()
    p.add_argument("--portal", required=True)
    p.add_argument("--ch", type=int, required=True)
    p.add_argument("--debug", action="store_true")
    args = p.parse_args()

    auth = PortalAuth(args.portal, debug=args.debug)
    return await auth.get_token_url(args.ch)

# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    url = asyncio.run(main())
    if not url:
        sys.exit("[ERROR] url not received")

    print(f"[URL ] {url}")

    # --- вытаскиваем token=... из URL и кладём в token.txt --------------------
    token = parse_qs(urlparse(url).query).get("token", [""])[0]
    if token:
        Path("token.txt").write_text(token, encoding="utf-8")
        print(f"[INFO] Token saved to token.txt ({token[:8]}...)")
    else:
        print("[WARN] token param not found in URL")
