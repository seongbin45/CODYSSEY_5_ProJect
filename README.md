# 국내 여행지 추천 (`main`)

과제 제출물입니다. LLM 1개(Gemini) + 지도 1개(Kakao) + CLI 하나 + `results/` 출력입니다.

웹 서버, Docker, 키 배포 토큰은 이 브랜치에 없습니다.

---

## 채점 대조

| 요건 | 여기 |
|---|---|
| CLI, `argparse`, `-date YYYY-MM-DD` | `travel_planner.py` |
| 1단계 LLM → JSON (`recommended_city`, `weather`, `events`, `reason`) | `src/api_llm.py` `get_recommendation` — **POST** |
| 2단계 지도 검색. 입력은 1단계의 `recommended_city` | `src/api_map.py` `search_restaurants` — **GET** |
| 맛집 0건이어도 중단하지 않음 | 빈 리스트로 3단계 진행 |
| 3단계 LLM → Markdown 리포트 | `src/api_llm.py` `generate_report` — **POST** |
| `results/날짜_raw_data.json` | 1차 JSON + 맛집 + `errors` |
| `results/날짜_travel_plan.md` | 최종 리포트 |
| 키는 코드에 없음 | `.env` (`python-dotenv`) |
| 날짜 형식 오류 | 사용법 출력 후 종료 |
| LLM JSON 파싱 실패 | 1회만 재요청 |

로그는 과제 예시와 같이 `[1/3]` `[2/3]` `[3/3]` 입니다.

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

`-date`가 과제 옵션입니다. `--date`도 같은 값으로 동작합니다.  
`--model`을 생략하면 키로 조회한 목록에서 고릅니다. 지정 예: `-date "2026-03-15" --model gemini-2.5-flash`

Windows에서 `python`이 안 되면 `py -3`으로 바꿔 치면 됩니다.

끝나면 `results/2026-03-15_travel_plan.md`를 엽니다.  
같은 날짜를 다시 실행하면 저장된 JSON으로 리포트만 다시 씁니다(보너스 캐시). 처음부터 다시 받으려면 그 JSON을 지웁니다.

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
docs/과제요건_정리.md  과제 원문 정리
```

---

## 확장 (과제 필수 아님)

값이 `.env`에 있을 때만 호출합니다. 없어도 `[1/3]~[3/3]`은 그대로 끝납니다.

- `TOUR_API_SERVICE_KEY` → `src/api_tour.py` (로그: `[확장]`)
- `TMAP_OPEN_API_APP_KEY` → `src/api_tmap.py` (로그: `[확장]`)
- `--list-models` / `--verify-models`
- `export/` PyInstaller exe, [Release v1.0.0](https://github.com/seongbin45/CODYSSEY_5_ProJect/releases/tag/v1.0.0)
- 웹·키 서버: 브랜치 `fastapi-web`
