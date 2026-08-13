# `server/` — 웹으로 실행하는 입구

이 폴더는 **브라우저에서 날짜를 넣고 리포트를 받는 FastAPI 서버**입니다.  
Gemini/Kakao 키는 서버 환경변수에만 있고, HTML이나 JSON 응답으로 내려가지 않습니다.

웹 화면의 버튼·색·주소는 [templates/README.md](templates/README.md)에 있습니다.

---

## 1. 왜 웹이 있나

과제 본편은 터미널(`travel_planner.py`)입니다.  
평가자가 파이썬을 설치하지 않고도 흐름을 볼 수 있게, 같은 `src/pipeline.py`를 웹에서도 돌립니다.

배포 주소 (현재): https://codyssey-5-project.onrender.com  
코드 브랜치: https://github.com/seongbin45/CODYSSEY_5_ProJect/tree/fastapi-web

---

## 2. 파일

| 파일 | 역할 |
|---|---|
| `app.py` | 주소(라우트)와 동작. 여기가 서버의 본문입니다. |
| `__init__.py` | 이 폴더를 패키지로 만듦 |
| `templates/index.html` | 첫 화면 HTML |

시작할 때 `app.py`는 상위 폴더의 `src/`를 `sys.path`에 넣습니다.  
그래서 `from pipeline import run_pipeline`이 됩니다.

---

## 3. 주소표 (외울 필요 없이 이 표만 보면 됨)

| 방법 | 주소 | 하는 일 |
|---|---|---|
| GET, HEAD | `/` | 첫 화면. Render 헬스체크용 HEAD도 받음 |
| GET | `/health` | 서버가 살아 있는지, Gemini/Kakao 키가 **있는지**만 (값은 안 줌) |
| GET | `/api/models` | 선택 가능한 Gemini 모델 이름 목록 |
| POST | `/api/plan` | 날짜·모델로 파이프라인 실행. 리포트 본문을 JSON으로 반환 |
| GET | `/api/keys` | **토큰이 있을 때만** 제공자 키 JSON. exe/CLI용 |
| GET | `/results` | 저장된 md/json 목록 페이지 |
| GET | `/results/파일이름` | 그 파일 다운로드/열기 |

`/api/keys`는 화면 버튼이 아닙니다.  
헤더 `Authorization: Bearer {KEY_SERVER_TOKEN}` 이 맞아야 200입니다. 틀리면 401입니다.

---

## 4. `/api/plan`이 받는 값과 주는 값

브라우저 폼이 `multipart/form-data`로 보냅니다.

- `date` : `YYYY-MM-DD` (필수)
- `model` : 예 `gemini-2.5-flash` (비우면 서버가 기본 모델)
- `use_cache` : 같은 날짜 JSON이 있으면 재사용

성공 시 JSON에 `logs`, `report_md`, `report_url`, `raw_url`, `results_url`이 들어 있습니다.  
키는 들어 있지 않습니다.

---

## 5. 로컬에서 켜는 순서

1. 프로젝트 루트에 `.env`를 채웁니다. ([루트 README 3단계](../README.md))
2. 패키지를 설치합니다. `pip install -r requirements.txt`
3. 루트에서 실행합니다.

```bat
cd C:\Users\seong\Downloads\CODYSSEY_5_ProJect
uvicorn server.app:app --reload --port 8000
```

4. 브라우저에서 http://127.0.0.1:8000
5. 날짜를 고르고 **리포트 생성**
6. **저장된 리포트 저장소 열기** → `/results`

`--reload`는 코드를 저장하면 서버가 다시 시작됩니다.

---

## 6. 클라우드(Render)에 올리는 순서

자세한 화면 클릭은 루트의 [DEPLOY.md](../DEPLOY.md)와 같습니다. 요약만 적습니다.

1. GitHub 저장소의 `fastapi-web` 브랜치를 Render Web Service에 연결
2. Docker / `render.yaml` 사용
3. Environment에 키를 넣음 (`GEMINI_API_KEY`, `KAKAO_REST_API_KEY`, 선택 키, `KEY_SERVER_TOKEN`)
4. Deploy
5. 첫 화면이 열리는지, `/health`의 `kakao: true` 인지 확인

무료 인스턴스는 잠시 꺼졌다가 다시 켜질 수 있고, 디스크의 `results/`는 재시작 후 사라질 수 있습니다.

---

## 7. 자주 보는 오류

- 첫 화면 500 + `TemplateResponse` / `unhashable dict` : 예전 버그. 지금은 Jinja를 쓰지 않고 HTML을 직접 줍니다.
- 맛집 0곳 + Kakao 401 : Render의 Kakao 키가 REST 키가 아니거나 잘렸습니다. 보통 32자입니다.
- `/api/keys` 401 : 토큰이 없거나 Render의 `KEY_SERVER_TOKEN`과 다릅니다.
- `/api/keys` 500 : 서버에 `KEY_SERVER_TOKEN` 자체가 없습니다.

---

위로: [프로젝트 README](../README.md)  
엔진: [src/README.md](../src/README.md)  
화면 HTML: [templates/README.md](templates/README.md)
