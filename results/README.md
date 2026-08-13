# `results/` — 실행이 남기는 결과물

이 폴더는 처음에는 비어 있거나 이 README만 있습니다.  
프로그램을 한 번 실행하면 여기에 파일이 생깁니다.

Git에는 결과 파일은 올리지 않습니다. (`.gitignore`의 `results/`)  
이 설명 파일만 예외로 올립니다.

---

## 1. 누가 만드나

- 터미널: `python travel_planner.py --date ...`
- 웹: 사이트에서 **리포트 생성**
- exe: `travel_planner.exe --date ...`

저장 위치는 “프로그램이 있는 폴더/results” 입니다.

- 소스로 실행 → 프로젝트 루트의 `results/`
- exe로 실행 → `travel_planner.exe`와 같은 폴더의 `results/`
- Render 웹 → 서버 안의 `/app/results/` (재시작하면 지워질 수 있음)

---

## 2. 파일 이름 규칙

날짜는 **오늘이 아니라**, 사용자가 넣은 여행일입니다.

| 파일 | 내용 |
|---|---|
| `YYYY-MM-DD_raw_data.json` | 기계가 읽는 원본. 1차 추천, 맛집, 관광지, 이동, 오류 |
| `YYYY-MM-DD_travel_plan.md` | 사람이 읽는 최종 리포트 |
| `gemini_model_compat.json` | `--verify-models`를 돌렸을 때만 생김. 모델별 통과/실패 |

예: `--date 2026-08-22` 이면

- `2026-08-22_raw_data.json`
- `2026-08-22_travel_plan.md`

---

## 3. 원본 JSON 안에 최소한 있는 것

과제가 요구하는 것:

- 1차 추천 (`recommendation`: city, weather, events, reason)
- 맛집 리스트 (`restaurants`, 0곳도 가능)
- 오류 배열 (`errors`, 빈 배열도 가능)

이 프로젝트는 추가로 넣습니다.

- `date`, `model`
- `tour_places` (관광지/숙소/연관/집중률)
- `transit_legs` (TMAP 구간)

---

## 4. 리포트 Markdown에 있는 제목

- 추천 지역, 추천 이유
- 날씨 요약, 행사/축제
- 맛집 추천 (0곳이면 “데이터 없음”)
- 관광지, 숙소, 연관 관광지, 혼잡/집중률
- 1일 일정 제안 (오전/오후/저녁)
- 이동 정보
- 오류 요약

맛집이 없어도 리포트는 만들어집니다. 그게 과제 요구입니다.

---

## 5. 캐시 (같은 날짜를 다시 실행할 때)

같은 `YYYY-MM-DD_raw_data.json`이 있으면 1~4단계 API를 다시 부르지 않고, 그 JSON으로 리포트만 다시 씁니다.

처음부터 다시 받으려면 그 JSON을 지우면 됩니다.  
웹에서 Kakao 키를 고친 뒤에도, 예전에 실패한 JSON이 남아 있으면 맛집이 계속 0곳일 수 있습니다. 그때는 파일을 지우고 다시 생성하거나 날짜를 바꿉니다.

---

## 6. 웹에서 보는 방법

1. 사이트 상단 **저장된 리포트 저장소 열기**
2. 또는 주소 `/results`
3. 파일 이름을 누르면 내려받거나 브라우저에 내용이 보입니다.

로컬이면 탐색기에서 이 폴더를 열어도 됩니다.

---

위로: [프로젝트 README](../README.md)
