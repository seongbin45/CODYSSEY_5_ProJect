"""
유틸리티 모듈

날짜 검증, 결과 저장, 에러 관리 등 공통 헬퍼 함수를 제공한다.
"""

import json
import os
import sys
from datetime import datetime


def app_dir():
    """프로젝트 루트 또는 exe 폴더. results/ 와 .env 기준 경로."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(here) == "src":
        return os.path.dirname(here)
    return here


def resource_dir():
    """PyInstaller가 풀은 임시 폴더. 번들된 .env 를 여기서 찾는다."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", app_dir())
    return app_dir()


def results_dir():
    path = os.path.join(app_dir(), "results")
    os.makedirs(path, exist_ok=True)
    return path


def load_runtime_env(key_server_url=None, key_server_token=None):
    """
    로컬 .env 를 읽는다.
    --key-server 또는 KEY_SERVER_URL 을 명시한 경우에만 키 서버를 호출한다.
    이미 있는 환경변수는 덮어쓰지 않는다.
    """
    from dotenv import load_dotenv

    from key_client import fetch_keys_from_server

    load_dotenv(os.path.join(resource_dir(), ".env"), override=False)
    load_dotenv(os.path.join(app_dir(), ".env"), override=True)

    url = (key_server_url or os.environ.get("KEY_SERVER_URL", "")).strip()
    token = (key_server_token or os.environ.get("KEY_SERVER_TOKEN", "")).strip()
    if not url:
        return

    print(f"[정보] 키 서버에서 설정을 불러옵니다: {url}")
    try:
        applied = fetch_keys_from_server(url, token)
    except Exception as exc:
        print(f"[오류] 키 서버 요청 실패: {exc}")
        return
    if applied:
        print(f"[정보] 키 서버에서 받은 항목: {', '.join(applied)}")
    else:
        print("[정보] 키 서버 응답에 새로 적용할 키가 없습니다.")


def validate_date(date_str):
    """
    날짜 문자열이 YYYY-MM-DD 형식인지 검증한다.

    Args:
        date_str: 검증할 날짜 문자열

    Returns:
        True이면 유효, False이면 무효
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def normalize_secret(value):
    """환경변수에 붙은 따옴표, Bearer/KakaoAK 접두어를 제거한다."""
    text = (value or "").strip().strip('"').strip("'").strip()
    for prefix in ("KakaoAK ", "kakaoak ", "Bearer "):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    return text


def check_api_keys(require_kakao=True):
    """
    필수 API 키가 환경변수에 설정되어 있는지 확인한다.
    """
    gemini_key = normalize_secret(os.environ.get("GEMINI_API_KEY", ""))
    kakao_key = normalize_secret(
        os.environ.get("KAKAO_REST_API_KEY") or os.environ.get("KAKAO_API_KEY") or ""
    )
    tmap_key = normalize_secret(os.environ.get("TMAP_OPEN_API_APP_KEY", ""))
    tour_key = normalize_secret(os.environ.get("TOUR_API_SERVICE_KEY", ""))

    missing = []
    if not gemini_key:
        missing.append("GEMINI_API_KEY")
    if require_kakao and not kakao_key:
        missing.append("KAKAO_REST_API_KEY")

    if missing:
        print("=" * 60)
        print("[오류] 다음 API 키가 설정되지 않았습니다:")
        for key_name in missing:
            print(f"  - {key_name}")
        print()
        print("[설정 방법]")
        print("  1. 개발: 프로젝트 .env 에 제공자 키를 넣습니다.")
        print("  2. 평가용 exe: 키 서버를 띄운 뒤 KEY_SERVER_URL / KEY_SERVER_TOKEN 만 사용합니다.")
        print("     python key_server.py")
        print('     travel_planner.exe --key-server http://HOST:8787/keys --key-token TOKEN')
        print()
        print("[키 발급 위치]")
        print("  - Gemini: https://aistudio.google.com/apikey")
        print("  - Kakao:  https://developers.kakao.com/ → 내 애플리케이션 → REST API 키")
        print("  - TMAP(선택): https://openapi.sk.com/ → 앱 키(appKey)")
        print("  - TourAPI(선택): 공공데이터포털 한국관광공사 국문 관광정보 서비스")
        print("=" * 60)
        return None

    return gemini_key, kakao_key, tmap_key, tour_key


def ensure_results_dir():
    """results/ 폴더가 없으면 생성한다."""
    return results_dir()


def save_raw_data(
    date_str,
    recommendation,
    restaurants,
    errors,
    model=None,
    transit_legs=None,
    tour_places=None,
):
    """
    원본 데이터를 JSON 파일로 저장한다.
    """
    ensure_results_dir()

    data = {
        "date": date_str,
        "model": model,
        "recommendation": recommendation,
        "restaurants": restaurants,
        "tour_places": tour_places or {"attractions": [], "stays": []},
        "transit_legs": transit_legs or [],
        "errors": errors,
    }

    filepath = os.path.join(results_dir(), f"{date_str}_raw_data.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath


def save_report(date_str, report_md):
    """
    최종 여행 리포트를 Markdown 파일로 저장한다.

    Args:
        date_str: 여행 날짜 (YYYY-MM-DD)
        report_md: Markdown 형식의 리포트 문자열

    Returns:
        저장된 파일 경로
    """
    ensure_results_dir()

    filepath = os.path.join(results_dir(), f"{date_str}_travel_plan.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_md)

    return filepath


def load_cached_data(date_str):
    """
    캐시된 원본 데이터가 있으면 로드한다. (보너스: 결과 캐싱)

    Args:
        date_str: 여행 날짜 (YYYY-MM-DD)

    Returns:
        캐시된 데이터 dict 또는 None
    """
    filepath = os.path.join(results_dir(), f"{date_str}_raw_data.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def add_error(errors, step, error_type, message):
    """
    오류 목록에 오류를 추가한다.

    Args:
        errors: 오류 리스트 (수정됨)
        step: 오류 발생 단계 (예: "llm_recommendation", "place_search", "llm_report")
        error_type: 오류 유형 (예: "AUTH_ERROR", "NETWORK_ERROR", "PARSE_ERROR", "EMPTY_RESULT")
        message: 구체적 오류 메시지
    """
    errors.append({
        "step": step,
        "type": error_type,
        "message": message,
    })
