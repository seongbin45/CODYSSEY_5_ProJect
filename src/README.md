# `src/` — 프로그램의 엔진

이 폴더는 **실제로 API를 호출하고 결과를 이어 붙이는 코드**입니다.  
루트의 `travel_planner.py`와 `server/app.py`는 입구일 뿐이고, 계산은 여기서 합니다.

초심자는 아래 순서로 읽으면 됩니다.

---

## 1. 왜 `src`로 나누었나

한 파일에 모두 넣으면 과제는 통과할 수 있습니다.  
다만 Gemini, Kakao, TMAP, TourAPI가 각각 오류 처리와 주소가 달라서, **역할별로 파일을 나눈 것**입니다.

실행할 때 파이썬이 이 폴더를 찾을 수 있게, `travel_planner.py`가 `src`를 `sys.path`에 넣습니다.  
그래서 코드 안에서는 `from utils import ...`처럼 **짧은 이름**으로 가져옵니다.

---

## 2. 파일 목록 (역할)

| 파일 | 한 줄 역할 | HTTP |
|---|---|---|
| `pipeline.py` | 1→5단계를 순서대로 실행 | 직접 호출 없음 |
| `utils.py` | 날짜 검사, 키 확인, 파일 저장, `.env`/키 서버 읽기 | 키 서버 GET |
| `key_client.py` | Render `/api/keys`에서 키 JSON을 받음 | GET |
| `key_server.py` | 로컬에서만 쓰는 작은 키 서버 (선택) | GET |
| `api_llm.py` | Gemini 모델 목록, 1차 JSON, 최종 Markdown | GET 목록, POST 생성 |
| `api_map.py` | Kakao 맛집 검색 | GET |
| `api_tmap.py` | 도보·대중교통 구간 | POST |
| `api_tour.py` | 관광공사 공식/중심/연관/집중률 | GET |
| `__init__.py` | “이 폴더는 파이썬 패키지”라는 표시 | 없음 |

`__pycache__/`는 파이썬이 자동으로 만드는 번역 파일입니다. 손으로 고치지 않습니다.

---

## 3. 데이터가 흘러가는 순서

`pipeline.py`의 `run_pipeline(날짜, 모델이름)`이 지휘합니다.

```
날짜 검사
  → 키 확인 (없거나 Kakao 없으면 중단)
  → Gemini 모델 확정
  → (캐시 JSON이 있으면 1~4단계 생략)
  → [1] Gemini POST  → recommended_city, weather, events, reason
  → [2] Kakao GET    → 맛집 리스트 (실패해도 빈 리스트로 계속)
  → [3] TourAPI GET  → 관광지/숙소/연관/집중률 (키 없으면 생략)
  → [4] TMAP POST    → 맛집 사이 이동 (키 없거나 맛집 0곳이면 빈 값)
  → 원본 JSON 저장
  → [5] Gemini POST  → Markdown 리포트 저장
```

과제가 요구하는 최소 흐름은 **1, 2, 5**입니다. 3과 4는 보강입니다.

---

## 4. 파일별 세부

### `pipeline.py`

- `PipelineError` : 웹/CLI가 같은 방식으로 실패를 받기 위한 예외
- `list_usable_models(gemini_key)` : 선택 가능한 모델 이름 목록
- `run_pipeline(...)` : 위 전체 순서. 로그 문자열 리스트와 결과 dict를 돌려줍니다.

웹과 CLI가 이 함수를 **같이** 씁니다. 동작을 바꿀 때는 여기부터 보면 됩니다.

### `utils.py`

- `app_dir()` : 프로젝트 루트 또는 exe가 있는 폴더
- `results_dir()` : `app_dir()/results` 를 만들고 경로를 돌려줌
- `load_runtime_env()` :
  1. 로컬 `.env`를 읽음
  2. 이미 Gemini 키가 있으면 서버를 부르지 않음
  3. 키가 없고 URL이 있으면 `key_client`로 서버에서 받음
- `validate_date()` : `YYYY-MM-DD` 인지 검사
- `check_api_keys()` : Gemini 필수, Kakao는 옵션으로 필수 지정 가능
- `normalize_secret()` : 따옴표, `KakaoAK ` 접두어 제거
- `save_raw_data` / `save_report` / `load_cached_data` : 결과 파일
- `add_error()` : `{step, type, message}` 를 리스트에 추가

### `key_client.py`

- `DEFAULT_KEY_SERVER_URL` : Render 주소 `/api/keys`
- `PROVIDER_KEYS` : 받아도 되는 키 이름 네 개만
- `fetch_keys_from_server(url, token)` : `Authorization: Bearer 토큰` 으로 GET
- 키 값은 print 하지 않습니다. 적용된 **이름만** 로그에 남깁니다.

### `api_llm.py` (Gemini)

1. `GET /v1beta/models` 로 키에 보이는 모델 전체 목록
2. 이름만으로 1차 추정 (`gemini-2.5-flash` 는 가능, `antigravity-` 는 불가)
3. `--verify-models` 로 텍스트+JSON을 실제로 호출해 `results/gemini_model_compat.json`에 기록
4. 1차 추천: `POST .../generateContent`, `responseMimeType=application/json`
5. JSON 파싱 실패 시 **한 번만** 다시 요청
6. 최종 리포트: 같은 POST, 이번엔 일반 텍스트(Markdown)
7. 키는 URL이 아니라 `x-goog-api-key` 헤더로 보냄 (로그에 키가 안 남게)

과제가 요구하는 1차 JSON 키:

- `recommended_city` (문자열)
- `weather` (문자열)
- `events` (문자열 배열 1~3개)
- `reason` (2~4문장)

### `api_map.py` (Kakao)

- 주소: `GET https://dapi.kakao.com/v2/local/search/keyword.json`
- 헤더: `Authorization: KakaoAK {REST키}`
- 검색어: `{도시} 맛집`, 음식점 코드 `FD6`, 최대 5곳
- 필드: `name`, `address`, `category`, `url`, `x`, `y` (숫자는 가능하면 float)
- 0건이거나 401/403이어도 **프로그램을 끝내지 않음**. `errors`에만 남김
- 오류 메시지에 키를 넣지 않음. 대신 키 **길이**만 알려 줌 (REST 키는 보통 32자)

### `api_tmap.py`

- 도보: `POST .../tmap/routes/pedestrian`
- 대중교통: `POST .../transit/routes/sub`
- 맛집 앞 3곳의 좌표로 구간 1~2개를 만듦
- 키 없거나 좌표 없거나 실패하면 빈 리스트. 리포트는 계속

### `api_tour.py`

같은 `TOUR_API_SERVICE_KEY`로 네 가지를 부릅니다.

1. KorService2 `searchKeyword2` : 공식 관광지(12), 숙소(32)
2. LocgoHubTarService1 : 그 지역 중심 관광지
3. TarRlteTarService1 : 함께 가는 장소
4. TatsCnctrRateService : 여행일 집중률 (조회일부터 약 30일)

도시 이름 → 법정동 `areaCd`/`signguCd` 표가 파일 안에 있습니다.  
표에 없는 도시면 데이터랩은 건너뛰고, 키워드 검색만 시도합니다.

### `key_server.py`

로컬 연습용입니다. 실제 평가는 Render FastAPI의 `/api/keys`를 씁니다.

```bat
python src/key_server.py --host 127.0.0.1 --port 8787
```

---

## 5. 이 폴더만 시험해 보고 싶을 때

프로젝트 루트에서:

```bat
set PYTHONPATH=src
python -c "from pipeline import run_pipeline; print(run_pipeline('2026-08-20', 'gemini-2.5-flash')['logs'])"
```

키가 없으면 `check_api_keys`가 안내를 출력하고 실패합니다.

---

위로: [프로젝트 README](../README.md)  
웹 쪽: [server/README.md](../server/README.md)
