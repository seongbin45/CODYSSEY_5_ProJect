# `src/` — API를 호출하는 파이썬 모듈

이 폴더의 파일이 Gemini / Kakao / TMAP / TourAPI에 `requests`로 GET·POST 하고, 반환 dict를 다음 함수 인자로 넘깁니다.

- 터미널: `travel_planner.py`의 `main()`이 아래 함수를 **직접** import 해서 같은 순서로 호출합니다. `pipeline.run_pipeline()`은 쓰지 않습니다.
- 웹: `server/app.py`의 `POST /api/plan`이 `pipeline.run_pipeline()`만 호출합니다.

초심자는 아래 순서로 읽으면 됩니다.

---

## 1. 왜 `src`로 나누었나

한 `.py`에 모두 넣어도 과제는 통과할 수 있습니다.  
Gemini·Kakao·TMAP·TourAPI는 URL, 헤더, 오류 코드가 달라서 **제공자마다 파일 하나**로 나눈 것입니다.

실행 시 이 폴더를 찾게 하는 코드:

- `travel_planner.py`가 `src`를 `sys.path` 앞에 넣음 (exe가 아닐 때)
- `server/app.py`도 상위 폴더의 `src`를 `sys.path`에 넣음
- `travel_planner.spec`의 `pathex=['src']`

그래서 코드 안에서는 `from utils import ...`처럼 패키지 접두어 없이 import 합니다.

---

## 2. 파일 목록

| 파일 | 들어 있는 함수 / 하는 일 | HTTP |
|---|---|---|
| `pipeline.py` | `run_pipeline()` — 웹만 사용. 아래 3절 순서 | 직접 호출 없음 |
| `utils.py` | 날짜 검사, 키 확인, `results/` 저장, `.env`와 키 서버 | 키 서버만 GET |
| `key_client.py` | `fetch_keys_from_server()` — Render `/api/keys` | GET |
| `key_server.py` | 로컬 연습용 HTTP 서버. Render 대신 쓸 때만 | GET `/keys` |
| `api_llm.py` | 모델 목록, 1차 JSON, 최종 Markdown | GET 목록, POST 생성 |
| `api_map.py` | `search_restaurants()` | GET |
| `api_tmap.py` | `build_travel_legs()` | POST |
| `api_tour.py` | `search_official_places()` | GET |
| `__init__.py` | 이 폴더를 패키지로 표시. 내용 없음에 가깝다 | 없음 |

`__pycache__/`는 파이썬이 `.pyc`를 넣는 폴더입니다. 손으로 고치지 않습니다.

---

## 3. `run_pipeline()` / CLI `main()`이 호출하는 순서

`pipeline.py`의 `run_pipeline(date_str, model_name=None, use_cache=True)`와  
`travel_planner.py`의 `main()`은 **같은 함수를 같은 순서로** 부릅니다.

```
validate_date(date_str)
  → check_api_keys(require_kakao=True)
       키가 없거나 Kakao가 없으면 CLI는 sys.exit(1), 웹은 PipelineError
  → select_model(gemini_key, preferred=...)
  → load_cached_data(date_str) 가 results/{날짜}_raw_data.json 을 읽으면
       get_recommendation / search_restaurants / search_official_places / build_travel_legs 생략
  → [1] get_recommendation()     Gemini POST  → dict(recommended_city, weather, events, reason)
  → [2] search_restaurants()     Kakao GET    → list (실패해도 [])
  → [3] search_official_places() TourAPI GET  → TOUR_API_SERVICE_KEY 없으면 생략
  → [4] build_travel_legs()      TMAP POST    → TMAP 키가 없거나 restaurants == [] 이면 []
  → save_raw_data(...)           results/{날짜}_raw_data.json
  → [5] generate_report()        Gemini POST  → Markdown 문자열
  → save_report(...)             results/{날짜}_travel_plan.md
```

과제 최소 호출은 **[1], [2], [5]** 입니다.  
[3][4]는 환경변수가 있을 때만 `if` 안으로 들어갑니다.

웹 반환 dict 키: `date`, `model`, `recommendation`, `restaurants`, `tour_places`, `transit_legs`, `errors`, `report_md`, `report_path`, `raw_path`, `logs`.

---

## 4. 파일별 함수

### `pipeline.py`

- `PipelineError` : `server/app.py`가 잡아 HTTP 400으로 바꿈
- `list_usable_models(gemini_key)` : `list_models()` 결과 중 `is_allowed_model()`이 True인 이름만
- `run_pipeline(...)` : 위 3절. 웹 `POST /api/plan`만 호출

동작을 바꿀 때: CLI는 `travel_planner.py`, 웹은 이 파일을 **둘 다** 고쳐야 같은 결과가 납니다.

### `utils.py`

- `app_dir()` : exe면 `sys.executable`의 폴더, 아니면 `src`의 상위(프로젝트 루트)
- `results_dir()` : `app_dir()/results` 를 만들고 그 경로를 반환
- `load_runtime_env(key_server_url, key_server_token)` :
  1. `resource_dir()/.env` 읽기 (`override=False`)
  2. `app_dir()/.env` 읽기 (`override=True`)
  3. `GEMINI_API_KEY`가 있고 URL이 없으면 return
  4. URL이 없고 Gemini 키도 없으면 `DEFAULT_KEY_SERVER_URL`
  5. `key_client.fetch_keys_from_server(url, token)` — 기존 환경변수는 덮어쓰지 않음
- `validate_date()` : `datetime.strptime(..., "%Y-%m-%d")`
- `check_api_keys(require_kakao=True)` : Gemini 필수. Kakao는 인자로 필수 지정
- `normalize_secret()` : 양쪽 따옴표, `KakaoAK ` 접두어 제거
- `save_raw_data` / `save_report` / `load_cached_data` : `results/` 파일
- `add_error()` : `{step, type, message}` 를 리스트에 append

### `key_client.py`

- `DEFAULT_KEY_SERVER_URL` : `https://codyssey-5-project.onrender.com/api/keys`
- `PROVIDER_KEYS` : `GEMINI_API_KEY`, `KAKAO_REST_API_KEY`, `TMAP_OPEN_API_APP_KEY`, `TOUR_API_SERVICE_KEY`
- `fetch_keys_from_server(url, token)` : `Authorization: Bearer {token}` 으로 GET
- 키 값은 print 하지 않음. 적용된 **이름만** `[정보] 키 서버에서 받은 항목:` 뒤에 출력

### `api_llm.py` (Gemini)

1. `GET https://generativelanguage.googleapis.com/v1beta/models` — 키 헤더 `x-goog-api-key`
2. 이름 규칙으로 1차 제외 (`antigravity-`, 이미지/TTS 등)
3. `--verify-models` → `verify_all_models()`가 텍스트+JSON을 실제로 POST하고 `results/gemini_model_compat.json`에 기록
4. 1차 추천: `POST .../models/{id}:generateContent`, `responseMimeType=application/json`
5. JSON 파싱 실패 시 **한 번만** 같은 POST를 다시 함
6. 최종 리포트: 같은 POST, `responseMimeType` 없이 Markdown 텍스트
7. 키가 URL 쿼리에 들어가지 않음 (`x-goog-api-key` 헤더)

1차 JSON에 있어야 하는 키:

- `recommended_city` (문자열)
- `weather` (문자열)
- `events` (문자열 배열 1~3개)
- `reason` (2~4문장)

### `api_map.py` (Kakao)

- URL: `GET https://dapi.kakao.com/v2/local/search/keyword.json`
- 헤더: `Authorization: KakaoAK {REST키}`
- 쿼리: `query={도시} 맛집`, `category_group_code=FD6`, `size=5`
- 반환 필드: `name`, `address`, `category`, `url`, `x`, `y` (`x`/`y`는 float 또는 None)
- 0건이거나 HTTP 401/403이어도 프로세스를 끝내지 않음. `errors`에만 추가하고 `[]` 반환
- 오류 메시지에 키 문자열을 넣지 않음. `len(api_key)`만 넣음 (REST 키는 보통 32자)

### `api_tmap.py`

- 도보: `POST https://apis.openapi.sk.com/tmap/routes/pedestrian`
- 대중교통: `POST https://apis.openapi.sk.com/transit/routes/sub`
- `restaurants` 앞 3곳의 `x`,`y`로 구간 1~2개를 만듦
- 키 없음 / 좌표 없음 / HTTP 실패 → `[]`. `generate_report()`는 계속 호출됨

### `api_tour.py`

같은 `TOUR_API_SERVICE_KEY`로 네 번 GET:

1. KorService2 `searchKeyword2` : `contentTypeId` 12(관광지), 32(숙소)
2. LocgoHubTarService1 : 법정동 코드가 있을 때만
3. TarRlteTarService1 : 법정동 코드가 있을 때만
4. TatsCnctrRateService : 여행일 기준 조회일부터 약 30일

도시 이름 → `areaCd` / `signguCd` 표가 이 파일 안에 있습니다.  
표에 없는 도시면 2~4를 건너뛰고 `searchKeyword2`만 시도합니다.

### `key_server.py`

로컬에서만 쓰는 연습용 서버입니다. 평가·exe는 Render의 `GET /api/keys`를 씁니다.

```bat
python src/key_server.py --host 127.0.0.1 --port 8787
```

이 서버의 경로는 `/keys`입니다. Render FastAPI의 경로는 `/api/keys`입니다. 혼동하지 마세요.

---

## 5. 이 폴더만 시험할 때

프로젝트 루트에서 (`run_pipeline`은 웹과 같은 경로):

```bat
set PYTHONPATH=src
python -c "from pipeline import run_pipeline; print(run_pipeline('2026-08-20', 'gemini-2.5-flash')['logs'])"
```

`GEMINI_API_KEY` / `KAKAO_REST_API_KEY`가 없으면 `check_api_keys`가 안내를 출력하고 실패합니다.

CLI와 똑같이 시험하려면:

```bat
python travel_planner.py --date "2026-08-20" --model gemini-2.5-flash
```

---

위로: [프로젝트 README](../README.md)  
웹 주소: [server/README.md](../server/README.md)
