"""
讯飞 TTS 服务 — 服务端 WebSocket 合成
"""
import asyncio
import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from urllib.parse import quote

import websockets

APP_ID     = "fb74bf2a"
API_KEY    = "a1ddd25040f6bd8a802a593289054510"
API_SECRET = "YmUwZGRlZWRhMDU3ZjFkNjI4NjFlOGFj"
TTS_HOST   = "tts-api.xfyun.cn"
TTS_PATH   = "/v2/tts"


def _build_auth_url() -> str:
    date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    sign_origin = f"host: {TTS_HOST}\ndate: {date}\nGET {TTS_PATH} HTTP/1.1"
    signature = base64.b64encode(
        hmac.new(
            key=API_SECRET.encode("utf-8"),
            msg=sign_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
    ).decode("utf-8")
    auth_origin = (
        f'api_key="{API_KEY}", algorithm="hmac-sha256", '
        f'headers="host date request-line", signature="{signature}"'
    )
    authorization = base64.b64encode(auth_origin.encode("utf-8")).decode("utf-8")
    return (
        f"wss://{TTS_HOST}{TTS_PATH}"
        f"?authorization={quote(authorization)}"
        f"&date={quote(date)}"
        f"&host={TTS_HOST}"
    )


async def synthesize_audio(text: str, voice: str = "x4_xiaoyan") -> bytes:
    """将文字合成为 MP3 二进制数据"""
    url = _build_auth_url()
    text_b64 = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    chunks: list[bytes] = []

    async with websockets.connect(url, ping_interval=None) as ws:
        await ws.send(
            json.dumps(
                {
                    "common": {"app_id": APP_ID},
                    "business": {
                        "aue":    "lame",
                        "sfl":    1,
                        "tte":    "UTF8",
                        "vcn":    voice,
                        "ent":   "intp65",
                        "speed":  42,
                        "pitch":  50,
                        "volume": 80,
                        "bgs":    0,
                    },
                    "data": {"status": 2, "text": text_b64},
                }
            )
        )

        async for raw in ws:
            res = json.loads(raw)
            if res.get("code") != 0:
                raise RuntimeError(
                    f"讯飞 TTS 错误 {res.get('code')}: {res.get('message')}"
                )
            audio = res.get("data", {}).get("audio")
            if audio:
                chunks.append(base64.b64decode(audio))
            if res.get("data", {}).get("status") == 2:
                break

    return b"".join(chunks)
