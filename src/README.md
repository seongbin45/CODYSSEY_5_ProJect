# `src/`

| 파일 | 단계 | HTTP |
|---|---|---|
| `api_llm.py` | 1단계 JSON, 3단계 Markdown | POST `generateContent` |
| `api_map.py` | 2단계 맛집 | GET Kakao keyword, `FD6` |
| `utils.py` | 날짜, `.env`, `results/` 저장 | 없음 |

CLI는 `travel_planner.py`의 `main()`이 위 함수를 직접 호출합니다.  
`-date`만 주면 모델은 `gemini-2.5-flash`입니다.

---

## 확장 (없어도 과제 최소는 동작)

| 파일 | 언제 호출되나 |
|---|---|
| `api_tour.py` | `TOUR_API_SERVICE_KEY`가 있을 때만 |
| `api_tmap.py` | `TMAP_OPEN_API_APP_KEY`가 있을 때만 |
