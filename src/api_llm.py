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


REQUIRED_RECOMMENDATION_KEYS = ("recommended_city", "weather", "events", "reason")


def recommendation_schema_error(data):
    """1차 JSON에 필수 4키가 있고 값이 비어 있지 않은지 검사한다. 문제 없으면 None."""
    if not isinstance(data, dict):
        return "응답이 JSON 객체가 아닙니다."
    missing = [key for key in REQUIRED_RECOMMENDATION_KEYS if key not in data]
    if missing:
        return "필수 키 누락: {0}".format(", ".join(missing))
    city = data.get("recommended_city")
    weather = data.get("weather")
    reason = data.get("reason")
    events = data.get("events")
    if not isinstance(city, str) or not city.strip():
        return "recommended_city 가 비어 있습니다."
    if not isinstance(weather, str) or not weather.strip():
        return "weather 가 비어 있습니다."
    if not isinstance(reason, str) or not reason.strip():
        return "reason 가 비어 있습니다."
    if not isinstance(events, list) or not 1 <= len(events) <= 3:
        return "events 는 문자열 1~3개 배열이어야 합니다."
    if not all(isinstance(item, str) and item.strip() for item in events):
        return "events 항목이 빈 문자열이거나 문자열이 아닙니다."
    return None


def get_recommendation(api_key, model_name, date_str, errors):
    """
    1단계: LLM에게 여행 날짜를 주고 추천 도시 정보를 JSON으로 받는다.

    Args:
        api_key: Gemini API 키
        model_name: 사용할 모델 이름
        date_str: 여행 날짜 (YYYY-MM-DD)
        errors: 오류 리스트 (수정됨)

    Returns:
        추천 정보 dict. 실패 시 None.
    """
    prompt = f"""당신은 한국 국내 여행 전문가입니다.
사용자가 여행을 계획하는 날짜는 {date_str} 입니다.

이 시기에 여행하기 좋은 국내 도시를 1곳 추천하고,
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
            if not text:
                raise ValueError("Gemini 응답 본문이 비어 있습니다.")
            recommendation = json.loads(text)
            schema_error = recommendation_schema_error(recommendation)
            if schema_error:
                raise ValueError(schema_error)
            recommendation["recommended_city"] = recommendation["recommended_city"].strip()
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
                prompt += (
                    "\n\n이전 응답 오류: {0}\n"
                    "필수 키만 다시 JSON으로 출력하세요: "
                    "recommended_city, weather, events, reason. "
                    "다른 키와 설명 텍스트는 넣지 마세요."
                ).format(e)
                continue
            else:
                add_error(errors, "llm_recommendation", "PARSE_ERROR",
                          f"응답 구조 오류 (재시도 후에도 실패): {e}")
                return None

    return None


ALLOWED_REPORT_HEADINGS = (
    "추천 지역",
    "추천 이유",
    "날씨 요약",
    "행사/축제",
    "맛집 추천",
    "1일 일정 제안",
    "오류 요약",
)


def format_restaurants_md(restaurants):
    """맛집 절은 검색 결과로 고정한다. 주소는 한 줄로 두어 메모장에서도 클릭된다."""
    from api_map import kakao_place_url

    if not restaurants:
        return "데이터 없음"
    lines = []
    for item in restaurants:
        name = item.get("name") or "이름 없음"
        address = item.get("address") or ""
        category = item.get("category") or ""
        url = kakao_place_url(item.get("url"))
        extra = []
        if category:
            extra.append(category)
        if address:
            extra.append(address)
        suffix = " ({0})".format(", ".join(extra)) if extra else ""
        lines.append("- **{0}**{1}".format(name, suffix))
        if url:
            lines.append("  {0}".format(url))
        else:
            lines.append("  링크 없음")
    return "\n".join(lines)


def keep_allowed_sections(report_md, allowed=ALLOWED_REPORT_HEADINGS):
    """모델이 넣은 관광지·숙소 등 과제 밖 제목을 뺀다."""
    lines = (report_md or "").splitlines()
    out = []
    keep = True
    for line in lines:
        if line.startswith("## "):
            keep = line[3:].strip() in allowed
        if keep:
            out.append(line)
    return "\n".join(out).rstrip() + "\n"


def replace_md_section(report_md, heading, body):
    """'## 제목' 절만 갈아끼운다. 없으면 오류 요약 앞에 붙인다."""
    import re

    text = report_md or ""
    pattern = r"(## {0}\s*\n)(.*?)(?=\n## |\Z)".format(re.escape(heading))

    def repl(match):
        return match.group(1) + body + "\n"

    new_text, count = re.subn(pattern, repl, text, count=1, flags=re.S)
    if count:
        return new_text
    marker = "\n## 오류 요약"
    block = "\n## {0}\n{1}\n".format(heading, body)
    if marker in text:
        return text.replace(marker, block + marker, 1)
    return text.rstrip() + block


def generate_report(
    api_key,
    model_name,
    date_str,
    recommendation,
    restaurants,
    errors,
    transit_legs=None,
    tour_places=None,
):
    """
    최종 Markdown 리포트를 생성한다.
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

    extra_note = ""
    if tour_places and any(tour_places.get(key) for key in ("attractions", "stays", "related", "crowd")):
        extra_note += f"\n추가 관광 데이터(일정에만 반영, 별도 절 만들지 말 것):\n{tour_json}\n"
    if transit_legs:
        extra_note += f"\n추가 이동 데이터(일정에만 반영, 별도 절 만들지 말 것):\n{transit_json}\n"

    prompt = f"""당신은 한국 국내 여행 가이드입니다.
아래 데이터를 기반으로 여행 리포트를 Markdown 형식으로 작성하세요.

여행 날짜: {date_str}

1차 추천 정보:
{recommendation_json}

맛집 목록:
{restaurants_json}
{extra_note}
오류 요약:
{errors_text}

아래 절만 사용하세요. 다른 제목을 추가하지 마세요. Markdown만 출력하세요.

# {date_str} 국내 여행 추천 리포트

## 추천 지역
## 추천 이유
## 날씨 요약
## 행사/축제
## 맛집 추천
(맛집 데이터가 없으면 "데이터 없음")
## 1일 일정 제안
(오전/오후/저녁)
## 오류 요약
(없으면 "없음")"""

    try:
        report = _call_gemini(api_key, model_name, prompt, response_json=False)
        if report:
            report = keep_allowed_sections(report)
            return replace_md_section(
                report, "맛집 추천", format_restaurants_md(restaurants)
            )

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

    restaurants_str = format_restaurants_md(restaurants)

    if errors:
        errors_str = "\n".join(
            f"- [{e['step']}] {e['type']}: {e['message']}" for e in errors
        )
    else:
        errors_str = "없음"

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

## 1일 일정 제안
- 오전: {city} 주요 관광지 방문
- 오후: 맛집 탐방 및 자유 시간
- 저녁: 야경 감상 또는 지역 특색 체험

## 오류 요약
{errors_str}
"""
