# 국내 여행지 추천 — 오늘 처음 실행하기 (`main`)

이 브랜치는 **과제용 터미널 프로그램**입니다.

날짜 하나를 넣으면, 이 PC가 인터넷으로 Gemini와 Kakao를 호출하고  
`results` 폴더에 여행 리포트 파일을 만듭니다.

웹 페이지·토큰·Render 설명은 여기에 없습니다. 그건 다른 브랜치입니다.  
https://github.com/seongbin45/CODYSSEY_5_ProJect/tree/fastapi-web

이 파일은 **위에서 아래로** 따라 하면 됩니다. 한 단계를 끝낸 뒤에 다음으로 가세요.

---

## 0. 준비물

- Windows PC, 인터넷
- Python 3.10 이상
- Google 계정 (Gemini 키)
- Kakao 개발자 계정 (REST API 키)

TMAP 키와 TourAPI 키는 **없어도** 과제의 최소 실행은 됩니다.  
없으면 관광지·이동 칸만 비고, 맛집 리포트는 그대로 만들어집니다.

---

## 1단계. 이 폴더로 이동

1. 파일 탐색기에서 `C:\Users\seong\Downloads\CODYSSEY_5_ProJect` 를 엽니다.
2. 주소창을 클릭하고 `powershell` 을 입력한 뒤 Enter.  
   그 폴더에서 PowerShell이 열립니다.
3. 아래를 붙여 넣고 Enter.

```bat
cd C:\Users\seong\Downloads\CODYSSEY_5_ProJect
```

폴더가 다른 곳에 있으면 `cd` 뒤 경로만 바꾸면 됩니다.

---

## 2단계. Python이 되는지 확인

```bat
python --version
```

**성공:** `Python 3.10.x` 또는 더 큰 숫자가 나옵니다. 3단계로 갑니다.

**실패 A — Microsoft Store 창이 열리거나 `Python was not found`:**

설치된 실행 파일을 직접 씁니다. 아래를 먼저 실행해 보세요.

```bat
C:\Users\seong\AppData\Local\Programs\Python\Python310\python.exe --version
```

이게 되면, 이 문서의 `python`을 전부 저 긴 경로로 바꿔 치면 됩니다.  
예:

```bat
C:\Users\seong\AppData\Local\Programs\Python\Python310\python.exe --version
```

**실패 B — 파일 자체가 없음:**  
https://www.python.org/downloads/ 에서 3.10 이상을 설치합니다.  
설치 화면에서 **Add python.exe to PATH** 에 체크합니다.  
설치가 끝나면 터미널을 **닫았다가 다시** 열고 2단계를 반복합니다.

---

## 3단계. 필요한 패키지 설치

같은 폴더에서:

```bat
python -m pip install -r requirements.txt
```

`python`이 안 되면 2단계의 긴 경로를 씁니다.

```bat
C:\Users\seong\AppData\Local\Programs\Python\Python310\python.exe -m pip install -r requirements.txt
```

끝날 때까지 기다립니다. `Successfully installed` 또는 `already satisfied` 가 보이면 됩니다.

---

## 4단계. 키 두 개 받기

키는 **비밀번호처럼** 취급합니다. `travel_planner.py` 같은 코드 파일에 붙여 넣지 않습니다.  
다음에 만들 `.env` 파일에만 넣습니다. GitHub에도 올리지 않습니다.

### 4-1. Gemini 키

1. 브라우저에서 https://aistudio.google.com/apikey 를 엽니다.
2. Google 계정으로 로그인합니다.
3. **Create API key** 를 누릅니다.
4. 나온 긴 문자열을 메모장에 복사합니다. 앞에 `GEMINI_API_KEY=` 는 아직 쓰지 마세요.

### 4-2. Kakao REST API 키

1. https://developers.kakao.com/ 를 엽니다.
2. 로그인 후 **내 애플리케이션** → **애플리케이션 추가하기**  
   이름은 아무거나 (예: `travel-planner`) 해도 됩니다.
3. 만든 앱을 엽니다.
4. **앱 키** 화면에서 **REST API 키** 를 복사합니다.  
   JavaScript 키, Admin 키가 아닙니다.
5. REST 키는 보통 **영문·숫자 32자**입니다. 앞뒤에 따옴표나 `KakaoAK` 를 붙이지 마세요.
6. 같은 앱에서 **카카오맵** → **이용 설정**을 **ON** 합니다.  
   OFF 이면 나중에 맛집이 0곳이고 오류에 403이 납니다.

TMAP·TourAPI는 지금 건너뛰어도 됩니다.

---

## 5단계. `.env` 파일 만들기

키를 저장하는 파일 이름은 `.env` 입니다. 예제 파일을 복사해서 만듭니다.

같은 폴더의 PowerShell에서:

```bat
copy .env.example .env
notepad .env
```

메모장이 열리면 `=` 오른쪽에만 값을 붙입니다. 이름(왼쪽)은 바꾸지 않습니다.

```ini
GEMINI_API_KEY=여기에_제미니_키
KAKAO_REST_API_KEY=여기에_카카오_REST키
TMAP_OPEN_API_APP_KEY=
TOUR_API_SERVICE_KEY=
```

지킬 것:

- `=` 양옆에 공백을 넣지 않습니다.
- 값에 `"따옴표"` 를 씌우지 않습니다.
- `KakaoAK ` 를 붙이지 않습니다.
- 저장(`Ctrl+S`)한 뒤 메모장을 닫습니다.
- `.env` 는 GitHub에 올리지 않습니다. 이미 `.gitignore`에 들어 있습니다.

`KEY_SERVER_TOKEN` 줄이 예제에 있어도, **이 브랜치에서 터미널로 실행할 때는 비워 두면 됩니다.**

---

## 6단계. 프로그램 실행

같은 폴더에서:

```bat
python travel_planner.py --date "2026-08-20" --model gemini-2.5-flash
```

`python`이 안 되면:

```bat
C:\Users\seong\AppData\Local\Programs\Python\Python310\python.exe travel_planner.py --date "2026-08-20" --model gemini-2.5-flash
```

날짜는 `YYYY-MM-DD` 만 됩니다. `2026-8-20` 이나 `26/08/20` 은 안 됩니다.

처음이면 인터넷으로 Gemini·Kakao를 부르므로 **수십 초** 걸릴 수 있습니다.

**성공하면** 마지막에 비슷한 문장이 나옵니다.

```
완료! ...\results\2026-08-20_travel_plan.md 를 확인하세요.
```

---

## 7단계. 결과 파일 열기

파일 탐색기에서 `C:\Users\seong\Downloads\CODYSSEY_5_ProJect\results` 를 엽니다.

| 파일 | 누가 읽나 |
|---|---|
| `2026-08-20_travel_plan.md` | 사람. 메모장이나 VS Code로 엽니다. |
| `2026-08-20_raw_data.json` | 프로그램이 저장한 원본. 도시 이름, 맛집 목록, 오류가 들어 있습니다. |

같은 날짜를 다시 실행하면, 이미 있는 `2026-08-20_raw_data.json` 을 재사용하고 리포트만 다시 씁니다.  
처음부터 다시 받으려면 그 JSON 파일을 지우고 6단계를 다시 하면 됩니다.

---

## 막히면 (화면에 나온 글자 기준)

| 화면에 보인 것 | 할 일 |
|---|---|
| `Python was not found` / Store 창 | 2단계. 긴 `python.exe` 경로를 쓰거나 Python을 다시 설치 |
| `No module named requests` | 3단계 `python -m pip install -r requirements.txt` 를 다시 |
| 날짜 오류 / 사용법만 출력 | `--date "2026-08-20"` 처럼 네 자리 연도-월-일, 따옴표 포함 |
| Gemini 키 없음 / API 키 안내 | `.env` 파일 이름과 위치가 프로젝트 폴더인지, `GEMINI_API_KEY=` 값이 비었는지 |
| Kakao 401, 키 길이가 32가 아님 | REST API 키를 다시 복사. 따옴표/`KakaoAK ` 제거 |
| Kakao 403 | 카카오 개발자 콘솔에서 그 앱의 **카카오맵 ON** |
| 맛집 0곳, 리포트는 있음 | 과제는 통과 가능. JSON의 `errors`를 열어 원인을 봄 |
| 모델 400 / `antigravity` | `--model gemini-2.5-flash` 를 그대로 씀 |
| 같은 날짜인데 예전 오류가 반복 | `results\그날짜_raw_data.json` 을 지우고 다시 실행 |

---

## 8단계. 그다음 (필요할 때만)

한 번 성공한 뒤에만 보면 됩니다.

**모델 목록만 보기**

```bat
python travel_planner.py --list-models
```

**모델을 지정하지 않고 목록에서 고르기**

```bat
python travel_planner.py --date "2026-08-20"
```

`gemini-2.5-flash` 처럼 일반 텍스트 모델만 고릅니다.

**이미 만든 exe 받기** (Python 없이 Windows에서 실행)

- https://github.com/seongbin45/CODYSSEY_5_ProJect/releases/tag/v1.0.0

exe는 제공자 키가 들어 있지 않습니다. 서버에서 키를 받으려면 토큰이 필요합니다.  
토큰 만드는 법: https://github.com/seongbin45/CODYSSEY_5_ProJect/tree/fastapi-web

**브라우저에서 쓰기** (이 브랜치 설명이 아님)

https://codyssey-5-project.onrender.com  
서버 올리는 순서: 위 fastapi-web 링크

---

## 과제가 보려는 것 (실행이 된 다음)

채점 포인트는 “날씨가 맞는지”가 아닙니다.

1. 인터넷으로 데이터를 **조회**하는 요청(`GET`)과, 본문을 **보내는** 요청(`POST`)을 구분할 것
2. Gemini가 준 JSON의 도시 이름을 Kakao 검색어로 넘길 것
3. 키 오류·네트워크 오류가 나도 프로그램이 죽지 않고 `errors`에 남길 것
4. 키를 `.py`에 쓰지 말고 `.env`에 둘 것

최소로 돌아가는 순서는 이렇습니다.

1. Gemini에게 날짜를 주고 도시·날씨·행사 JSON을 받는다 (`POST`)
2. 그 도시 이름으로 Kakao에서 맛집을 찾는다 (`GET`)
3. 그 결과를 다시 Gemini에게 주고 Markdown 리포트를 받는다 (`POST`)
4. `results` 폴더에 JSON과 MD를 저장한다

TourAPI·TMAP은 키가 있을 때만 추가됩니다.

코드가 어디 있는지는 실행 후에 [src/README.md](src/README.md)를 보면 됩니다.

---

## 폴더 (지금 당장 외울 필요 없음)

```
CODYSSEY_5_ProJect/
├── README.md              ← 지금 이 파일. 실행 순서
├── travel_planner.py      ← 터미널에서 실행하는 파일
├── requirements.txt       ← 3단계에서 설치하는 목록
├── .env.example           ← 5단계에서 복사하는 예제
├── .env                   ← 직접 만듦. GitHub에 올리지 않음
├── src/                   ← 실제 API를 호출하는 코드
├── results/               ← 7단계에서 열리는 결과
├── docs/                  ← 과제 원문. 프로그램이 읽지 않음
├── export/                ← exe를 다시 만들 때
└── server/                ← 웹. fastapi-web 브랜치에서 설명
```

---

## 이 브랜치와 다른 브랜치

| | `main` (지금) | `fastapi-web` |
|---|---|---|
| 하는 일 | 터미널로 리포트 만들기 | 웹 페이지 + exe가 키를 받아 가게 |
| 키 | 이 PC의 `.env` | Render 대시보드 |
| 토큰 | 필요 없음 | 필요할 때만. 그쪽 README 1단계 |

두 브랜치 README는 일부러 다르게 두었습니다.
