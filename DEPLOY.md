# FastAPI 배포 (fastapi-web 브랜치)

이 브랜치는 CLI와 같은 파이프라인을 **웹 서버**에서 돌립니다.  
제공자 API 키는 GitHub에 올리지 말고, 호스팅 대시보드 환경변수에만 넣습니다.

## GitHub에서 서버로 올리는 방법 (Render)

1. https://github.com/seongbin45/CODYSSEY_5_ProJect 의 `fastapi-web` 브랜치를 연다.
2. [Render](https://dashboard.render.com/) → New → Web Service → 이 저장소를 연결한다.
3. Branch를 `fastapi-web` 으로 둔다. `render.yaml`이 Docker 웹 서비스를 만든다.
4. Environment에 아래를 넣는다.

```
GEMINI_API_KEY
KAKAO_REST_API_KEY
TMAP_OPEN_API_APP_KEY
TOUR_API_SERVICE_KEY
```

5. Deploy 후 `https://<서비스>.onrender.com` 으로 평가한다.

키를 브라우저나 `/keys` 로 내려주지 않습니다. 페이지는 날짜만 받아 서버에서 리포트를 만듭니다.

## 로컬에서 웹만 확인할 때

```bash
pip install -r requirements.txt
uvicorn server.app:app --reload --port 8000
```

브라우저: http://127.0.0.1:8000

## 과제 CLI는 그대로

```bash
python travel_planner.py --date "2026-08-20" --model gemini-2.5-flash
```
