"""
TMAP Open API 모듈 (선택)

Kakao 맛집 좌표를 이어 도보/대중교통 이동 정보를 만든다.
키가 없거나 호출이 실패해도 프로그램은 중단하지 않는다.
"""

from datetime import datetime

import requests

from utils import add_error

TMAP_TRANSIT_URL = "https://apis.openapi.sk.com/transit/routes/sub"
TMAP_WALK_URL = "https://apis.openapi.sk.com/tmap/routes/pedestrian"


def _headers(api_key):
    return {
        "appKey": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _xy(place):
    try:
        x = float(place.get("x"))
        y = float(place.get("y"))
    except (TypeError, ValueError):
        return None
    return x, y


def _minutes(seconds):
    if seconds is None:
        return None
    return max(1, round(int(seconds) / 60))


def get_transit_leg(api_key, start, end, search_dttm, errors):
    """
    두 좌표 사이 대중교통 요약. 실패 시 None.
    POST /transit/routes/sub  (Free TMAP 대중교통)
    """
    body = {
        "startX": str(start[0]),
        "startY": str(start[1]),
        "endX": str(end[0]),
        "endY": str(end[1]),
        "count": 1,
        "format": "json",
        "searchDttm": search_dttm,
    }
    try:
        response = requests.post(
            TMAP_TRANSIT_URL, headers=_headers(api_key), json=body, timeout=30
        )
        if response.status_code in (401, 403):
            add_error(
                errors, "tmap_transit", "AUTH_ERROR",
                f"TMAP 대중교통 인증 실패 (HTTP {response.status_code})",
            )
            return None
        response.raise_for_status()
        itineraries = (
            response.json()
            .get("metaData", {})
            .get("plan", {})
            .get("itineraries") or []
        )
        if not itineraries:
            add_error(errors, "tmap_transit", "EMPTY_RESULT", "대중교통 경로 0건")
            return None
        best = itineraries[0]
        return {
            "minutes": _minutes(best.get("totalTime")),
            "walk_minutes": _minutes(best.get("totalWalkTime") or best.get("walkTime")),
            "transfers": best.get("transferCount"),
            "fare": (best.get("fare") or {}).get("regular", {}).get("totalFare"),
            "distance_m": best.get("totalDistance"),
        }
    except requests.exceptions.RequestException as exc:
        add_error(errors, "tmap_transit", "NETWORK_ERROR", f"TMAP 대중교통 오류: {exc}")
        return None
    except (ValueError, KeyError, TypeError) as exc:
        add_error(errors, "tmap_transit", "PARSE_ERROR", f"TMAP 대중교통 파싱 오류: {exc}")
        return None


def get_walk_leg(api_key, start, end, start_name, end_name, errors):
    """
    두 좌표 사이 도보 요약. 실패 시 None.
    POST /tmap/routes/pedestrian  (Free TMAP)
    """
    body = {
        "startX": start[0],
        "startY": start[1],
        "endX": end[0],
        "endY": end[1],
        "startName": start_name or "출발",
        "endName": end_name or "도착",
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
    }
    try:
        response = requests.post(
            TMAP_WALK_URL,
            headers=_headers(api_key),
            params={"version": "1"},
            json=body,
            timeout=30,
        )
        if response.status_code in (401, 403):
            add_error(
                errors, "tmap_walk", "AUTH_ERROR",
                f"TMAP 도보 인증 실패 (HTTP {response.status_code})",
            )
            return None
        response.raise_for_status()
        features = response.json().get("features") or []
        if not features:
            add_error(errors, "tmap_walk", "EMPTY_RESULT", "도보 경로 0건")
            return None
        props = features[0].get("properties") or {}
        return {
            "minutes": _minutes(props.get("totalTime")),
            "distance_m": props.get("totalDistance"),
        }
    except requests.exceptions.RequestException as exc:
        add_error(errors, "tmap_walk", "NETWORK_ERROR", f"TMAP 도보 오류: {exc}")
        return None
    except (ValueError, KeyError, TypeError) as exc:
        add_error(errors, "tmap_walk", "PARSE_ERROR", f"TMAP 도보 파싱 오류: {exc}")
        return None


def build_travel_legs(api_key, restaurants, date_str, errors):
    """
    좌표가 있는 맛집 앞 3곳을 이어 오전→오후→저녁 이동 구간을 만든다.
    """
    if not api_key:
        return []

    dated = datetime.strptime(date_str, "%Y-%m-%d")
    search_dttm = dated.strftime("%Y%m%d1200")

    stops = []
    for place in restaurants:
        xy = _xy(place)
        if xy:
            stops.append((place.get("name") or "장소", xy))
        if len(stops) == 3:
            break

    if len(stops) < 2:
        return []

    legs = []
    for index in range(len(stops) - 1):
        from_name, from_xy = stops[index]
        to_name, to_xy = stops[index + 1]
        legs.append({
            "from": from_name,
            "to": to_name,
            "walk": get_walk_leg(api_key, from_xy, to_xy, from_name, to_name, errors),
            "transit": get_transit_leg(api_key, from_xy, to_xy, search_dttm, errors),
        })
    return legs
