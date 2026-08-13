# 국내 여행지 추천 프로그램 (처음부터 따라오기)

이 저장소는 **Codyssey 과제**용입니다.  
여행 날짜 하나를 넣으면, 여러 외부 API를 이어서 국내 여행 리포트(JSON + Markdown)를 만듭니다.

초심자는 이 파일을 **위에서 아래 순서**로 읽으면 됩니다.  
각 폴더의 세부 설명은 그 폴더 안의 `README.md`에 있습니다.

---

## 0단계. 이 프로그램이 하는 일

사람이 하는 일을 프로그램이 대신합니다.

1. 날짜를 받는다. 예: `2026-08-22`
2. AI(Gemini)에게 “이 날짜에 국내 어디가 좋은지” 물어 **JSON**으로 받는다.
3. 추천된 도시 이름으로 **Kakao**에서 맛집을 찾는다. (`GET`)
4. 있으면 **한국관광공사 TourAPI**로 관광지·숙소·혼잡도를 보강한다.
5. 있으면 **TMAP**으로 장소 사이 도보/대중교통 시간을 구한다.
6. 다시 Gemini에게 이 데이터를 주고 **Markdown 리포트**를 받는다.
7. `results/` 폴더에 원본 JSON과 리포트 MD를 저장한다.

과제가 중요하게 보는 것은 “날씨가 정확한가”가 아닙니다.  
**API를 여러 개 연결하고, JSON을 다음 단계 입력으로 쓰며, 키를 코드에 넣지 않는 것**입니다.

학습 목표 네 가지:

- REST의 `GET`(조회)과 `POST`(본문을 보내는 요청) 차이를 말할 수 있다.
- LLM 출력을 JSON으로 받아 지도 검색 입력으로 넘기는 흐름을 말할 수 있다.
- 인증/네트워크/파싱 오류가 나도 프로그램이 어떻게 대응하는지 말할 수 있다.
- 키를 `.env` 또는 서버 환경변수로 두는 이유를 말할 수 있다.

---

## 1단계. 폴더 지도 (어디에 무엇이 있나)

```
CODYSSEY_5_ProJect/
├── README.md                 ← 지금 읽고 있는 안내서
├── DEPLOY.md                 ← 웹 서버를 Render에 올리는 방법
├── 과제조건.txt              ← 원본 과제 화면(HTML) 저장본
├── travel_planner.py         ← 터미널에서 실행하는 입구
├── travel_planner.spec       ← exe 를 만들 때 쓰는 설계도
├── requirements.txt          ← 설치해야 하는 파이썬 패키지 목록
├── Dockerfile / render.yaml  ← 클라우드에 웹을 올릴 때 사용
├── .env.example              ← 키 이름만 있는 견본 (값은 없음)
├── src/                      ← 실제 계산과 API 호출 코드
├── server/                   ← 웹 페이지(FastAPI)
├── results/                  ← 실행 결과물 (자동 생성)
├── export/                   ← 만든 exe 가 나오는 곳
└── docs/                     ← 과제 정리, API 매뉴얼 등 참고 자료
```

다음으로 읽을 문서:

| 폴더 | 문서 | 내용 |
|---|---|---|
| `src/` | [src/README.md](src/README.md) | 파이프라인과 각 API 모듈 |
| `server/` | [server/README.md](server/README.md) | 웹 주소와 화면 |
| `server/templates/` | [server/templates/README.md](server/templates/README.md) | HTML 화면 파일 |
| `results/` | [results/README.md](results/README.md) | 저장되는 JSON/MD |
| `export/` | [export/README.md](export/README.md) | exe 실행 방법 |
| `docs/` | [docs/README.md](docs/README.md) | 참고 자료 목록 |

---

## 2단계. 컴퓨터 준비

1. Python **3.10 이상**이 있는지 확인합니다.

```bat
python --version
```

2. 이 폴더로 이동합니다.

```bat
cd C:\Users\seong\Downloads\CODYSSEY_5_ProJect
```

3. 필요한 패키지를 설치합니다. `requirements.txt`에 적힌 것만 설치됩니다.

```bat
pip install -r requirements.txt
```

들어 있는 것:

- `requests` : 인터넷으로 API를 호출
- `python-dotenv` : `.env` 파일을 읽어 환경변수로 만듦
- `fastapi`, `uvicorn`, `jinja2`, `python-multipart` : 웹 서버용

---

## 3단계. API 키를 어디에 두나

키는 **두 가지 중 하나**로 넣습니다. 둘 다 코드 파일에는 적지 않습니다.

### 방법 A. 내 PC에서 개발할 때 (가장 단순)

1. 프로젝트 루트에 `.env` 파일을 만듭니다. (`.env.example`을 복사해도 됩니다.)
2. 아래 이름을 그대로 쓰고, `=` 뒤에 본인 키만 붙입니다. 따옴표는 넣지 않습니다.

```ini
GEMINI_API_KEY=
KAKAO_REST_API_KEY=
TMAP_OPEN_API_APP_KEY=
TOUR_API_SERVICE_KEY=
KEY_SERVER_TOKEN=
```

3. 필수 키는 Gemini와 Kakao입니다. TMAP, TourAPI는 없으면 그 단계만 건너뜁니다.
4. Kakao는 **REST API 키**만 씁니다. 보통 **32자 16진수**입니다.  
   개발자 콘솔에서 **카카오맵 사용 설정 ON**이 필요합니다.

발급 위치:

- Gemini: https://aistudio.google.com/apikey
- Kakao REST: https://developers.kakao.com/ → 앱 → REST API 키
- TMAP: https://openapi.sk.com/
- TourAPI: 공공데이터포털 (국문 관광정보 + 데이터랩 3종, 같은 서비스키)

### 방법 B. 평가용 exe / 다른 PC (서버에서 키를 받음)

1. 웹 서버(Render) 환경변수에 제공자 키와 `KEY_SERVER_TOKEN`을 넣어둡니다.
2. 클라이언트는 제공자 키를 갖지 않고, 토큰만 들고 서버의 `/api/keys`를 호출합니다.
3. 서버가 토큰을 확인한 뒤에만 키 JSON을 줍니다.

```bat
python travel_planner.py --key-server https://codyssey-5-project.onrender.com/api/keys --key-token 토큰 --date "2026-08-20" --model gemini-2.5-flash
```

토큰이 틀리면 401입니다.  
로컬 `.env`에 이미 Gemini 키가 있으면 서버에서 다시 받아오지 않습니다.

---

## 4단계. 터미널에서 실행하기 (과제 본편)

날짜 형식은 반드시 `YYYY-MM-DD` 입니다. `-date`와 `--date` 둘 다 됩니다.

```bat
python travel_planner.py --date "2026-08-20" --model gemini-2.5-flash
```

`--model`을 빼면 Gemini가 가진 모델 목록을 보여 주고 고르게 합니다.  
`gemini-2.5-flash`처럼 일반 텍스트 모델을 고르세요. `antigravity-...` 같은 에이전트 모델은 이 프로그램과 맞지 않습니다.

다른 명령:

```bat
python travel_planner.py --list-models
python travel_planner.py --verify-models
```

`--verify-models`는 모델을 하나씩 실제로 호출해 텍스트+JSON이 되는지 검사합니다.  
결과는 `results/gemini_model_compat.json`에 남고, 이후 선택 화면은 이 실측을 우선합니다.

날짜가 잘못되면 사용법을 출력하고 끝납니다.  
같은 날짜를 다시 실행하면 캐시된 JSON을 쓰고 리포트만 다시 만듭니다. 처음부터 다시 하려면 그 JSON을 지우세요.

---

## 5단계. 웹으로 실행하기

브라우저에서 날짜를 넣고 리포트를 받습니다. 키는 브라우저로 내려가지 않습니다.

로컬:

```bat
uvicorn server.app:app --reload --port 8000
```

브라우저: http://127.0.0.1:8000

인터넷 배포본: https://codyssey-5-project.onrender.com  
코드: https://github.com/seongbin45/CODYSSEY_5_ProJect  

자세한 배포는 [DEPLOY.md](DEPLOY.md)와 [server/README.md](server/README.md)를 봅니다.

---

## 6단계. 결과 확인

실행이 끝나면 `results/`에 파일이 생깁니다.

- `YYYY-MM-DD_raw_data.json` : 1차 추천, 맛집, 관광지, 이동, 오류 목록
- `YYYY-MM-DD_travel_plan.md` : 사람이 읽는 리포트

웹에서는 **저장된 리포트 저장소 열기** 버튼으로 `/results`에 갑니다.

---

## 7단계. exe 만들기 (키는 넣지 않음)

```bat
pip install pyinstaller
pyinstaller --noconfirm --clean --distpath export --workpath build travel_planner.spec
```

나온 파일: `export\travel_planner.exe`  
제공자 키는 들어 있지 않습니다. 실행 방법은 [export/README.md](export/README.md)를 봅니다.

---

## 브랜치

- `main` : 정리된 전체 코드 (지금 폴더)
- `fastapi-web` : Render가 배포할 때 보는 브랜치. 내용은 main과 맞춰 두었습니다.

키, `.env`, exe, zip 매뉴얼은 GitHub에 올리지 않습니다.
