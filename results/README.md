# `results/`

`python travel_planner.py -date "2026-03-15"` 실행 후:

| 파일 | 과제 |
|---|---|
| `YYYY-MM-DD_raw_data.json` | 1차 추천 + 맛집 + `errors` |
| `YYYY-MM-DD_travel_plan.md` | 최종 Markdown |

날짜는 오늘이 아니라 `-date`에 넣은 값입니다.

같은 날짜 JSON이 있으면 1·2단계 API를 다시 부르지 않고, 콘솔에 `[경고] 캐시 사용`을 출력한 뒤 리포트만 다시 씁니다.  
다시 받으려면 `--no-cache` 를 붙이거나 그 JSON을 지웁니다.

`gemini_model_compat.json`은 `--verify-models`를 썼을 때만 생깁니다. 과제 필수 아님.
