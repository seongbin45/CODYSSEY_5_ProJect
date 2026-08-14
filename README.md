# 국내 여행지 추천 (`main`)

날짜 하나를 넣으면 Gemini가 도시를 JSON으로 고르고, Kakao에서 맛집을 찾은 뒤, Markdown 리포트를 `results/`에 저장합니다. 웹이 아닙니다.

---

## 실행

Python 3.10 이상. 저장소를 받은 폴더에서:

```bat
python -m pip install -r requirements.txt
copy .env.example .env
```

`.env`에 `GEMINI_API_KEY`와 `KAKAO_REST_API_KEY`만 붙입니다. 따옴표와 `KakaoAK`는 넣지 않습니다.

- Gemini: https://aistudio.google.com/apikey
- Kakao: https://developers.kakao.com/ → 앱 → **REST API 키**. 같은 앱에서 카카오맵 ON.

```bat
python travel_planner.py -date "2026-03-15"
```

`-date`가 과제 옵션입니다. `--date`도 같습니다. 모델 기본값은 `gemini-2.5-flash`입니다.

끝나면 아래를 엽니다.

- `results/2026-03-15_raw_data.json` — 1차 추천 + 맛집 + `errors`
- `results/2026-03-15_travel_plan.md` — 최종 리포트

같은 날짜 JSON이 있으면 1·2단계 API를 건너뛰고 `[경고] 캐시 사용`을 출력한 뒤 리포트만 다시 씁니다. 처음부터: `-date "2026-03-15" --no-cache`

키 문자열은 README, 로그, 결과 파일에 적지 않습니다.

---

## 학습 목표

과제 원문이 “말로 설명할 수 있어야 한다”고 한 네 가지입니다.

### 1. REST와 GET / POST

HTTP 요청은 **방법(메서드)** + **주소** + (있을 수 있는) **본문** + **응답**입니다.

| | GET | POST |
|---|---|---|
| 하는 일 | 이미 있는 것을 조회 | 본문을 보내 일을 시킴 |
| 이 프로그램 | Kakao 맛집 검색 | Gemini JSON·리포트 생성 |
| 코드 | `src/api_map.py` `search_restaurants` → `requests.get` | `src/api_llm.py` `_call_gemini` → `requests.post` |

Kakao는 `GET .../keyword.json?query={도시} 맛집&category_group_code=FD6` 입니다. 검색어가 주소에 붙습니다. 키는 헤더 `Authorization: KakaoAK ...`에만 넣습니다.

Gemini는 `POST .../models/{이름}:generateContent` 입니다. 프롬프트와 “JSON으로 답하라”가 **본문**에 있습니다. 문장이 길어 GET 주소에 넣지 않습니다.

교재에서 POST를 “처리/등록”이라고 부르기도 합니다. **과제 원문 용어는 GET/POST입니다.** 이 코드에 대면:

- **조회** = Kakao GET
- **처리** = Gemini POST (구글에 우리 여행을 저장하지 않음. 텍스트만 만들어 줌)
- **등록** = `src/utils.py` `save_raw_data` / `save_report` 가 `results/`에 파일을 씀

### 2. LLM JSON을 다음 단계 입력으로

`src/api_llm.py` `get_recommendation`이 1차 JSON을 받습니다. 필수 키는 `recommended_city`, `weather`, `events`, `reason`입니다. `recommendation_schema_error()`가 키·빈 값을 검사하고, 실패하면 프롬프트에 오류를 붙여 **1회만** 다시 POST합니다.

`travel_planner.py`는 `recommendation["recommended_city"]`를 `search_restaurants(..., city_name)`에 넘깁니다. Kakao `query`가 `{도시} 맛집`이 됩니다. **1단계 POST의 도시 이름이 2단계 GET의 검색어입니다.**

### 3. 오류와 대응

| 원문이 말한 오류 | 이 프로그램 |
|---|---|
| 키 미설정 | `check_api_keys`가 종료하고 `copy .env.example .env`를 안내 |
| 인증 (401/403) | Kakao: `add_error(..., AUTH_ERROR)`, 맛집 `[]`, 리포트는 계속 |
| 네트워크 | `RequestException` → `errors`, 해당 단계만 실패 |
| 파싱 | JSON/스키마 실패 시 프롬프트 수정 후 재시도 1회. 또 실패하면 `errors`에 남기고 1단계는 종료 |
| 맛집 0건 | 중단하지 않음. 리포트 맛집 절에 “데이터 없음” |

`errors`는 `{step, type, message}` 리스트로 JSON과 리포트에 들어갑니다.

### 4. 키를 `.env`에 두는 이유

원문이 적은 이유 두 가지입니다.

- 제출·공유할 때 키가 코드에 안 보임
- 키를 바꿔도 `.py`를 고치지 않음

구현: `.env` + `python-dotenv` (`load_runtime_env`). `.env`는 Git에 올리지 않습니다 (`.gitignore`).

---

## 채점 대조

| 원문 | 여기 |
|---|---|
| CLI, argparse, `-date YYYY-MM-DD` | `travel_planner.py` |
| 날짜 오류 시 사용법 후 종료 | `validate_date` + `parser.print_help` |
| LLM 택1 + 지도 택1 | Gemini + Kakao Local |
| 1차 JSON 4키, 파싱 실패 시 재시도 1회 | `get_recommendation`, `recommendation_schema_error` |
| 맛집 N곳(5), 0건이어도 계속 | `search_restaurants` `size=5` |
| Markdown: 추천 지역·이유, 날씨, 행사, 맛집, 1일 일정, 오류 | `generate_report` |
| JSON에 1차 추천 + 맛집 + errors | `save_raw_data` |
| 키 미설정 즉시 종료 | `check_api_keys` |
| 키를 코드/README/결과에 안 씀 | `.env`만 |

로그는 `[1/3]` `[2/3]` `[3/3]` 입니다.

보너스: 같은 날짜 캐시(`load_cached_data`, `--no-cache`). 복수 지역 추천은 **선택이며 구현하지 않았습니다.**

---

## 폴더

```
travel_planner.py     CLI
requirements.txt      requests, python-dotenv
.env.example          키 이름만
src/api_llm.py        1·3단계 POST
src/api_map.py        2단계 GET
src/utils.py          날짜, .env, results 저장
results/              JSON + MD
과제조건.txt          과제 화면 저장본
```

---

## 확장 (과제 필수 아님)

`.env`에 키가 있을 때만 호출합니다. 학습 목표의 GET/POST 필수 예가 아닙니다.

- `TOUR_API_SERVICE_KEY` → `src/api_tour.py` (GET, 로그 `[확장]`)
- `TMAP_OPEN_API_APP_KEY` → `src/api_tmap.py` (POST, 로그 `[확장]`)
- `--list-models` / `--verify-models` / `--model`
- `export/` exe — https://github.com/seongbin45/CODYSSEY_5_ProJect/releases/latest
- 웹: 브랜치 `fastapi-web`

---

## 모델 목록이 바뀌면

Google은 Gemini 이름을 주기적으로 바꿉니다. 기본값 `gemini-2.5-flash`가 사라지면 코드를 고쳐야 합니다. `--list-models`로 현재 목록을 보고 `--model`을 쓰거나 `DEFAULT_MODEL`을 바꿉니다.
