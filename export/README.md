# `export/` — 평가용 실행 파일

이 폴더에는 PyInstaller가 만든 `travel_planner.exe`가 들어갑니다.  
소스 파이썬이 없는 Windows에서도 터미널로 과제를 실행할 수 있습니다.

exe 자체는 GitHub에 올리지 않습니다. 이 설명 파일만 올립니다.

---

## 1. exe가 하는 일 / 하지 않는 일

하는 일:

- 날짜를 받아 서버(또는 로컬 `.env`)에서 키를 준비한 뒤
- Gemini → Kakao → (TourAPI) → (TMAP) → 리포트
- exe와 **같은 폴더**의 `results/`에 JSON/MD 저장

하지 않는 일:

- 제공자 API 키를 파일 안에 넣지 않음
- 웹 화면을 띄우지 않음 (검은 콘솔 창)

---

## 2. 만들기 (개발자 PC)

프로젝트 루트에서:

```bat
cd C:\Users\seong\Downloads\CODYSSEY_5_ProJect
pip install pyinstaller
pyinstaller --noconfirm --clean --distpath export --workpath build travel_planner.spec
```

`travel_planner.spec`이 설계도입니다.

- 한 파일(`onefile`)
- 콘솔 프로그램
- `.env`를 묶지 않음
- `src` 폴더를 모듈 검색 경로에 넣음

끝나면 여기에 `travel_planner.exe`가 생깁니다.

---

## 3. 평가자가 실행하는 순서

1. `travel_planner.exe`만 받습니다. (또는 이 폴더 전체)
2. 인터넷이 되는 PC에서 명령 프롬프트/PowerShell을 엽니다.
3. exe가 있는 폴더로 이동합니다.
4. 키는 exe 안이 아니라 **Render 서버**에서 받습니다.

```bat
travel_planner.exe --key-server https://codyssey-5-project.onrender.com/api/keys --key-token 토큰 --date "2026-08-20" --model gemini-2.5-flash
```

5. 끝나면 같은 폴더에 `results\2026-08-20_travel_plan.md`가 생깁니다.

토큰은 제출자가 Render에 넣어 둔 `KEY_SERVER_TOKEN`과 같아야 합니다.  
토큰을 채팅이나 GitHub에 올리지 마세요.

다른 명령:

```bat
travel_planner.exe --help
travel_planner.exe --list-models --key-server https://codyssey-5-project.onrender.com/api/keys --key-token 토큰
```

---

## 4. 키가 서버가 아니라 파일에 있을 때

exe 옆에 `.env`를 두면 그 값이 우선입니다.  
개발자가 자기 PC에서만 시험할 때 씁니다. 평가용으로 키를 넣어 배포하지 마세요.

---

## 5. 안 될 때

- “키 서버 인증 실패” : 토큰이 틀렸거나 Render에 `KEY_SERVER_TOKEN`이 없음
- “키 서버 요청 실패” : 주소가 틀렸거나 Render가 잠자기 후 아직 안 깨어남. 30초 뒤 다시
- Kakao 401 : 서버에 넣은 Kakao 키가 REST 키가 아니거나 잘림 (보통 32자)
- 모델 400 : `antigravity-` 같은 모델을 고름. `gemini-2.5-flash`를 지정

---

위로: [프로젝트 README](../README.md)  
키 서버 주소의 구현: [server/README.md](../server/README.md)
