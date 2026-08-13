"""
Kakao Local API 모듈

Kakao Local API를 requests로 직접 호출한다.
- 맛집 검색: 특정 지역의 맛집 5곳을 검색하여 리스트로 반환
"""

import requests

from utils import add_error

# Kakao Local Keyword Search API 엔드포인트
KAKAO_API_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"


def _as_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_restaurant(doc):
    """
    Kakao API 응답 1건을 과제에서 요구하는 형식으로 변환한다.
    """
    return {
        "name": doc.get("place_name", ""),
        "address": doc.get("road_address_name") or doc.get("address_name", ""),
        "category": doc.get("category_name", ""),
        "url": doc.get("place_url", ""),
        "x": _as_number(doc.get("x")),
        "y": _as_number(doc.get("y")),
    }


def search_restaurants(api_key, city_name, errors):
    """
    2단계: 지도/장소 검색 API로 해당 지역의 맛집을 검색한다.

    Args:
        api_key: Kakao REST API 키
        city_name: 검색할 도시/지역 이름 (예: "제주")
        errors: 오류 리스트 (수정됨)

    Returns:
        맛집 정보 dict의 리스트. 실패하거나 결과가 없으면 빈 리스트 반환.
    """
    headers = {
        "Authorization": f"KakaoAK {api_key}"
    }

    params = {
        "query": f"{city_name} 맛집",
        "category_group_code": "FD6",  # 음식점 카테고리
        "size": 5                      # 권장 5곳
    }

    try:
        response = requests.get(KAKAO_API_URL, headers=headers, params=params, timeout=30)
        
        if response.status_code in (401, 403):
            add_error(errors, "place_search", "AUTH_ERROR", 
                      f"Kakao API 인증 실패 (상태 코드: {response.status_code})")
            return []
            
        response.raise_for_status()
        
        result = response.json()
        documents = result.get("documents", [])
        
        if not documents:
            add_error(errors, "place_search", "EMPTY_RESULT", 
                      f"'{params['query']}' 검색 결과 0건")
            return []
            
        restaurants = [_parse_restaurant(doc) for doc in documents]
        return restaurants

    except requests.exceptions.RequestException as e:
        add_error(errors, "place_search", "NETWORK_ERROR", 
                  f"Kakao API 네트워크/HTTP 오류: {e}")
        return []
    except ValueError as e:
        add_error(errors, "place_search", "PARSE_ERROR", 
                  f"Kakao API 응답 파싱 오류: {e}")
        return []
