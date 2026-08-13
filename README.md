# fastapi-web — Render 웹 서버와 키 받기

이 브랜치는 **`main`과 설명이 다릅니다.**

| | `main` | 지금 보고 있는 `fastapi-web` |
|---|---|---|
| 무엇을 하나 | 과제 CLI `python travel_planner.py --date ...` | 브라우저 웹 + exe가 키를 받아 가는 서버 |
| 배포 | 없음 | Render가 이 브랜치를 읽어 https://codyssey-5-project.onrender.com 을 켬 |
| 제공자 키 | 로컬 `.env` | Render Environment |
| `KEY_SERVER_TOKEN` | CLI만 쓰면 없어도 됨 | exe가 `GET /api/keys`를 부를 때 **반드시** 필요 |

과제 본편(날짜 → Gemini JSON → Kakao GET → Markdown)은 `main`을 봅니다.  
https://github.com/seongbin45/CODYSSEY_5_ProJect/tree/main

이 파일은 **웹을 다시 올리고, 토큰을 만들고, exe가 서버에서 키를 받게** 하는 순서입니다. 위에서 아래로 따라 하면 됩니다.

---

## 0단계. 두 가지 비밀을 섞지 말 것

| 이름 | 누가 주나 | 어디에 붙이나 | 브라우저/exe에 넣나 |
|---|---|---|---|
| `GEMINI_API_KEY`, `KAKAO_REST_API_KEY`, `TMAP_OPEN_API_APP_KEY`, `TOUR_API_SERVICE_KEY` | 각 사이트 콘솔 | Render Environment | 아니요. 서버만 가짐 |
| `KEY_SERVER_TOKEN` | **아무도 안 줌. 이 PC에서 만듦** | Render Environment (exe 쓸 때는 로컬 `.env`에도 같은 값) | 브라우저에는 안 넣음. exe만 `--key-token`으로 냄 |

웹 페이지에서 **리포트 생성**만 하면 토큰은 필요 없습니다.  
토큰이 필요한 경우는 하나뿐입니다. `travel_planner.exe`(또는 로컬 CLI)가 `GET /api/keys`로 **제공자 키 JSON을 받아 갈 때**입니다.

`GET /api/keys`는 인터넷에 열려 있습니다. 토큰이 없으면 아무나 제공자 키를 가져갑니다.  
그래서 `server/app.py`의 `api_keys()`는 헤더 `Authorization: Bearer {KEY_SERVER_TOKEN}`이 맞을 때만 200을 줍니다.

---

## 1단계. `KEY_SERVER_TOKEN` 만들기 (발급 사이트가 없음)

Google / Kakao / SK / 공공데이터포털 어디에도 `KEY_SERVER_TOKEN` 메뉴는 없습니다.  
우리가 무작위 문자열을 하나 만들고, 서버와 exe가 **같은 문자열**을 쓰게 하면 그게 토큰입니다.

### 1-1. Python 3.10이 있는지

```bat
python --version
```

`Python 3.10` 이상이 나와야 합니다. Windows Store 안내만 나오면:

```bat
C:\Users\seong\AppData\Local\Programs\Python\Python310\python.exe --version
```

아래 `python`을 그 전체 경로로 바꿔도 됩니다.

### 1-2. 이 브랜치를 받은 폴더로 이동

```bat
cd C:\Users\seong\Downloads\CODYSSEY_5_ProJect
git checkout fastapi-web
```

### 1-3. 토큰 문자열 출력

아래 둘 중 **하나만** 하면 됩니다. 결과는 같은 종류의 문자열입니다.

```bat
python scripts\make_key_server_token.py
```

또는 한 줄:

```bat
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

출력 예 (이 예 값을 쓰지 마세요. 매번 다릅니다):

```
xK3...여기_43자_안팎...
```

`secrets.token_urlsafe(32)`는 32바이트 난수를 URL에 넣기 안전한 문자로 바꾼 것입니다. 보통 43자입니다.

### 1-4. 나온 첫 줄을 어디에 붙이나

1. 메모장에 잠시 복사합니다. **GitHub, README, Release, 채팅 공개 채널에는 올리지 않습니다.**
2. Render Environment의 `KEY_SERVER_TOKEN`에 붙입니다. (3단계)
3. exe를 이 PC에서 시험할 때만, 프로젝트 루트 `.env`에 아래처럼 붙입니다. 따옴표 없이.

```ini
KEY_SERVER_TOKEN=여기에_1-3에서_나온_첫_줄
```

4. 평가자에게 exe를 쓰게 하려면, 제출 안내(비공개)에 `--key-token` 값으로만 알려 줍니다.

토큰을 잃어버리면 다시 1-3을 실행해 **새 문자열**을 만들고, Render와 `.env`를 **둘 다** 그 새 값으로 바꿉니다. 한쪽만 바꾸면 exe가 401을 받습니다.

### 1-5. 잘 붙였는지 확인 (3단계 배포 후)

브라우저 주소창에 `https://codyssey-5-project.onrender.com/api/keys` 만 치면 **401** 이어야 합니다.  
토큰 없이 200이 나오면 검사가 빠진 것입니다.

PowerShell에서 토큰을 넣어 확인 (값은 본인 것으로):

```powershell
$t = "여기에_토큰"
Invoke-RestMethod -Headers @{ Authorization = "Bearer $t" } -Uri "https://codyssey-5-project.onrender.com/api/keys"
```

| HTTP | 의미 | 다음에 할 일 |
|---|---|---|
| 200 + JSON에 `GEMINI_API_KEY` 등 | 토큰과 제공자 키가 맞음 | exe `--key-token`에 같은 값 |
| 401 `unauthorized` | 보낸 토큰 ≠ Render 값 | 1-3을 다시 하거나 Render 값을 다시 붙임 |
| 500 `서버에 KEY_SERVER_TOKEN 이 없습니다.` | Render에 이름 자체가 없음 | Environment에 `KEY_SERVER_TOKEN` 줄을 **추가** |
| 한참 기다림 / 실패 | 무료 인스턴스가 잠자기 | 30초 뒤 `/health`부터 다시 |

응답 JSON이 터미널에 보이면 키가 노출된 것입니다. 스크린샷을 GitHub에 올리지 마세요.

---

## 2단계. 제공자 키 발급 (이건 각 사이트에서)

토큰과 별개입니다. 값이 생긴 뒤 Render Environment에 붙입니다. `.py`에 쓰지 않습니다.

| 환경변수 이름 | 어디서 받나 | 넣을 때 주의 |
|---|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey | Create API key |
| `KAKAO_REST_API_KEY` | https://developers.kakao.com/ → 앱 → **REST API 키** | 보통 32자 16진수. `KakaoAK `와 따옴표 금지. 같은 앱에서 **카카오맵 사용 설정 ON** |
| `TMAP_OPEN_API_APP_KEY` | https://openapi.sk.com/ | 없으면 이동 구간만 생략 |
| `TOUR_API_SERVICE_KEY` | 공공데이터포털 (KorService2 + 데이터랩 3종, 같은 serviceKey) | 없으면 관광지/숙소만 생략 |

웹 **리포트 생성**은 Gemini + Kakao만 있어도 됩니다.

---

## 3단계. Render에 이 브랜치를 올리기

이미 `https://codyssey-5-project.onrender.com` 이 있으면 3-1은 건너뛰고 3-2만 하면 됩니다.

### 3-1. 서비스를 처음 만들 때

1. GitHub에 `fastapi-web` 브랜치가 푸시되어 있는지 확인: https://github.com/seongbin45/CODYSSEY_5_ProJect/tree/fastapi-web
2. https://dashboard.render.com/ → **New** → **Web Service**
3. 저장소 `seongbin45/CODYSSEY_5_ProJect` 연결
4. **Branch**를 `fastapi-web` 으로 둠 (`main`이 아님)
5. `render.yaml` / Docker 가 잡히면 그대로 둠
6. 3-2를 채운 뒤 **Deploy**

### 3-2. Environment에 이름과 값을 넣기

Render → 해당 Web Service → **Environment** → **Add Environment Variable**

이름은 아래와 **한 글자도 같게** 만듭니다. 값은 대시보드에만 붙입니다.

```
GEMINI_API_KEY
KAKAO_REST_API_KEY
TMAP_OPEN_API_APP_KEY
TOUR_API_SERVICE_KEY
KEY_SERVER_TOKEN
```

- `KEY_SERVER_TOKEN` 값 = 1-3에서 만든 첫 줄
- 저장 후 Render가 다시 배포하는지 확인. 안 하면 **Manual Deploy** → **Deploy latest commit**

`render.yaml`에 위 이름이 적혀 있어도 **값은 Git에 없습니다.** 대시보드에서 직접 붙여야 합니다.

### 3-3. 배포가 됐는지

1. 브라우저: https://codyssey-5-project.onrender.com  
   제목 **국내 여행지 추천**, 날짜 칸이 보이면 `GET /` 성공
2. https://codyssey-5-project.onrender.com/health  
   `kakao: true` 이고 `kakao_key_len` 이 **32** 인지
3. 1-5의 `/api/keys` 표

클릭 단위 메모는 [DEPLOY.md](DEPLOY.md)에도 있습니다.

---

## 4단계. 브라우저에서 리포트 만들기 (토큰 불필요)

1. https://codyssey-5-project.onrender.com
2. 여행 날짜를 고름
3. 모델은 `gemini-2.5-flash` (기본)
4. **리포트 생성** → 브라우저가 `POST /api/plan` (`date`, `model`)을 보냄
5. 20~40초 뒤 로그와 Markdown이 보임
6. **저장된 리포트 저장소 열기** → `GET /results`

키는 HTML에 없고, 응답 JSON에도 없습니다. 서버 환경변수만 사용합니다.

---

## 5단계. exe가 서버에서 키를 받을 때 (토큰 필요)

exe: https://github.com/seongbin45/CODYSSEY_5_ProJect/releases/download/v1.0.0/travel_planner.exe

```bat
travel_planner.exe --key-server https://codyssey-5-project.onrender.com/api/keys --key-token 토큰 --date "2026-08-20" --model gemini-2.5-flash
```

`토큰` = Render의 `KEY_SERVER_TOKEN`과 같은 문자열.

동작:

1. exe가 `GET /api/keys` + `Authorization: Bearer 토큰`
2. `api_keys()`가 `token_matches()`로 비교
3. 맞으면 `GEMINI_API_KEY` 등 네 이름을 JSON으로 줌
4. exe가 그 키로 Gemini/Kakao를 호출
5. 결과는 **exe와 같은 폴더**의 `results\`

`--key-server`를 생략하고 exe 옆에 `.env`에도 `GEMINI_API_KEY`가 없으면,  
`src/utils.py`의 `load_runtime_env()`가 `https://codyssey-5-project.onrender.com/api/keys`를 씁니다. 그래도 토큰은 필요합니다.

---

## 6단계. 이 PC에서 웹만 켜 보기

제공자 키는 루트 `.env`에 둡니다. `KEY_SERVER_TOKEN`은 로컬에서 `/api/keys`를 시험할 때만 필요합니다.

```bat
cd C:\Users\seong\Downloads\CODYSSEY_5_ProJect
git checkout fastapi-web
pip install -r requirements.txt
uvicorn server.app:app --reload --port 8000
```

브라우저: http://127.0.0.1:8000

---

## 이 브랜치에서 볼 문서

| 파일 | 내용 |
|---|---|
| [DEPLOY.md](DEPLOY.md) | Render 클릭만 모아 둔 것 |
| [scripts/README.md](scripts/README.md) | `make_key_server_token.py` |
| [server/README.md](server/README.md) | `/`, `/api/plan`, `/api/keys` |
| [server/templates/README.md](server/templates/README.md) | `index.html` |
| [src/README.md](src/README.md) | `run_pipeline()`과 API 함수 |
| [export/README.md](export/README.md) | exe 인자 |

`.env`와 토큰 값은 GitHub에 올리지 않습니다.
