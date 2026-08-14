"""
Gemini LLM API 모듈

Google Gemini REST API를 requests로 직접 호출한다.
- 1차 추천: 여행 날짜를 받아 추천 도시 JSON을 생성
- 최종 리포트: 추천 정보 + 맛집 목록을 받아 Markdown 리포트를 생성
"""

import json
import os
import time
from datetime import datetime, timezone

import requests

from utils import add_error, ensure_results_dir, results_dir


# Gemini REST API 엔드포인트 기본 URL
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
def _compat_path():
    return os.path.join(results_dir(), "gemini_model_compat.json")


def _gemini_headers(api_key):
    """키는 쿼리스트링이 아니라 헤더로 보낸다. 예외/로그에 키가 섞이지 않게 한다."""
    return {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }


def model_id(model):
    """models/gemini-2.5-flash -> gemini-2.5-flash"""
    if isinstance(model, dict):
        name = model.get("name", "")
    else:
        name = str(model)
    if name.startswith("models/"):
        return name[len("models/"):]
    return name


# generateContent가 있어도 이 CLI의 JSON/Markdown 호출과 안 맞는 모델
_UNUSABLE_NAME_PARTS = (
    "antigravity",
    "deep-research",
    "computer-use",
    "robotics",
    "tts",
    "image",
    "imagen",
    "veo",
    "live",
    "embedding",
    "lyria",
    "omni",
    "nano-banana",
    "aqa",
)


def supports_generate_content(model):
    methods = model.get("supportedGenerationMethods") or []
    return "generateContent" in methods


def is_text_generation_model(model):
    """
    이름 기반 1차 추정. 실제 허용 여부는 교차검증 결과(is_allowed_model)를 우선한다.
    """
    if not supports_generate_content(model):
        return False
    name = model_id(model).lower()
    if any(part in name for part in _UNUSABLE_NAME_PARTS):
        return False
    return name.startswith("gemini-") or name.startswith("gemma-")


def load_model_compat():
    path = _compat_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def save_model_compat(report):
    ensure_results_dir()
    path = _compat_path()
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    return path


def compat_row_for(model):
    report = load_model_compat()
    if not report:
        return None
    mid = model_id(model)
    for row in report.get("models") or []:
        if row.get("id") == mid:
            return row
    return None


def is_allowed_model(model):
    """
    교차검증 파일이 있으면 실측 결과를 쓰고, 없으면 이름 휴리스틱을 쓴다.
    """
    row = compat_row_for(model)
    if row is not None:
        return bool(row.get("usable"))
    return is_text_generation_model(model)


def list_models(api_key):
    """
    이 API 키가 조회할 수 있는 모델 전체를 페이지를 넘겨 가져온다.

    Returns:
        모델 dict 리스트. 네트워크/인증 오류면 예외를 그대로 올린다.
    """
    models = []
    page_token = None

    while True:
        params = {"pageSize": 100}
        if page_token:
            params["pageToken"] = page_token

        response = requests.get(
            f"{GEMINI_API_BASE_URL}/models",
            headers=_gemini_headers(api_key),
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        models.extend(payload.get("models") or [])
        page_token = payload.get("nextPageToken")
        if not page_token:
            break

    models.sort(
        key=lambda m: (
            0 if is_allowed_model(m) else 1,
            model_id(m).lower(),
        )
    )
    return models


def find_model(models, query):
    """번호가 아닌 이름(짧은 ID 또는 models/...)으로 목록에서 찾는다."""
    if not query:
        return None
    needle = query.strip()
    needle_id = model_id(needle)
    for item in models:
        if needle == item.get("name") or needle_id == model_id(item):
            return item
    return None


def format_model_catalog(models):
    """화면에 뿌릴 모델 목록 문자열."""
    lines = []
    usable = 0
    for index, item in enumerate(models, 1):
        methods = item.get("supportedGenerationMethods") or []
        method_label = ", ".join(methods) if methods else "없음"
        display = item.get("displayName") or ""
        row = compat_row_for(item)
        if row is None:
            usable_mark = (
                "추정 사용 가능" if is_text_generation_model(item) else "추정 사용 불가"
            )
        elif row.get("usable"):
            usable_mark = "검증 통과"
        else:
            usable_mark = "검증 실패"
        extra = f"  {display}" if display else ""
        lines.append(
            f"  {index}. {model_id(item):<36} [{usable_mark}]  ({method_label}){extra}"
        )
        if is_allowed_model(item):
            usable += 1
    header = (
        f"이 API 키가 조회한 모델 {len(models)}개 "
        f"(이 프로그램에서 쓸 수 있는 모델: {usable}개)"
    )
    return header, "\n".join(lines)


def print_model_catalog(models):
    header, body = format_model_catalog(models)
    print(header)
    print(body)


def resolve_model_choice(models, raw_choice):
    """
    사용자 입력(번호 또는 모델 이름)을 모델 dict로 바꾼다.

    Returns:
        (model_dict | None, error_message | None)
    """
    choice = (raw_choice or "").strip()
    if not choice:
        return None, "번호 또는 모델 이름을 입력하세요."

    if choice.isdigit():
        index = int(choice) - 1
        if 0 <= index < len(models):
            selected = models[index]
        else:
            return None, f"1부터 {len(models)} 사이의 번호를 입력하세요."
    else:
        selected = find_model(models, choice)
        if selected is None:
            return None, f"목록에 없는 모델입니다: {choice}"

    if not is_allowed_model(selected):
        row = compat_row_for(selected)
        if row and not row.get("usable"):
            reason = row.get("error") or "교차검증 실패"
            return None, (
                f"'{model_id(selected)}' 는 교차검증에서 탈락했습니다: {reason}"
            )
        return None, (
            f"'{model_id(selected)}' 는 이 프로그램의 텍스트/JSON 호출에 맞지 않습니다. "
            "gemini-2.5-flash 같은 일반 텍스트 모델을 고르거나 --verify-models 로 재검증하세요."
        )
    return selected, None


def select_model(api_key, preferred=None):
    """
    키로 모델 목록을 받은 뒤 사용할 모델을 정한다.

    preferred가 있으면 그 이름이 목록에 있고 generateContent를 지원하는지 확인한다.
    없으면 목록을 보여 주고 사용자가 고른다.

    Returns:
        선택한 모델의 짧은 ID (예: gemini-2.5-flash)

    Raises:
        RuntimeError: 목록 조회 실패, 선택 불능, 입력이 끝났는데 선택이 안 된 경우
    """
    try:
        models = list_models(api_key)
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        raise RuntimeError(
            f"모델 목록 조회 실패 (HTTP {status}). GEMINI_API_KEY와 권한을 확인하세요."
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"모델 목록 조회 실패: {exc}") from exc

    if not models:
        raise RuntimeError("이 API 키로 조회된 모델이 없습니다.")

    if preferred:
        selected, error = resolve_model_choice(models, preferred)
        if error:
            print_model_catalog(models)
            raise RuntimeError(error)
        return model_id(selected)

    print()
    print_model_catalog(models)
    print()
    print("번호 또는 모델 이름을 입력하세요. gemini-2.5-flash 같은 일반 텍스트 모델만 사용합니다.")

    while True:
        try:
            raw = input("> ")
        except EOFError as exc:
            raise RuntimeError(
                "모델이 선택되지 않았습니다. --model 로 모델 ID를 넘기세요."
            ) from exc

        selected, error = resolve_model_choice(models, raw)
        if error:
            print(f"  - {error}")
            continue
        return model_id(selected)


def get_available_models(api_key):
    """하위 호환: generateContent 모델의 짧은 ID 리스트."""
    try:
        return [model_id(m) for m in list_models(api_key) if is_allowed_model(m)]
    except requests.exceptions.RequestException as exc:
        print(f"[오류] 모델 목록 조회 실패: {exc}")
        return []


def _call_gemini(api_key, model_name, prompt, response_json=False, timeout=60):
    """
    Gemini API를 호출한다. (POST)

    Args:
        api_key: Gemini API 키
        model_name: 사용할 모델 이름 (예: 'gemini-2.5-flash')
        prompt: 프롬프트 텍스트
        response_json: True이면 JSON 형식 응답을 강제

    Returns:
        응답 텍스트 문자열. 실패 시 None.

    Raises:
        requests.exceptions.RequestException: 네트워크/HTTP 오류
    """
    resource = model_name if model_name.startswith("models/") else f"models/{model_name}"
    url = f"{GEMINI_API_BASE_URL}/{resource}:generateContent"

    body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
    }

    # JSON 출력 강제 옵션
    if response_json:
        body["generationConfig"] = {
            "responseMimeType": "application/json"
        }

    response = requests.post(
        url,
        headers=_gemini_headers(api_key),
        json=body,
        timeout=timeout,
    )
    if not response.ok:
        detail = ""
        try:
            err = response.json().get("error") or {}
            detail = err.get("message") or ""
        except ValueError:
            detail = (response.text or "")[:200]
        raise requests.exceptions.HTTPError(
            f"HTTP {response.status_code} model={model_id(model_name)}"
            + (f" ({detail})" if detail else ""),
            response=response,
        )

    result = response.json()

    # 응답에서 텍스트 추출
    text = result["candidates"][0]["content"]["parts"][0]["text"]
    return text


def _probe_once(api_key, model_name, response_json):
    if response_json:
        prompt = 'Return JSON only: {"ok": true}'
    else:
        prompt = "Reply with the single word OK."
    text = _call_gemini(
        api_key, model_name, prompt, response_json=response_json, timeout=25
    )
    if response_json:
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("JSON 응답이 객체가 아님")
    elif "OK" not in (text or "").upper():
        raise ValueError(f"예상과 다른 텍스트: {(text or '')[:80]}")
    return (text or "")[:80]


def probe_model(api_key, model):
    """
    한 모델을 이 프로그램과 같은 방식(텍스트 + JSON)으로 호출해 본다.
    """
    mid = model_id(model)
    methods = model.get("supportedGenerationMethods") or []
    row = {
        "id": mid,
        "display_name": model.get("displayName") or "",
        "methods": methods,
        "heuristic": is_text_generation_model(model),
        "text_ok": False,
        "json_ok": False,
        "usable": False,
        "skipped": False,
        "error": "",
    }
    if not supports_generate_content(model):
        row["skipped"] = True
        row["error"] = "generateContent 미지원"
        return row

    errors = []
    try:
        _probe_once(api_key, mid, False)
        row["text_ok"] = True
    except Exception as exc:
        errors.append(f"text: {exc}")

    time.sleep(0.2)
    try:
        _probe_once(api_key, mid, True)
        row["json_ok"] = True
    except Exception as exc:
        errors.append(f"json: {exc}")

    row["usable"] = bool(row["text_ok"] and row["json_ok"])
    row["error"] = " | ".join(errors)
    return row


def verify_all_models(api_key):
    """
    키가 조회한 모든 모델을 하나씩 교차검증하고 결과를 저장한다.
    """
    models = list_models(api_key)
    rows = []
    total = len(models)
    print(f"[검증] 모델 {total}개를 하나씩 호출합니다. (텍스트 + JSON)")

    for index, item in enumerate(models, 1):
        mid = model_id(item)
        print(f"[{index}/{total}] {mid} ...", flush=True)
        row = probe_model(api_key, item)
        if row["skipped"]:
            print(f"         skip ({row['error']})")
        elif row["usable"]:
            print("         pass (text+json)")
        else:
            print(f"         fail ({row['error'][:160]})")
        rows.append(row)
        time.sleep(0.3)

    passed = [row for row in rows if row.get("usable")]
    failed = [row for row in rows if not row.get("usable") and not row.get("skipped")]
    skipped = [row for row in rows if row.get("skipped")]
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "passed": len(passed),
        "failed": len(failed),
        "skipped": len(skipped),
        "models": rows,
    }
    path = save_model_compat(report)
    print()
    print(f"[검증] 통과 {len(passed)} / 실패 {len(failed)} / 생략 {len(skipped)}")
    if passed:
        print("[검증] 사용 가능:")
        for row in passed:
            print(f"  - {row['id']}")
    print(f"[검증] 결과 저장: {path}")
    return report


def get_recommendation(api_key, model_name, date_str, errors, city=None):
    """
    1단계: LLM에게 여행 날짜를 주고 추천 도시 정보를 JSON으로 받는다.
    city 가 있으면 그 도시를 고정하고 날씨/행사/이유만 채운다.
    """
    city = (city or "").strip()
    if city:
        intro = (
            f"사용자가 여행을 계획하는 날짜는 {date_str} 입니다.\n"
            f"목적지는 사용자가 고른 '{city}' 입니다. "
            f"recommended_city 는 반드시 '{city}' 로 두고, "
            "그 도시의 날씨·행사·이유만 채우세요. 다른 도시로 바꾸지 마세요."
        )
    else:
        intro = (
            f"사용자가 여행을 계획하는 날짜는 {date_str} 입니다.\n"
            "이 시기에 여행하기 좋은 국내 도시를 1곳 추천하세요."
        )

    prompt = f"""당신은 한국 국내 여행 전문가입니다.
{intro}

아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

{{
  "recommended_city": "도시명",
  "weather": "해당 시기의 일반적 날씨 요약 (1~2문장)",
  "events": ["행사/축제 후보 1", "행사/축제 후보 2"],
  "reason": "추천 근거 2~4문장"
}}

규칙:
- recommended_city는 한국 도시명 (예: 제주, 강릉, 부산, 경주, 여수 등)
- events는 1~3개의 문자열 배열
- reason은 2~4문장의 문자열
- 반드시 위 JSON 형식으로만 출력하세요."""

    # 1차 시도
    for attempt in range(2):  # 최대 2회 (1차 + 재시도 1회)
        try:
            text = _call_gemini(api_key, model_name, prompt, response_json=True)
            recommendation = json.loads(text)

            # 필수 키 검증
            required_keys = ["recommended_city", "weather", "events", "reason"]
            for key in required_keys:
                if key not in recommendation:
                    raise ValueError(f"필수 키 누락: {key}")

            return recommendation

        except json.JSONDecodeError as e:
            if attempt == 0:
                print(f"  - JSON 파싱 실패, 재시도 중... ({e})")
                # 재시도 시 프롬프트 보강
                prompt += "\n\n중요: 반드시 올바른 JSON만 출력하세요. 마크다운이나 설명 텍스트를 포함하지 마세요."
                continue
            else:
                add_error(errors, "llm_recommendation", "PARSE_ERROR",
                          f"JSON 파싱 실패 (재시도 후에도 실패): {e}")
                return None

        except requests.exceptions.HTTPError as e:
            add_error(errors, "llm_recommendation", "API_ERROR",
                      f"Gemini API HTTP 오류: {e}")
            return None

        except requests.exceptions.RequestException as e:
            add_error(errors, "llm_recommendation", "NETWORK_ERROR",
                      f"Gemini API 네트워크 오류: {e}")
            return None

        except (KeyError, IndexError, ValueError) as e:
            if attempt == 0:
                print(f"  - 응답 구조 오류, 재시도 중... ({e})")
                continue
            else:
                add_error(errors, "llm_recommendation", "PARSE_ERROR",
                          f"응답 구조 오류 (재시도 후에도 실패): {e}")
                return None

    return None


def generate_report(
    api_key,
    model_name,
    date_str,
    recommendation,
    restaurants,
    errors,
    transit_legs=None,
    tour_places=None,
    end_date=None,
    days=1,
):
    """
    최종 Markdown 리포트를 생성한다.
    days>1 이면 N일 일정을 쓴다. 과제 최소는 1일이다.
    """
    recommendation_json = json.dumps(recommendation, ensure_ascii=False, indent=2)
    restaurants_json = json.dumps(restaurants, ensure_ascii=False, indent=2)
    transit_json = json.dumps(transit_legs or [], ensure_ascii=False, indent=2)
    tour_json = json.dumps(
        tour_places or {"attractions": [], "stays": []},
        ensure_ascii=False,
        indent=2,
    )

    if errors:
        errors_text = json.dumps(errors, ensure_ascii=False, indent=2)
    else:
        errors_text = "없음"

    days = max(1, int(days or 1))
    end_date = end_date or date_str
    if days <= 1:
        period = f"여행 날짜: {date_str} (당일)"
        schedule_heading = "## 1일 일정 제안\n(오전/오후/저녁 일정 제안. 관광지/맛집/TMAP 이동 정보가 있으면 일정에 반영)"
    else:
        nights = days - 1
        period = f"여행 기간: {date_str} ~ {end_date} ({nights}박 {days}일)"
        schedule_heading = (
            f"## {days}일 일정 제안\n"
            f"(1일차부터 {days}일차까지. 각 날은 오전/오후/저녁. "
            f"1~{nights}일차에는 숙소를 넣고, 마지막 날은 귀가 일정으로 잡으세요.)"
        )

    prompt = f"""당신은 한국 국내 여행 가이드입니다.
아래 데이터를 기반으로 여행 리포트를 Markdown 형식으로 작성하세요.

## 입력 데이터

{period}

1차 추천 정보:
{recommendation_json}

맛집 목록:
{restaurants_json}

TourAPI 데이터(중심 관광지/연관 관광지/집중률, 없을 수 있음):
{tour_json}

TMAP 이동 정보(도보/대중교통, 없을 수 있음):
{transit_json}

오류 요약:
{errors_text}

## 출력 형식

아래 Markdown 구조를 정확히 따르세요. Markdown 텍스트만 출력하세요.

# {date_str} 국내 여행 추천 리포트

## 추천 지역
(추천 도시명과 간단한 소개)

## 추천 이유
(추천 근거 요약)

## 날씨 요약
(해당 시기 날씨 요약)

## 행사/축제
(행사 목록, 불릿 포인트로)

## 맛집 추천
(맛집 목록을 표 또는 리스트로 정리. 맛집 데이터가 없으면 "데이터 없음 (장소 검색 결과 0건)" 표기)

## 관광지
(TourAPI 중심 관광지 또는 공식 관광지가 있으면 목록으로. 없으면 "데이터 없음")

## 숙소
(KorService2 공식 숙소가 있으면 주소와 함께 목록으로. 없으면 "데이터 없음")

## 연관 관광지
(함께 많이 가는 장소가 있으면 목록으로. 없으면 "데이터 없음")

## 혼잡/집중률
(집중률이 있으면 날짜와 함께 표기. 100에 가까울수록 붐빔. 없으면 "데이터 없음")

{schedule_heading}

## 이동 정보
(TMAP 데이터가 있으면 구간별 도보/대중교통을 정리. 없으면 "데이터 없음")

## 오류 요약
(에러가 있으면 표기, 없으면 "없음")"""

    try:
        report = _call_gemini(api_key, model_name, prompt, response_json=False)
        return report

    except requests.exceptions.RequestException as e:
        add_error(errors, "llm_report", "NETWORK_ERROR",
                  f"Gemini API 오류: {e}")

    except (KeyError, IndexError) as e:
        add_error(errors, "llm_report", "PARSE_ERROR",
                  f"Gemini 응답 구조 오류: {e}")

    return _fallback_report(
        date_str, recommendation, restaurants, errors, transit_legs, tour_places
    )


def _fallback_report(
    date_str, recommendation, restaurants, errors, transit_legs=None, tour_places=None
):
    """
    LLM 리포트 생성 실패 시 사용할 기본 템플릿.
    """
    city = recommendation.get("recommended_city", "알 수 없음")
    weather = recommendation.get("weather", "정보 없음")
    events = recommendation.get("events", [])
    reason = recommendation.get("reason", "정보 없음")

    events_str = "\n".join(f"- {e}" for e in events) if events else "- 정보 없음"

    if restaurants:
        restaurant_lines = []
        for r in restaurants:
            restaurant_lines.append(
                f"| {r.get('name', '')} | {r.get('address', '')} | "
                f"{r.get('category', '')} | {r.get('url', '')} |"
            )
        restaurants_str = (
            "| 이름 | 주소 | 카테고리 | URL |\n"
            "|------|------|----------|-----|\n"
            + "\n".join(restaurant_lines)
        )
    else:
        restaurants_str = "데이터 없음 (장소 검색 결과 0건)"

    tour_places = tour_places or {}
    attractions = tour_places.get("attractions") or []
    stays = tour_places.get("stays") or []
    related = tour_places.get("related") or []
    crowd = tour_places.get("crowd") or []
    if attractions:
        attractions_str = "\n".join(
            f"- {p.get('rank', '')}. {p.get('name', '')} ({p.get('category', '')})"
            for p in attractions
        )
    else:
        attractions_str = "데이터 없음"
    if stays:
        stays_str = "\n".join(
            f"- {p.get('name', '')} ({p.get('address', '')})" for p in stays
        )
    else:
        stays_str = "데이터 없음"
    if related:
        related_str = "\n".join(
            f"- {p.get('from', '')} → {p.get('name', '')} ({p.get('category', '')})"
            for p in related
        )
    else:
        related_str = "데이터 없음"
    if crowd:
        crowd_str = "\n".join(
            f"- {p.get('name', '')}: {p.get('date', '')} 집중률 {p.get('rate', '')}"
            for p in crowd
        )
    else:
        crowd_str = "데이터 없음"

    if errors:
        errors_str = "\n".join(
            f"- [{e['step']}] {e['type']}: {e['message']}" for e in errors
        )
    else:
        errors_str = "없음"

    if transit_legs:
        transit_lines = []
        for leg in transit_legs:
            walk = leg.get("walk") or {}
            transit = leg.get("transit") or {}
            walk_txt = (
                f"도보 {walk.get('minutes')}분/{walk.get('distance_m')}m"
                if walk else "도보 정보 없음"
            )
            if transit:
                transit_txt = (
                    f"대중교통 {transit.get('minutes')}분, "
                    f"환승 {transit.get('transfers')}회, "
                    f"요금 {transit.get('fare')}원"
                )
            else:
                transit_txt = "대중교통 정보 없음"
            transit_lines.append(
                f"- {leg.get('from')} → {leg.get('to')}: {walk_txt} / {transit_txt}"
            )
        transit_str = "\n".join(transit_lines)
    else:
        transit_str = "데이터 없음"

    return f"""# {date_str} 국내 여행 추천 리포트

## 추천 지역
{city}

## 추천 이유
{reason}

## 날씨 요약
{weather}

## 행사/축제
{events_str}

## 맛집 추천
{restaurants_str}

## 관광지
{attractions_str}

## 숙소
{stays_str}

## 연관 관광지
{related_str}

## 혼잡/집중률
{crowd_str}

## 1일 일정 제안
- 오전: {city} 주요 관광지 방문
- 오후: 맛집 탐방 및 자유 시간
- 저녁: 야경 감상 또는 지역 특색 체험

## 이동 정보
{transit_str}

## 오류 요약
{errors_str}
"""
