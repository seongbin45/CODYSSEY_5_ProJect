"""
Python 응용: API 활용 국내 여행지 추천 프로그램

- 1단계: Gemini LLM API (여행지 추천)
- 2단계: Kakao Local API (맛집 검색)
- 3단계: Gemini LLM API (최종 리포트 생성)
"""

import argparse
import os
import sys
from pathlib import Path

if not getattr(sys, "frozen", False):
    _SRC = str(Path(__file__).resolve().parent / "src")
    if _SRC not in sys.path:
        sys.path.insert(0, _SRC)

from utils import (
    app_dir,
    validate_date,
    check_api_keys,
    load_cached_data,
    save_raw_data,
    save_report,
    load_runtime_env,
)
from api_llm import (
    list_models,
    print_model_catalog,
    get_recommendation,
    generate_report,
    verify_all_models,
)
from api_map import search_restaurants
from api_tmap import build_travel_legs
from api_tour import search_official_places

DEFAULT_MODEL = "gemini-2.5-flash"


def parse_args():
    parser = argparse.ArgumentParser(description="API 활용 국내 여행지 추천 프로그램")
    parser.add_argument("-date", "--date", dest="date", help="여행 날짜 (YYYY-MM-DD). 과제 옵션은 -date")
    parser.add_argument(
        "--model",
        dest="model",
        default=DEFAULT_MODEL,
        help=f"Gemini 모델 ID (기본: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="이 API 키가 조회할 수 있는 모델 목록만 출력하고 종료합니다.",
    )
    parser.add_argument(
        "--verify-models",
        action="store_true",
        help="조회된 모든 모델을 하나씩 호출해 텍스트/JSON 호환 여부를 검증하고 저장합니다.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="같은 날짜의 results JSON이 있어도 1·2단계 API를 다시 호출합니다.",
    )
    args = parser.parse_args()
    if not args.list_models and not args.verify_models and not args.date:
        parser.error("-date 는 필수입니다. 예: python travel_planner.py -date 2026-03-15")
    return args, parser


def main():
    args, parser = parse_args()

    os.chdir(app_dir())
    load_runtime_env()
    keys = check_api_keys(
        require_kakao=not (args.list_models or args.verify_models)
    )
    if not keys:
        sys.exit(1)

    gemini_key, kakao_key, tmap_key, tour_key = keys

    if args.verify_models:
        print("[정보] 모델 교차검증을 시작합니다...")
        try:
            verify_all_models(gemini_key)
        except Exception as exc:
            print(f"[오류] 모델 교차검증 실패: {exc}")
            sys.exit(1)
        return

    if args.list_models:
        print("[정보] 이 API 키가 조회할 수 있는 모델 목록을 불러옵니다...")
        try:
            models = list_models(gemini_key)
        except Exception as exc:  # requests 오류를 사용자 메시지로만 보여 준다
            print(f"[오류] 모델 목록 조회 실패: {exc}")
            sys.exit(1)
        if not models:
            print("[오류] 조회된 모델이 없습니다.")
            sys.exit(1)
        print()
        print_model_catalog(models)
        return

    date_str = args.date
    if not validate_date(date_str):
        print(f"오류: '{date_str}'는 올바른 날짜 형식이 아닙니다 (YYYY-MM-DD).")
        parser.print_help()
        sys.exit(1)

    selected_model = args.model
    print(f"[정보] 선택된 모델: {selected_model}\n")

    errors = []

    cached_data = None if args.no_cache else load_cached_data(date_str)
    if cached_data:
        cache_name = f"{date_str}_raw_data.json"
        print("=" * 60)
        print(f"[경고] 캐시 사용: results/{cache_name}")
        print("[경고] 1·2단계 API(Gemini JSON, Kakao 맛집)를 다시 호출하지 않습니다.")
        print("[경고] errors 도 캐시 파일을 그대로 씁니다.")
        print("[경고] 처음부터 다시 받으려면 --no-cache 를 붙이거나 그 JSON을 지우세요.")
        print("=" * 60)
        recommendation = cached_data.get("recommendation", {})
        restaurants = cached_data.get("restaurants", [])
        tour_places = cached_data.get("tour_places") or {"attractions": [], "stays": []}
        transit_legs = cached_data.get("transit_legs", [])
        errors = cached_data.get("errors", [])
    else:
        print("[1/3] 1차 추천 생성 중(LLM)...")
        recommendation = get_recommendation(gemini_key, selected_model, date_str, errors)

        if not recommendation:
            print("오류: 1차 추천 정보를 생성하지 못했습니다. 프로그램을 종료합니다.")
            sys.exit(1)

        recommended_city = recommendation["recommended_city"]
        print(f"  - recommended_city: {recommended_city}")

        print("[2/3] 맛집 검색 중(지도/장소 API)...")
        restaurants = search_restaurants(kakao_key, recommended_city, errors)

        if restaurants:
            print(f"  - 맛집 {len(restaurants)}곳 검색 완료")
        else:
            print("  - 검색 결과 0건 (또는 오류 발생)")

        tour_places = {"attractions": [], "stays": []}
        if tour_key:
            print("[확장] 관광지/숙소 조회 중(TourAPI)...")
            tour_places = search_official_places(
                tour_key, recommended_city, date_str, errors
            )
            attr_n = len(tour_places.get("attractions") or [])
            stay_n = len(tour_places.get("stays") or [])
            rel_n = len(tour_places.get("related") or [])
            crowd_n = len(tour_places.get("crowd") or [])
            print(
                f"  - 중심 {attr_n}곳, 공식 숙소 {stay_n}곳, "
                f"연관 {rel_n}곳, 집중률 {crowd_n}건"
            )

        transit_legs = []
        if tmap_key:
            print("[확장] 이동 정보 조회 중(TMAP)...")
            transit_legs = build_travel_legs(tmap_key, restaurants, date_str, errors)
            if transit_legs:
                print(f"  - 이동 구간 {len(transit_legs)}개 조회 완료")
            else:
                print("  - 이동 정보 없음 (좌표 부족 또는 검색 실패)")

        raw_filepath = save_raw_data(
            date_str,
            recommendation,
            restaurants,
            errors,
            model=selected_model,
            transit_legs=transit_legs,
            tour_places=tour_places,
        )
        print(f"  - 원본 데이터 저장 완료: {raw_filepath}")

    print("[3/3] 최종 리포트 생성 중(LLM)...")
    report_md = generate_report(
        gemini_key,
        selected_model,
        date_str,
        recommendation,
        restaurants,
        errors,
        transit_legs=transit_legs,
        tour_places=tour_places,
    )
    
    report_filepath = save_report(date_str, report_md)
    print("  - 리포트 생성 완료")

    print(f"\n완료! {report_filepath} 를 확인하세요.")


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    main()
