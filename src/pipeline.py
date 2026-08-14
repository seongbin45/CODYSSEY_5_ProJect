"""
CLI와 FastAPI가 같이 쓰는 여행 추천 파이프라인.
키는 프로세스 환경변수에만 두고 응답에 넣지 않는다.
"""

from datetime import datetime

from utils import (
    validate_date,
    check_api_keys,
    load_cached_data,
    save_raw_data,
    save_report,
    result_stem,
)
from api_llm import (
    is_allowed_model,
    list_models,
    model_id,
    select_model,
    get_recommendation,
    generate_report,
)
from api_map import search_restaurants
from api_tmap import build_travel_legs
from api_tour import search_official_places


class PipelineError(Exception):
    pass


def list_usable_models(gemini_key):
    models = list_models(gemini_key)
    return [model_id(item) for item in models if is_allowed_model(item)]


def trip_days(start_str, end_str):
    start = datetime.strptime(start_str, "%Y-%m-%d")
    end = datetime.strptime(end_str, "%Y-%m-%d")
    return (end - start).days + 1


def run_pipeline(date_str, model_name=None, use_cache=True, city=None, end_date=None):
    if not validate_date(date_str):
        raise PipelineError("시작 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).")

    city = (city or "").strip() or None
    end_date = (end_date or "").strip() or date_str
    if not validate_date(end_date):
        raise PipelineError("종료 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).")
    days = trip_days(date_str, end_date)
    if days < 1:
        raise PipelineError("종료일은 시작일보다 앞설 수 없습니다.")
    if days > 7:
        raise PipelineError("일정은 최대 7일까지입니다.")

    keys = check_api_keys(require_kakao=True)
    if not keys:
        raise PipelineError("서버 환경변수에 API 키가 없습니다.")
    gemini_key, kakao_key, tmap_key, tour_key = keys

    preferred = model_name or "gemini-2.5-flash"
    selected_model = select_model(gemini_key, preferred=preferred)

    stem = result_stem(date_str, city, end_date)
    logs = [f"선택된 모델: {selected_model}"]
    if city:
        logs.append(f"사용자 지정 목적지: {city}")
    else:
        logs.append("목적지 비움 → LLM이 도시를 추천합니다.")
    if days == 1:
        logs.append(f"일정: {date_str} 당일")
    else:
        logs.append(f"일정: {date_str} ~ {end_date} ({days - 1}박 {days}일)")
    errors = []

    cached_data = load_cached_data(date_str, stem=stem) if use_cache else None
    if cached_data:
        logs.append(f"캐시된 데이터 사용: {stem}")
        recommendation = cached_data.get("recommendation", {})
        restaurants = cached_data.get("restaurants", [])
        tour_places = cached_data.get("tour_places") or {"attractions": [], "stays": []}
        transit_legs = cached_data.get("transit_legs", [])
        errors = cached_data.get("errors", [])
        raw_filepath = None
    else:
        logs.append("[1/5] 1차 추천 생성 중(LLM)")
        recommendation = get_recommendation(
            gemini_key, selected_model, date_str, errors, city=city
        )
        if not recommendation:
            raise PipelineError("1차 추천 정보를 생성하지 못했습니다.")
        if city:
            recommendation["recommended_city"] = city
        recommended_city = recommendation.get("recommended_city", "대한민국")
        logs.append(f"recommended_city: {recommended_city}")

        logs.append("[2/5] 맛집 검색 중(Kakao)")
        restaurants = search_restaurants(kakao_key, recommended_city, errors)
        logs.append(f"맛집 {len(restaurants)}곳")

        logs.append("[3/5] 관광지/숙소 조회 중(TourAPI)")
        tour_places = {"attractions": [], "stays": []}
        if tour_key:
            tour_places = search_official_places(
                tour_key, recommended_city, date_str, errors
            )
            logs.append(
                "중심 {0}곳, 숙소 {1}곳, 연관 {2}곳, 집중률 {3}건".format(
                    len(tour_places.get("attractions") or []),
                    len(tour_places.get("stays") or []),
                    len(tour_places.get("related") or []),
                    len(tour_places.get("crowd") or []),
                )
            )
        else:
            logs.append("TOUR_API_SERVICE_KEY 없음, 생략")

        logs.append("[4/5] 이동 정보 조회 중(TMAP)")
        transit_legs = []
        if tmap_key:
            transit_legs = build_travel_legs(tmap_key, restaurants, date_str, errors)
            logs.append(f"이동 구간 {len(transit_legs)}개")
        else:
            logs.append("TMAP_OPEN_API_APP_KEY 없음, 생략")

        raw_filepath = save_raw_data(
            date_str,
            recommendation,
            restaurants,
            errors,
            model=selected_model,
            transit_legs=transit_legs,
            tour_places=tour_places,
            stem=stem,
            end_date=end_date,
            days=days,
        )
        logs.append(f"원본 저장: {raw_filepath}")

    logs.append("[5/5] 최종 리포트 생성 중(LLM)")
    report_md = generate_report(
        gemini_key,
        selected_model,
        date_str,
        recommendation,
        restaurants,
        errors,
        transit_legs=transit_legs,
        tour_places=tour_places,
        end_date=end_date,
        days=days,
    )
    report_filepath = save_report(date_str, report_md, stem=stem)
    logs.append(f"리포트 저장: {report_filepath}")

    return {
        "date": date_str,
        "end_date": end_date,
        "days": days,
        "stem": stem,
        "model": selected_model,
        "recommendation": recommendation,
        "restaurants": restaurants,
        "tour_places": tour_places,
        "transit_legs": transit_legs,
        "errors": errors,
        "report_md": report_md,
        "report_path": report_filepath,
        "raw_path": raw_filepath,
        "logs": logs,
    }
