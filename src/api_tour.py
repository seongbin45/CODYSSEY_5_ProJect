"""
한국관광공사 데이터랩 3종 (선택)

- 기초지자체 중심 관광지: LocgoHubTarService1
- 관광지별 연관 관광지: TarRlteTarService1
- 관광지 집중률 예측: TatsCnctrRateService

키가 없거나 실패해도 프로그램은 중단하지 않는다.
"""

from datetime import datetime
from urllib.parse import unquote

import requests

from utils import add_error

HUB_URL = "https://apis.data.go.kr/B551011/LocgoHubTarService1/areaBasedList1"
RELATED_URL = "https://apis.data.go.kr/B551011/TarRlteTarService1/areaBasedList1"
CROWD_URL = "https://apis.data.go.kr/B551011/TatsCnctrRateService/tatsCnctrRatedList"
KOR_SEARCH_URL = "https://apis.data.go.kr/B551011/KorService2/searchKeyword2"

CONTENT_ATTRACTION = "12"
CONTENT_STAY = "32"

# 주요 여행지 -> (시도코드, 시군구코드). 법정동 코드 체계.
CITY_CODES = {
    "서울": ("11", "11110"),
    "종로": ("11", "11110"),
    "부산": ("26", "26350"),
    "해운대": ("26", "26350"),
    "대구": ("27", "27110"),
    "인천": ("28", "28110"),
    "광주": ("29", "29110"),
    "대전": ("30", "30110"),
    "울산": ("31", "31110"),
    "세종": ("36", "36110"),
    "수원": ("41", "41110"),
    "가평": ("41", "41820"),
    "파주": ("41", "41480"),
    "강릉": ("51", "51150"),
    "속초": ("51", "51210"),
    "춘천": ("51", "51110"),
    "양양": ("51", "51830"),
    "청주": ("43", "43111"),
    "단양": ("43", "43800"),
    "제천": ("43", "43150"),
    "공주": ("44", "44150"),
    "부여": ("44", "44760"),
    "태안": ("44", "44825"),
    "전주": ("52", "52111"),
    "군산": ("52", "52130"),
    "여수": ("46", "46130"),
    "순천": ("46", "46150"),
    "목포": ("46", "46110"),
    "담양": ("46", "46710"),
    "경주": ("47", "47130"),
    "안동": ("47", "47170"),
    "포항": ("47", "47111"),
    "통영": ("48", "48220"),
    "거제": ("48", "48310"),
    "제주": ("50", "50110"),
    "제주시": ("50", "50110"),
    "서귀포": ("50", "50130"),
}


def resolve_region(city_name):
    text = (city_name or "").replace(" ", "")
    for key, codes in CITY_CODES.items():
        if key in text:
            return {"name": key, "area_cd": codes[0], "signgu_cd": codes[1]}
    return None


def _as_item_list(items):
    if not items:
        return []
    if isinstance(items, list):
        return items
    if isinstance(items, dict):
        inner = items.get("item")
        if isinstance(inner, list):
            return inner
        if isinstance(inner, dict):
            return [inner]
        if items.get("title") or items.get("hubTatsNm") or items.get("tAtsNm"):
            return [items]
    return []


def _tour_get(url, service_key, extra, errors, label, record_error=True):
    params = {
        "serviceKey": unquote(service_key),
        "numOfRows": extra.get("numOfRows", 20),
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "TravelPlanner",
        "_type": "json",
    }
    params.update({k: v for k, v in extra.items() if k != "numOfRows"})
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code in (401, 403):
            if record_error:
                add_error(errors, label, "AUTH_ERROR", f"{label} 인증 실패 HTTP {response.status_code}")
            return []
        response.raise_for_status()
        payload = response.json()

        gateway = payload.get("OpenAPI_ServiceResponse") or {}
        if gateway:
            header = gateway.get("cmmMsgHeader") or {}
            if record_error:
                add_error(
                    errors, label, "API_ERROR",
                    f"{label} {header.get('returnReasonCode')} {header.get('returnAuthMsg')}",
                )
            return []

        header = (payload.get("response") or {}).get("header") or {}
        code = str(header.get("resultCode") or payload.get("resultCode") or "")
        if code not in ("0000", "0", ""):
            if record_error:
                add_error(
                    errors, label, "API_ERROR",
                    f"{label} resultCode={code} {header.get('resultMsg') or payload.get('resultMsg')}",
                )
            return []

        body = (payload.get("response") or {}).get("body") or {}
        return _as_item_list(body.get("items"))
    except ValueError as exc:
        add_error(errors, label, "PARSE_ERROR", f"{label} JSON 파싱 실패: {exc}")
        return []
    except requests.exceptions.RequestException as exc:
        add_error(errors, label, "NETWORK_ERROR", f"{label} 오류: {exc}")
        return []


def _iter_base_ym(date_str):
    current = datetime.strptime(date_str, "%Y-%m-%d")
    year, month = current.year, current.month
    for _ in range(24):
        yield f"{year:04d}{month:02d}"
        month -= 1
        if month == 0:
            month = 12
            year -= 1


def fetch_hubs(service_key, area_cd, signgu_cd, date_str, errors):
    for base_ym in _iter_base_ym(date_str):
        items = _tour_get(
            HUB_URL,
            service_key,
            {"areaCd": area_cd, "signguCd": signgu_cd, "baseYm": base_ym, "numOfRows": 15},
            errors,
            "tour_hub",
            record_error=False,
        )
        if items:
            hubs = []
            for item in items:
                name = item.get("hubTatsNm") or ""
                if "공항" in name:
                    continue
                hubs.append({
                    "name": name,
                    "rank": item.get("hubRank"),
                    "category": item.get("hubCtgryMclsNm") or item.get("hubCtgryLclsNm") or "",
                    "x": item.get("mapX") or "",
                    "y": item.get("mapY") or "",
                    "area": item.get("signguNm") or "",
                    "base_ym": item.get("baseYm") or base_ym,
                })
                if len(hubs) == 5:
                    break
            if hubs:
                return hubs, base_ym
    add_error(errors, "tour_hub", "EMPTY_RESULT", "중심 관광지 0건")
    return [], None


def fetch_related(service_key, area_cd, signgu_cd, base_ym, errors):
    if not base_ym:
        return []
    items = _tour_get(
        RELATED_URL,
        service_key,
        {"areaCd": area_cd, "signguCd": signgu_cd, "baseYm": base_ym, "numOfRows": 30},
        errors,
        "tour_related",
    )
    related = []
    seen = set()
    for item in items:
        name = item.get("rlteTatsNm") or ""
        if not name or "공항" in name or name in seen:
            continue
        seen.add(name)
        related.append({
            "from": item.get("tAtsNm") or "",
            "name": name,
            "category": item.get("rlteCtgryLclsNm") or "",
            "detail": item.get("rlteCtgrySclsNm") or item.get("rlteCtgryMclsNm") or "",
            "rank": item.get("rlteRank"),
        })
        if len(related) == 8:
            break
    if not related:
        add_error(errors, "tour_related", "EMPTY_RESULT", "연관 관광지 0건")
    return related


def _pick_crowd_item(items, date_str):
    target = date_str.replace("-", "")
    exact = [item for item in items if item.get("baseYmd") == target]
    pool = exact or items
    if not pool:
        return None
    pool = sorted(pool, key=lambda item: abs(int(item.get("baseYmd") or "0") - int(target)))
    return pool[0]


def fetch_kor_keyword(service_key, keyword, content_type_id, errors, rows=5):
    items = _tour_get(
        KOR_SEARCH_URL,
        service_key,
        {
            "keyword": keyword,
            "contentTypeId": content_type_id,
            "arrange": "C",
            "numOfRows": rows,
        },
        errors,
        "tour_official",
    )
    places = []
    for item in items:
        places.append({
            "name": item.get("title") or "",
            "address": item.get("addr1") or "",
            "tel": item.get("tel") or "",
            "image": item.get("firstimage") or "",
            "x": item.get("mapx") or "",
            "y": item.get("mapy") or "",
            "content_id": item.get("contentid") or "",
        })
    return places


def fetch_crowd(service_key, area_cd, signgu_cd, place_names, date_str, errors):
    crowd = []
    for name in place_names[:5]:
        items = _tour_get(
            CROWD_URL,
            service_key,
            {"areaCd": area_cd, "signguCd": signgu_cd, "tAtsNm": name, "numOfRows": 40},
            errors,
            "tour_crowd",
        )
        picked = _pick_crowd_item(items, date_str)
        if not picked:
            continue
        crowd.append({
            "name": picked.get("tAtsNm") or name,
            "date": picked.get("baseYmd") or "",
            "rate": picked.get("cnctrRate") or "",
        })
    if place_names and not crowd:
        add_error(errors, "tour_crowd", "EMPTY_RESULT", "집중률 데이터 없음")
    return crowd


def search_official_places(service_key, city_name, date_str, errors):
    """
    추천 도시 기준으로 중심 관광지, 연관 관광지, 집중률을 묶는다.
    """
    empty = {
        "region": None,
        "attractions": [],
        "stays": [],
        "related": [],
        "crowd": [],
        "official_attractions": [],
        "official_stays": [],
    }
    if not service_key:
        return empty

    official_attractions = fetch_kor_keyword(
        service_key, city_name, CONTENT_ATTRACTION, errors, rows=5
    )
    official_stays = fetch_kor_keyword(
        service_key, city_name, CONTENT_STAY, errors, rows=3
    )

    region = resolve_region(city_name)
    hubs, related, crowd, base_ym = [], [], [], None
    if region:
        hubs, base_ym = fetch_hubs(
            service_key, region["area_cd"], region["signgu_cd"], date_str, errors
        )
        related = fetch_related(
            service_key, region["area_cd"], region["signgu_cd"], base_ym, errors
        )
        crowd = fetch_crowd(
            service_key,
            region["area_cd"],
            region["signgu_cd"],
            [item["name"] for item in hubs],
            date_str,
            errors,
        )
        region = {**region, "base_ym": base_ym}
    else:
        add_error(
            errors, "tour_hub", "EMPTY_RESULT",
            f"데이터랩 지역코드를 찾지 못함: {city_name}",
        )

    return {
        "region": region,
        "attractions": hubs or official_attractions,
        "stays": official_stays,
        "related": related,
        "crowd": crowd,
        "official_attractions": official_attractions,
        "official_stays": official_stays,
    }
