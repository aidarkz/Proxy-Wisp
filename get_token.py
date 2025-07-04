import asyncio
import httpx
import hashlib
import argparse
import random
import time
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG250 stbapp ver: 2 rev: 250 Safari/533.3",
    "X-User-Agent": "Model: MAG250; Link: WiFi",
    "Accept": "*/*",
    "Pragma": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "",  # позже вставим сессией
}

MAG_SN = "0FC033179282C"
MAG_HW_VERSION = "1.7-BD-00"
MAG_DEVICE_ID = "5C7CA90674C7A31C8C663F7173CC7DB4D1CC5E99384871A090D3288CDAA465DE"

MAC_LIST = [
    "00:1A:79:56:0B:99",
    "00:1A:79:A8:D9:68"
]

class PortalAuth:
    def __init__(self, portal: str, debug=False):
        self.portal = portal.rstrip("/")
        self.base_url = f"{self.portal}/stalker_portal"
        self.session_url = f"{self.base_url}/c/"
        self.api_url = f"{self.base_url}/server/load.php"
        self.debug = debug
        self.client = httpx.AsyncClient(http2=False, follow_redirects=True, timeout=15.0)
        self.token = ""
        self.mac = ""
        self.headers = HEADERS.copy()

    async def session(self):
        if self.debug:
            print(f"[GET  ] {self.session_url}")
        r = await self.client.get(self.session_url, headers=self.headers)
        if r.status_code != 200:
            if self.debug:
                print(f"[FAIL] session /c/ status {r.status_code}")
            return False
        return True

    async def handshake(self):
        payload = {
            "type": "stb",
            "action": "handshake",
            "token": "",
            "JsHttpRequest": "1-xml"
        }
        r = await self.client.post(self.api_url, data=payload, headers=self.headers)
        if self.debug:
            print(f"[POST ] handshake → {r.status_code} [{len(r.content)}b]")
        if r.status_code == 200 and "js" in r.json():
            self.token = r.json()["js"]["token"]
            self.headers["Authorization"] = f"Bearer {self.token}"
            return True
        return False

    async def get_profile(self):
        timestamp = int(time.time())
        random_str = hashlib.md5(str(random.random()).encode()).hexdigest()
        prehash = hashlib.sha1(f"{self.mac}:{MAG_SN}:{timestamp}".encode()).hexdigest()
        signature = hashlib.sha256((self.token + self.mac).encode()).hexdigest()

        data = {
            "type": "stb",
            "action": "get_profile",
            "token": self.token,
            "JsHttpRequest": "1-xml",
            "hd": "1",
            "ver": "ImageDescription: 0.2.18-r23-250; ImageDate: Thu Sep 13 11:31:16 EEST 2018; PORTAL version: 5.5.0",
            "num_banks": "2",
            "sn": MAG_SN,
            "stb_type": "MAG250",
            "client_type": "STB",
            "image_version": "218",
            "video_out": "hdmi",
            "device_id": MAG_DEVICE_ID,
            "device_id2": MAG_DEVICE_ID,
            "signature": signature,
            "auth_second_step": "1",
            "hw_version": MAG_HW_VERSION,
            "not_valid_token": "0",
            "metrics": f'{{"mac":"{self.mac}","sn":"{MAG_SN}","type": "STB", "model":"MAG250","uid":"","random":"{random_str}"}}',
            "hw_version_2": "48993152b20e646ed9538d121e381a5d1db6a54c",
            "timestamp": str(timestamp),
            "api_signature": "262",
            "prehash": prehash
        }

        r = await self.client.post(self.api_url, data=data, headers=self.headers)
        if self.debug:
            print(f"[POST ] get_profile → {r.status_code} [{len(r.content)}b]")
        return r.status_code == 200

    async def create_link(self, channel_id: int):
        cmd = f"ffrt http:///ch/{channel_id}"
        data = {
            "type": "itv",
            "action": "create_link",
            "cmd": cmd,
            "series": "0",
            "forced_storage": "0",
            "disable_ad": "0",
            "download": "0",
            "force_ch_link_check": "0",
            "JsHttpRequest": "1-xml"
        }
        r = await self.client.post(self.api_url, data=data, headers=self.headers)
        if self.debug:
            print(f"[POST ] create_link → {r.status_code} [{len(r.content)}b]")
        if r.status_code == 200 and b"http" in r.content:
            return r.json()["js"]["cmd"]
        elif r.status_code == 200 and r.text.strip() == "Authorization failed.":
            print(f"[FAIL] {self.mac}: Authorization failed.")
        else:
            print(f"[FAIL] {self.mac}: create_link raw → {r.text[:64]}")
        return None

    async def get_token_url(self, channel_id: int):
        for mac in MAC_LIST:
            self.mac = mac
            cookies = {"mac": mac, "stb_lang": "en", "timezone": "Europe/Paris"}
            self.client.cookies.clear()
            self.client.cookies.update(cookies)

            if not await self.session():
                continue

            if not await self.handshake():
                continue

            print(f"[AUTH] {mac} -> {self.token}")

            if not await self.get_profile():
                continue

            link = await self.create_link(channel_id)
            if link:
                return link
        raise RuntimeError("Ни один MAC не прошёл")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--portal", required=True)
    parser.add_argument("--ch", type=int, required=True)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    auth = PortalAuth(args.portal, debug=args.debug)
    url = await auth.get_token_url(args.ch)
    print(f"[URL ] {url}")

if __name__ == "__main__":
    asyncio.run(main())
