# FastAPI 배포 메모 (`main`에서는 요약만)

웹 서버·토큰 만들기·Render 클릭의 **전체 재현 순서**는 `fastapi-web`에 있습니다. 이 파일만 보고 따라 하지 마세요.

https://github.com/seongbin45/CODYSSEY_5_ProJect/tree/fastapi-web

아래는 주소만 적습니다.

---

## GitHub → Render

1. https://github.com/seongbin45/CODYSSEY_5_ProJect 의 `fastapi-web` 브랜치를 연다.
2. [Render](https://dashboard.render.com/) → New → Web Service → 이 저장소를 연결한다.
3. Branch를 `fastapi-web` 으로 둔다. `render.yaml`이 Docker 웹 서비스를 만든다.
4. Environment에 아래 **이름**을 만든다. 값은 대시보드에만 붙인다.

```
GEMINI_API_KEY
KAKAO_REST_API_KEY
TMAP_OPEN_API_APP_KEY
TOUR_API_SERVICE_KEY
KEY_SERVER_TOKEN
```

`KAKAO_REST_API_KEY`는 카카오 개발자 콘솔의 REST API 키(보통 32자 16진수)입니다. 따옴표와 `KakaoAK `를 붙이지 않습니다.  
`KEY_SERVER_TOKEN`은 로컬 `.env`의 같은 이름과 **완전히 같아야** `GET /api/keys`가 200을 줍니다.

5. Deploy 후 확인:

- 브라우저: `https://<서비스>.onrender.com` (`GET /`)
- `https://<서비스>.onrender.com/health` — `kakao: true`, `kakao_key_len`이 32인지
- 평가용 exe: `GET https://<서비스>.onrender.com/api/keys` + `Authorization: Bearer {KEY_SERVER_TOKEN}`

`/api/keys`는 화면 버튼이 아닙니다. 토큰이 틀리면 401, 서버에 토큰이 없으면 500입니다.  
`POST /api/plan` JSON과 `index.html`에는 제공자 키가 들어가지 않습니다.

무료 인스턴스는 꺼졌다가 첫 요청에 깨어납니다. `/app/results/`는 재시작 후 없을 수 있습니다.

---

## 로컬에서 웹만 확인할 때

프로젝트 루트에서 (cwd가 `.env`를 찾게):

```bat
pip install -r requirements.txt
uvicorn server.app:app --reload --port 8000
```

브라우저: http://127.0.0.1:8000

---

## 과제 CLI는 그대로

```bat
python travel_planner.py --date "2026-08-20" --model gemini-2.5-flash
```
