# `server/` — FastAPI 라우트와 HTML (`fastapi-web`)

이 폴더는 브라우저가 날짜를 넣고 `POST /api/plan`을 보내면 `src/pipeline.run_pipeline()`을 실행하는 FastAPI 앱입니다.  
`GEMINI_API_KEY` 등 제공자 키는 프로세스 환경변수에만 있습니다. `index.html`과 `/api/plan` JSON에는 키가 들어가지 않습니다.

`GET /api/keys`에 쓰는 `KEY_SERVER_TOKEN`은 콘솔에서 발급받지 않습니다.  
만드는 명령은 루트 [README.md 1단계](../README.md)와 [scripts/README.md](../scripts/README.md)입니다.

화면의 버튼·색·`fetch`는 [templates/README.md](templates/README.md)에 있습니다.

---

## 1. 왜 `server/`가 있나

과제 제출본은 터미널의 `python travel_planner.py --date ...`입니다.  
평가자가 파이썬을 설치하지 않아도 `https://codyssey-5-project.onrender.com`에서 같은 `src/` 함수가 돌아가는지 보게 하려고 `server/app.py`를 두었습니다.

- 배포 URL: https://codyssey-5-project.onrender.com
- 배포가 보는 브랜치: https://github.com/seongbin45/CODYSSEY_5_ProJect/tree/fastapi-web

---

## 2. 파일

| 파일 | 내용 |
|---|---|
| `app.py` | `@app.get` / `@app.post` 함수. 여기가 주소 정의 |
| `__init__.py` | 이 폴더를 패키지로 만듦 |
| `templates/index.html` | `GET /`이 읽는 HTML 원문 |

시작할 때 `app.py`는 상위 폴더의 `src/`를 `sys.path`에 넣습니다.  
그래서 `from pipeline import run_pipeline`이 됩니다.  
`load_dotenv()`는 프로세스 cwd의 `.env`를 읽습니다. 로컬에서는 프로젝트 루트에서 uvicorn을 켜세요.

---

## 3. 주소

| 방법 | 주소 | 함수 / 하는 일 |
|---|---|---|
| GET, HEAD | `/` | `home()` → `_render_index()`가 `index.html`의 `<select name="model">`만 채움. Render 헬스체크가 HEAD를 보냄 |
| GET | `/health` | `health()` — `ok`, `gemini`(bool), `kakao`(bool), `kakao_key_len`(길이만). 키 문자열 없음 |
| GET | `/api/models` | `list_usable_models()` 결과 `{ "models": [...] }` |
| POST | `/api/plan` | `run_pipeline(date, model, use_cache)` 실행 후 JSON 반환 |
| GET | `/api/keys` | 헤더 토큰이 맞을 때만 `PROVIDER_KEYS` JSON. 화면 버튼 없음 |
| GET | `/results` | `results_index()`가 `results_dir()` 파일 목록 HTML을 문자열로 만듦 |
| GET | `/results/파일이름` | `FileResponse`. `.md` / `.json`만, `..` 불가 |

`GET /api/keys` 조건 (`api_keys()`):

- 환경변수 `KEY_SERVER_TOKEN`이 없으면 HTTP 500 (`서버에 KEY_SERVER_TOKEN 이 없습니다.`)
- 헤더 `Authorization: Bearer {값}`이 `KEY_SERVER_TOKEN`과 다르면 HTTP 401
- 맞으면 `{ "GEMINI_API_KEY": "...", ... }` — 값이 있는 이름만

토큰을 새로 만들 때:

```bat
python scripts\make_key_server_token.py
```

출력 첫 줄을 Render Environment `KEY_SERVER_TOKEN`에 붙입니다. GitHub에는 올리지 않습니다.

---

## 4. `POST /api/plan`이 받는 값과 주는 값

브라우저 `FormData`가 `multipart/form-data`로 보냅니다.

- `date` : `YYYY-MM-DD` (필수)
- `model` : 예 `gemini-2.5-flash` (빈 문자열이면 `run_pipeline`이 `gemini-2.5-flash`를 preferred로 씀)
- `use_cache` : 기본 True. 같은 날짜의 `results/{date}_raw_data.json`이 있으면 1~4단계 HTTP를 생략

성공 JSON 키: `date`, `model`, `logs`, `errors`, `report_md`, `recommendation`, `restaurants`, `report_url`, `raw_url`, `results_url`.  
제공자 키는 없습니다.

실패:

- `PipelineError` → HTTP 400, body `{ "detail": "..." }`
- 그 외 예외 → HTTP 502

---

## 5. 로컬에서 켜는 순서

1. 프로젝트 루트 `.env`에 키를 넣습니다. ([루트 README 3단계](../README.md))
2. `pip install -r requirements.txt`
3. **루트에서** 실행합니다. (cwd가 `.env`와 `src`를 찾게)

```bat
cd C:\Users\seong\Downloads\CODYSSEY_5_ProJect
uvicorn server.app:app --reload --port 8000
```

4. 브라우저 http://127.0.0.1:8000
5. 날짜를 고르고 **리포트 생성** → `POST /api/plan`
6. **저장된 리포트 저장소 열기** → `GET /results`

`--reload`는 `.py`를 저장하면 uvicorn이 프로세스를 다시 시작합니다.

---

## 6. Render에 올리는 순서

클릭 단위는 루트 [DEPLOY.md](../DEPLOY.md)와 같습니다. 여기서는 값만 적습니다.

1. GitHub `fastapi-web` 브랜치를 Render Web Service에 연결
2. Docker / `render.yaml` 사용
3. Environment에 넣기: `GEMINI_API_KEY`, `KAKAO_REST_API_KEY`, (선택) `TMAP_OPEN_API_APP_KEY`, `TOUR_API_SERVICE_KEY`, **`KEY_SERVER_TOKEN`**
4. Deploy
5. `GET https://codyssey-5-project.onrender.com/health` 에서 `kakao: true` 인지, `kakao_key_len`이 32인지 확인

무료 인스턴스는 꺼졌다가 첫 요청에 깨어납니다. 디스크의 `/app/results/`는 재시작 후 없을 수 있습니다.

---

## 7. 자주 보는 HTTP / 콘솔 메시지

- 첫 화면 500 + `TemplateResponse` / `unhashable dict` : 예전 코드. 지금은 `HTMLResponse` + 문자열 치환입니다.
- 맛집 0곳 + Kakao 401 : Render의 `KAKAO_REST_API_KEY`가 REST 키가 아니거나 잘림. `/health`의 `kakao_key_len`이 32가 아니면 다시 붙입니다.
- `/api/keys` 401 : 클라이언트의 `--key-token`과 Render `KEY_SERVER_TOKEN`이 다름
- `/api/keys` 500 : Render Environment에 `KEY_SERVER_TOKEN` 키가 없음
- HEAD `/` 405 : 예전. 지금은 `api_route(..., methods=["GET", "HEAD"])`

---

위로: [프로젝트 README](../README.md)  
호출하는 함수: [src/README.md](../src/README.md)  
HTML: [templates/README.md](templates/README.md)
