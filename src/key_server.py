"""
평가/배포용 키 서버.

제공자 API 키는 이 프로세스의 환경변수(.env)에만 둔다.
클라이언트는 Bearer 토큰이 맞을 때만 키 JSON을 받는다.

실행:
  python key_server.py
  python key_server.py --host 0.0.0.0 --port 8787
"""

import argparse
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from dotenv import load_dotenv

from key_client import PROVIDER_KEYS

load_dotenv()


def _token():
    return os.environ.get("KEY_SERVER_TOKEN", "").strip()


def _authorized(handler):
    expected = _token()
    if not expected:
        return False
    header = handler.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        given = header[7:].strip()
    else:
        given = handler.headers.get("X-Key-Token", "").strip()
    if not given or len(given) != len(expected):
        return False
    return hmac.compare_digest(given, expected)


class KeyHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[key-server]", fmt % args)

    def _send(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/health", "/"):
            self._send(200, {"ok": True, "service": "travel-planner-key-server"})
            return
        if path != "/keys":
            self._send(404, {"error": "not_found"})
            return
        if not _token():
            self._send(500, {"error": "server_token_missing"})
            return
        if not _authorized(self):
            self._send(401, {"error": "unauthorized"})
            return
        keys = {}
        for name in PROVIDER_KEYS:
            value = os.environ.get(name, "").strip()
            if value:
                keys[name] = value
        self._send(200, keys)


def main():
    parser = argparse.ArgumentParser(description="Travel planner key server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    if not _token():
        print("[오류] KEY_SERVER_TOKEN 이 .env 에 없습니다.")
        raise SystemExit(1)

    present = [name for name in PROVIDER_KEYS if os.environ.get(name, "").strip()]
    print(f"[key-server] 제공할 키: {', '.join(present) or '(없음)'}")
    print(f"[key-server] http://{args.host}:{args.port}/keys")
    print("[key-server] 토큰 없는 요청은 401로 거절합니다.")
    server = ThreadingHTTPServer((args.host, args.port), KeyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[key-server] 종료")


if __name__ == "__main__":
    main()
