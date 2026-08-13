"""
백엔드 키 서버 클라이언트.

제공자 키를 exe에 넣지 않고, 토큰이 맞는 요청만 서버에서 받아온다.
"""

import hmac
import os

import requests

DEFAULT_KEY_SERVER_URL = "https://codyssey-5-project.onrender.com/api/keys"

PROVIDER_KEYS = (
    "GEMINI_API_KEY",
    "KAKAO_REST_API_KEY",
    "TMAP_OPEN_API_APP_KEY",
    "TOUR_API_SERVICE_KEY",
)


def token_matches(given, expected):
    if not given or not expected or len(given) != len(expected):
        return False
    return hmac.compare_digest(given, expected)


def apply_key_payload(payload, override=False):
    """서버 JSON을 환경변수에 넣는다. 값은 출력하지 않는다."""
    if not isinstance(payload, dict):
        raise ValueError("키 서버 응답이 JSON 객체가 아닙니다.")
    applied = []
    for name in PROVIDER_KEYS:
        value = payload.get(name)
        if not value:
            continue
        if not override and os.environ.get(name, "").strip():
            continue
        os.environ[name] = str(value).strip()
        applied.append(name)
    return applied


def fetch_keys_from_server(url, token, timeout=15):
    if not url:
        raise ValueError("KEY_SERVER_URL 이 비어 있습니다.")
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(url, headers=headers, timeout=timeout)
    if response.status_code in (401, 403):
        raise RuntimeError("키 서버 인증 실패. KEY_SERVER_TOKEN 을 확인하세요.")
    response.raise_for_status()
    return apply_key_payload(response.json(), override=False)
