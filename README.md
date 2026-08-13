# 국내 여행지 추천 (`main`)

과제 제출물입니다. LLM 1개(Gemini) + 지도 1개(Kakao) + CLI 하나 + `results/` 출력입니다.

---

## 채점 대조

| 요건 | 여기 |
|---|---|
| CLI, `argparse`, `-date YYYY-MM-DD` | `travel_planner.py` |
| 1단계 LLM → JSON (`recommended_city`, `weather`, `events`, `reason`) | `src/api_llm.py` `get_recommendation` — **POST**. 4키·빈 값 검사, 실패 시 1회 재요청 |
| 2단계 지도 검색. 입력은 1단계의 `recommended_city` | `src/api_map.py` `search_restaurants` — **GET** |
| 맛집 0건이어도 중단하지 않음 | 빈 리스트로 3단계 진행 |
| 3단계 LLM → Markdown 리포트 | `src/api_llm.py` `generate_report` — **POST** |
| `results/날짜_raw_data.json` | 1차 JSON + 맛집 + `errors` |
| `results/날짜_travel_plan.md` | 최종 리포트 |
| 키는 코드에 없음. 미설정이면 즉시 종료 | `.env` + `check_api_keys` |
| 날짜 형식 오류 | 사용법 출력 후 종료 |

로그는 `[1/3]` `[2/3]` `[3/3]` 입니다.  
`-date`만 주면 모델은 `gemini-2.5-flash`입니다. 목록에서 고르지 않습니다.

---

## 실행

Python 3.10 이상. 저장소를 받은 폴더에서:

```bat
python -m pip install -r requirements.txt
copy .env.example .env
```

`.env`의 `GEMINI_API_KEY`와 `KAKAO_REST_API_KEY`만 채웁니다.  
Gemini: https://aistudio.google.com/apikey  
Kakao: https://developers.kakao.com/ → 앱 → **REST API 키**. 같은 앱에서 카카오맵 ON. 따옴표와 `KakaoAK`는 붙이지 않습니다.

```bat
python travel_planner.py -date "2026-03-15"
```

모델은 기본값 `gemini-2.5-flash`입니다. `--model`을 붙이지 않아도 됩니다.  
`-date`가 과제 옵션입니다. `--date`도 같은 값으로 동작합니다.  
Windows에서 `python`이 안 되면 `py -3`으로 바꿔 치면 됩니다.

끝나면 `results/2026-03-15_travel_plan.md`를 엽니다.

같은 날짜 JSON이 있으면 1·2단계 API를 건너뛰고 **경고를 출력한 뒤** 리포트만 다시 씁니다.  
처음부터 다시 받으려면:

```bat
python travel_planner.py -date "2026-03-15" --no-cache
```

---

## 폴더

```
travel_planner.py     CLI
requirements.txt      requests, python-dotenv
.env.example          키 이름만
src/api_llm.py        1단계·3단계
src/api_map.py        2단계
src/utils.py          날짜 검사, .env, results 저장
results/              출력
과제조건.txt          과제 화면 저장본
```

---

## 확장 (과제 필수 아님)

값이 `.env`에 있을 때만 호출합니다. 없어도 `[1/3]~[3/3]`은 그대로 끝납니다.

- `TOUR_API_SERVICE_KEY` → `src/api_tour.py` (로그: `[확장]`)
- `TMAP_OPEN_API_APP_KEY` → `src/api_tmap.py` (로그: `[확장]`)
- `--list-models` / `--verify-models` / `--model`
- `export/` PyInstaller exe
- 웹·키 서버: 브랜치 `fastapi-web`

---

## 모델 목록이 바뀌면

Google은 Gemini 모델 이름과 제공 목록을 주기적으로 바꿉니다. 모델 변경은 불가피합니다.

이 프로그램의 기본값은 코드에 박힌 `gemini-2.5-flash`입니다. 그 이름이 사라지거나 `generateContent`와 맞지 않게 바뀌면, 코드를 고치지 않고는 채점 경로를 유지할 수 없습니다. 모델 목록을 불러오는 로직을 코드에 만들지 않는 한 유지보수가 불가능합니다.

그때는 `--list-models`로 키가 보는 현재 목록을 확인하고, `--model`로 새 이름을 넘기거나 `travel_planner.py`의 `DEFAULT_MODEL`을 바꾸면 됩니다.
