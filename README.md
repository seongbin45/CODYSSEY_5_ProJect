# 국내 여행지 추천 프로그램 (처음부터 따라오기)

이 저장소는 **Codyssey 과제**용입니다.  
`--date YYYY-MM-DD` 하나를 넣으면 아래 함수가 순서대로 외부 HTTP를 호출하고, `results/`에 JSON과 Markdown을 씁니다.

초심자는 이 파일을 **위에서 아래 순서**로 읽으면 됩니다.  
각 폴더의 파일·함수·주소는 그 폴더의 `README.md`에 있습니다.

---

## 0단계. 실행하면 무엇이 호출되나

사람이 하는 일을 `travel_planner.py`의 `main()`(터미널) 또는 `server/app.py`의 `POST /api/plan` → `run_pipeline()`(웹)이 대신합니다. 둘 다 같은 `src/` 함수를 부릅니다.

1. 날짜를 받는다. 예: `2026-08-22` (`argparse`의 `-date` / `--date`)
2. `api_llm.get_recommendation()`이 Gemini `POST .../generateContent`로 1차 JSON을 받는다.  
   필수 키: `recommended_city`, `weather`, `events`, `reason`
3. 그 JSON의 `recommended_city`를 `api_map.search_restaurants()`에 넘긴다.  
   `GET https://dapi.kakao.com/v2/local/search/keyword.json?query={도시} 맛집&category_group_code=FD6`
4. `TOUR_API_SERVICE_KEY`가 있으면 `api_tour.search_official_places()`가 TourAPI를 **GET** 한다.  
   없으면 그 단계만 건너뛴다.
5. `TMAP_OPEN_API_APP_KEY`가 있으면 `api_tmap.build_travel_legs()`가 TMAP을 **POST** 한다.  
   키가 없거나 맛집이 0곳이면 빈 리스트로 둔다.
6. `api_llm.generate_report()`가 위 데이터를 다시 Gemini `POST .../generateContent`로 보내 Markdown을 받는다.
7. `utils.save_raw_data()` / `utils.save_report()`가 `results/YYYY-MM-DD_raw_data.json`과 `results/YYYY-MM-DD_travel_plan.md`를 쓴다.

과제가 채점하는 것은 날씨 정확도가 아닙니다.

- REST `GET`(조회)과 `POST`(본문을 보내는 요청)를 구분할 것
- Gemini JSON의 `recommended_city`를 Kakao `query`로 넘길 것
- 401/네트워크/JSON 파싱 실패 시 `errors`에 `{step, type, message}`를 넣고 계속할 것
- 키를 `.py`에 쓰지 말고 `.env` 또는 Render Environment에 둘 것

과제 최소 단계는 **1, 2, 6**(Gemini JSON → Kakao GET → Gemini Markdown)입니다.  
4와 5는 해당 환경변수가 있을 때만 실행합니다.

---

## 1단계. 폴더와 파일 (어디에 무엇이 있나)

```
CODYSSEY_5_ProJect/
├── README.md                 ← 지금 읽고 있는 파일
├── DEPLOY.md                 ← Render 대시보드에 넣을 값과 클릭 순서
├── 과제조건.txt              ← 원본 과제 화면 HTML 저장본
├── travel_planner.py         ← argparse CLI. python 또는 exe의 시작점
├── travel_planner.spec       ← PyInstaller 설정 (onefile, datas=[], pathex=['src'])
├── requirements.txt          ← pip가 설치하는 패키지 이름
├── Dockerfile / render.yaml  ← Render Web Service가 읽는 배포 설정
├── .env.example              ← 키 이름만 있는 예제. 값은 비어 있음
├── src/                      ← API를 호출하는 파이썬 모듈
├── server/                   ← FastAPI 라우트와 HTML
├── results/                  ← save_raw_data / save_report 가 쓰는 폴더
├── export/                   ← pyinstaller --distpath export 결과
└── docs/                     ← 프로그램이 읽지 않는 참고 파일
```

다음으로 읽을 문서:

| 폴더 | 문서 | 적혀 있는 것 |
|---|---|---|
| `src/` | [src/README.md](src/README.md) | 파일별 함수, HTTP 메서드, 호출 순서 |
| `server/` | [server/README.md](server/README.md) | `/`, `/api/plan`, `/api/keys` 등 주소 |
| `server/templates/` | [server/templates/README.md](server/templates/README.md) | `index.html`의 form과 fetch |
| `results/` | [results/README.md](results/README.md) | JSON/MD 파일 이름 |
| `export/` | [export/README.md](export/README.md) | `travel_planner.exe` 실행 인자 |
| `docs/` | [docs/README.md](docs/README.md) | zip·md 목록. 실행 시 읽지 않음 |

---

## 2단계. 컴퓨터 준비

1. Python **3.10 이상**이 있는지 확인합니다.

```bat
python --version
```

Windows에서 `python`이 Microsoft Store 안내만 나오면, 실제 실행 파일은 보통 아래입니다.

```bat
C:\Users\seong\AppData\Local\Programs\Python\Python310\python.exe --version
```

2. 이 폴더로 이동합니다.

```bat
cd C:\Users\seong\Downloads\CODYSSEY_5_ProJect
```

3. `requirements.txt`에 적힌 패키지만 설치합니다.

```bat
pip install -r requirements.txt
```

들어 있는 줄:

- `requests` : `src/api_*.py`가 HTTP GET/POST 할 때 사용
- `python-dotenv` : `utils.load_runtime_env()`가 `.env`를 읽을 때 사용
- `fastapi`, `uvicorn[standard]`, `jinja2`, `python-multipart` : `server/app.py`용  
  (`jinja2`는 남아 있으나 `app.py`는 Jinja `TemplateResponse`를 쓰지 않고 `HTMLResponse`를 씁니다.)

---

## 3단계. API 키를 어디에 두나

키 문자열은 **`.py` 파일에 적지 않습니다.** 아래 A 또는 B입니다.

### 방법 A. 이 PC에서 `python travel_planner.py` 할 때

1. 프로젝트 루트에 `.env`를 만듭니다. `.env.example`을 복사해도 됩니다.
2. 이름을 그대로 쓰고 `=` 뒤에 키만 붙입니다. 따옴표, `KakaoAK ` 접두어는 넣지 않습니다.  
   `utils.normalize_secret()`이 따옴표와 `KakaoAK `를 지우긴 하지만, 처음부터 넣지 않는 편이 안전합니다.

```ini
GEMINI_API_KEY=
KAKAO_REST_API_KEY=
TMAP_OPEN_API_APP_KEY=
TOUR_API_SERVICE_KEY=
KEY_SERVER_TOKEN=
```

3. `check_api_keys(require_kakao=True)`가 요구하는 것은 Gemini와 Kakao입니다.  
   `TMAP_OPEN_API_APP_KEY` / `TOUR_API_SERVICE_KEY`가 없으면 해당 `if`만 건너뜁니다.
4. Kakao는 개발자 콘솔의 **REST API 키**만 씁니다. 보통 **32자 16진수**입니다.  
   같은 앱에서 **카카오맵 사용 설정 ON**이 없으면 `GET`이 403입니다.

발급 URL:

- Gemini: https://aistudio.google.com/apikey
- Kakao REST: https://developers.kakao.com/ → 앱 → REST API 키
- TMAP: https://openapi.sk.com/
- TourAPI: 공공데이터포털 (KorService2 + LocgoHubTarService1 + TarRlteTarService1 + TatsCnctrRateService, 같은 `serviceKey`)

### 방법 B. exe가 서버에서 제공자 키를 받을 때

`KEY_SERVER_TOKEN`은 Kakao/Google이 발급하지 않습니다. 이 PC에서 만들고 Render에 붙입니다.

만드는 명령, Render 클릭, `GET /api/keys` 확인은 **`main`이 아니라** `fastapi-web` 설명에 있습니다.

https://github.com/seongbin45/CODYSSEY_5_ProJect/tree/fastapi-web

exe 한 줄만 보면:

```bat
travel_planner.exe --key-server https://codyssey-5-project.onrender.com/api/keys --key-token 토큰 --date "2026-08-20" --model gemini-2.5-flash
```

`토큰`은 Render Environment의 `KEY_SERVER_TOKEN`과 같아야 합니다. 값 자체는 이 브랜치 README에 적지 않습니다.

---

## 4단계. 터미널에서 실행하기 (과제 본편)

날짜 형식은 반드시 `YYYY-MM-DD` 입니다. `-date`와 `--date` 둘 다 `dest="date"`입니다.

```bat
python travel_planner.py --date "2026-08-20" --model gemini-2.5-flash
```

`--model`을 빼면 `api_llm.select_model()`이 `GET /v1beta/models` 목록을 보여 주고 번호를 받습니다.  
`gemini-2.5-flash`처럼 `generateContent`가 되는 이름을 고르세요.  
`antigravity-`로 시작하는 이름은 이 프로그램의 `POST .../generateContent`와 맞지 않습니다 (400).

다른 인자:

```bat
python travel_planner.py --list-models
python travel_planner.py --verify-models
```

- `--list-models` : `list_models()`만 호출하고 종료. Kakao 키는 필요 없음.
- `--verify-models` : `verify_all_models()`가 모델을 하나씩 `generateContent`로 호출하고 `results/gemini_model_compat.json`을 씀. 이후 `select_model()`이 이 파일을 먼저 본다.

날짜가 `YYYY-MM-DD`가 아니면 `parser.print_help()` 후 종료합니다.  
같은 날짜의 `results/YYYY-MM-DD_raw_data.json`이 있으면 `load_cached_data()`가 그 dict를 읽고, 1~4단계 HTTP를 다시 하지 않습니다. 처음부터 다시 받으려면 그 JSON을 지웁니다.

---

## 5단계. 웹으로 실행하기

브라우저가 키를 받지 않습니다. 키는 `server/app.py`가 돌아가는 프로세스의 환경변수에만 있습니다.

로컬:

```bat
uvicorn server.app:app --reload --port 8000
```

브라우저: http://127.0.0.1:8000  
폼의 **리포트 생성**은 `POST /api/plan` (`multipart/form-data`, 필드 `date`, `model`)입니다.

인터넷 배포본: https://codyssey-5-project.onrender.com  
코드: https://github.com/seongbin45/CODYSSEY_5_ProJect  

클릭 순서는 [DEPLOY.md](DEPLOY.md), 주소 표는 [server/README.md](server/README.md)입니다.

---

## 6단계. 결과 확인

실행이 끝나면 `results/`에 파일이 생깁니다.

- `YYYY-MM-DD_raw_data.json` : `recommendation`, `restaurants`, `tour_places`, `transit_legs`, `errors`
- `YYYY-MM-DD_travel_plan.md` : `generate_report()`가 받은 Markdown

웹에서는 `index.html`의 **저장된 리포트 저장소 열기**가 `GET /results`로 갑니다.

---

## 7단계. exe 만들기 (`.env`를 묶지 않음)

```bat
pip install pyinstaller
pyinstaller --noconfirm --clean --distpath export --workpath build travel_planner.spec
```

나온 파일: `export\travel_planner.exe`  
`travel_planner.spec`의 `datas=[]`이므로 제공자 키가 exe 안에 들어가지 않습니다.  
실행 인자는 [export/README.md](export/README.md)를 봅니다.

이미 만든 exe는 Git이 아니라 Release에 있습니다.

- https://github.com/seongbin45/CODYSSEY_5_ProJect/releases/tag/v1.0.0
- https://github.com/seongbin45/CODYSSEY_5_ProJect/releases/download/v1.0.0/travel_planner.exe

---

## 브랜치

- `main` (지금 문서) : 과제 CLI. 로컬 `.env`에 제공자 키를 두고 `python travel_planner.py --date ...`
- `fastapi-web` : Render 웹과 `GET /api/keys`. **토큰 만드는 법, Render Environment, exe가 키를 받는 순서**는 이쪽 README가 `main`과 다릅니다.  
  https://github.com/seongbin45/CODYSSEY_5_ProJect/tree/fastapi-web

두 브랜치의 README를 같게 맞추지 않습니다.

`.env`, `KEY_SERVER_TOKEN` 값, `export/*.exe`, `docs/*.zip`은 GitHub에 올리지 않습니다. (`.gitignore`)
