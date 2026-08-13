# `results/` — `save_raw_data` / `save_report`가 쓰는 폴더

이 폴더는 처음에는 이 README만 있을 수 있습니다.  
`python travel_planner.py --date ...` 또는 `POST /api/plan`을 한 번 실행하면 파일이 생깁니다.

Git에는 결과 파일을 올리지 않습니다. `.gitignore`의 `results/*` + `!results/README.md` 때문입니다.

---

## 1. 누가 어떤 경로에 쓰나

| 실행 방법 | 쓰는 함수 | 폴더 |
|---|---|---|
| `python travel_planner.py --date ...` | `utils.save_raw_data`, `utils.save_report` | 프로젝트 루트의 `results/` |
| `travel_planner.exe --date ...` | 같음. `app_dir()`이 exe 폴더 | exe와 같은 폴더의 `results/` |
| Render `POST /api/plan` | `pipeline.run_pipeline` → 같은 save 함수 | 컨테이너의 `/app/results/` (재시작하면 없을 수 있음) |

날짜는 **오늘이 아니라** `--date` / 폼의 `date` 값입니다.

---

## 2. 파일 이름

| 파일 | 누가 쓰나 | 내용 |
|---|---|---|
| `YYYY-MM-DD_raw_data.json` | `save_raw_data()` | `date`, `model`, `recommendation`, `restaurants`, `tour_places`, `transit_legs`, `errors` |
| `YYYY-MM-DD_travel_plan.md` | `save_report()` | `generate_report()`가 받은 Markdown |
| `gemini_model_compat.json` | `verify_all_models()` | `--verify-models`를 돌렸을 때만. 모델별 텍스트/JSON 통과 여부 |

예: `--date 2026-08-22`

- `2026-08-22_raw_data.json`
- `2026-08-22_travel_plan.md`

---

## 3. JSON에 최소한 있는 키

과제가 요구하는 것:

- `recommendation` : `recommended_city`, `weather`, `events`, `reason` (코드/리포트에서는 `recommended_city`)
- `restaurants` : 리스트. 0곳이면 `[]`
- `errors` : 리스트. 없으면 `[]`. 원소는 `{step, type, message}`

이 프로젝트가 추가로 넣는 키:

- `date`, `model`
- `tour_places` : `attractions`, `stays`, `related`, `crowd`
- `transit_legs` : TMAP 구간 dict 리스트

---

## 4. Markdown에 들어가는 제목

`generate_report()` 프롬프트가 요구하는 절:

- 추천 지역, 추천 이유
- 날씨 요약, 행사/축제
- 맛집 추천 (`restaurants`가 `[]`이면 “데이터 없음”)
- 관광지, 숙소, 연관 관광지, 혼잡/집중률
- 1일 일정 제안 (오전/오후/저녁)
- 이동 정보
- 오류 요약

맛집이 0곳이어도 `save_report()`는 호출됩니다. 과제 요구입니다.

---

## 5. 같은 날짜를 다시 실행할 때 (`load_cached_data`)

`results/YYYY-MM-DD_raw_data.json`이 있으면:

- CLI `main()`과 `run_pipeline(use_cache=True)`는 `get_recommendation` / `search_restaurants` / `search_official_places` / `build_travel_legs`를 **다시 HTTP 하지 않습니다.**
- `generate_report()`만 다시 호출하고 `{날짜}_travel_plan.md`를 덮어씁니다.

처음부터 다시 GET/POST 하려면 그 JSON을 지웁니다.

웹에서 Kakao 키를 고친 뒤에도, 예전에 401이 난 JSON이 남아 있으면 `restaurants`가 계속 `[]`입니다.  
그때는 `{날짜}_raw_data.json`을 지우거나 다른 `--date`를 씁니다.

---

## 6. 웹에서 보는 방법

1. `index.html` 상단 **저장된 리포트 저장소 열기** → `GET /results`
2. 또는 주소창에 `/results`
3. 파일 이름을 누르면 `GET /results/파일이름`

로컬이면 탐색기에서 이 폴더를 열어도 됩니다.

---

위로: [프로젝트 README](../README.md)
