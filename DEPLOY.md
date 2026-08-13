# Render에 `fastapi-web`을 올리는 클릭 순서

이 파일은 **이 브랜치 전용**입니다. `main`의 과제 CLI 설명과 바꿔 쓰지 마세요.

루트 [README.md](README.md)의 1~3단계와 같습니다. 여기는 대시보드 클릭만 모아 둡니다.

---

## 토큰은 사이트에서 받지 않음

`KEY_SERVER_TOKEN`은 Google/Kakao가 발급하지 않습니다.

```bat
cd C:\Users\seong\Downloads\CODYSSEY_5_ProJect
git checkout fastapi-web
python scripts\make_key_server_token.py
```

출력 **첫 줄**을 복사합니다. 아래 Environment에 붙입니다.

---

## 서비스가 없을 때

1. https://github.com/seongbin45/CODYSSEY_5_ProJect/tree/fastapi-web 이 있는지 확인
2. https://dashboard.render.com/ → **New** → **Web Service**
3. 저장소 `CODYSSEY_5_ProJect` 연결
4. Branch: **`fastapi-web`** (`main` 아님)
5. Docker / `render.yaml` 사용
6. 아래 Environment를 채운 뒤 Create / Deploy

---

## Environment (값은 GitHub에 없음)

**Environment** → **Add Environment Variable**. 이름 철자를 그대로 씁니다.

| 이름 | 값의 출처 |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| `KAKAO_REST_API_KEY` | 카카오 개발자 콘솔 REST API 키 (보통 32자, 따옴표/`KakaoAK ` 없음, 카카오맵 ON) |
| `TMAP_OPEN_API_APP_KEY` | https://openapi.sk.com/ (없으면 그 단계만 생략) |
| `TOUR_API_SERVICE_KEY` | 공공데이터포털 serviceKey (없으면 그 단계만 생략) |
| `KEY_SERVER_TOKEN` | 위에서 만든 첫 줄. exe `--key-token`과 **완전히 같아야** 함 |

저장 후 재배포가 안 되면 **Manual Deploy** → **Deploy latest commit**.

---

## 배포 후 세 주소

현재 서비스: https://codyssey-5-project.onrender.com

1. `GET /` — 날짜 폼
2. `GET /health` — `kakao: true`, `kakao_key_len` 32
3. `GET /api/keys` — 토큰 없이 열면 **401**. 헤더 `Authorization: Bearer {토큰}`이 맞으면 200

`POST /api/plan`과 `index.html`에는 제공자 키가 없습니다.  
토큰과 키 JSON을 README/Release에 적지 않습니다.

무료 인스턴스는 꺼졌다가 첫 요청에 깨어납니다. `/app/results/`는 재시작 후 없을 수 있습니다.

---

## 로컬에서 웹만

```bat
pip install -r requirements.txt
uvicorn server.app:app --reload --port 8000
```

http://127.0.0.1:8000

과제 CLI는 `main` 브랜치에서:

```bat
git checkout main
python travel_planner.py --date "2026-08-20" --model gemini-2.5-flash
```
