# `export/` — PyInstaller가 `travel_planner.exe`를 넣는 폴더

`pyinstaller --distpath export travel_planner.spec`이 끝나면 여기에 `travel_planner.exe`가 생깁니다.  
Python이 없는 Windows에서도 같은 argparse를 쓸 수 있습니다.

exe는 Git 커밋에 넣지 않습니다 (`.gitignore`의 `export/*` + `!export/README.md`).  
받으려면 Release를 엽니다.

- 릴리스: https://github.com/seongbin45/CODYSSEY_5_ProJect/releases/tag/v1.0.0
- 직접 받기: https://github.com/seongbin45/CODYSSEY_5_ProJect/releases/download/v1.0.0/travel_planner.exe

---

## 1. exe가 하는 일 / 하지 않는 일

하는 일:

- `travel_planner.py`의 `main()`과 같은 인자 (`--date`, `--model`, `--key-server`, `--key-token`, `--list-models`, `--verify-models`)
- `utils.load_runtime_env()`로 `.env` 또는 `GET /api/keys`에서 키를 환경변수에 넣음
- `get_recommendation` → `search_restaurants` → (`search_official_places`) → (`build_travel_legs`) → `generate_report`
- `app_dir()`이 exe 폴더이므로, 결과는 **exe와 같은 폴더**의 `results\`에 저장

하지 않는 일:

- `travel_planner.spec`의 `datas=[]`이므로 제공자 키를 exe 안에 넣지 않음
- 브라우저를 열지 않음 (`console=True` 콘솔 프로그램)

---

## 2. 만들기 (개발자 PC)

프로젝트 루트에서:

```bat
cd C:\Users\seong\Downloads\CODYSSEY_5_ProJect
pip install pyinstaller
pyinstaller --noconfirm --clean --distpath export --workpath build travel_planner.spec
```

`travel_planner.spec`이 정하는 값:

- `Analysis(['travel_planner.py'], pathex=['src'], datas=[])`
- `hiddenimports`에 `api_llm`, `api_map`, `api_tmap`, `api_tour`, `utils`, `key_client` 등
- `EXE(..., name='travel_planner', console=True)` — onefile

끝나면 이 폴더에 `travel_planner.exe`가 생깁니다. 중간 파일은 `build/`입니다.

---

## 3. 평가자가 실행하는 순서

1. `travel_planner.exe`만 받습니다. (또는 이 폴더 전체)
2. 인터넷이 되는 PC에서 cmd 또는 PowerShell을 엽니다.
3. exe가 있는 폴더로 이동합니다.
4. 제공자 키는 exe 안이 아니라 Render `GET /api/keys`에서 받습니다.

```bat
travel_planner.exe --key-server https://codyssey-5-project.onrender.com/api/keys --key-token 토큰 --date "2026-08-20" --model gemini-2.5-flash
```

`--key-server`를 생략하고 exe 옆에 `.env`에도 `GEMINI_API_KEY`가 없으면,  
`load_runtime_env()`가 `https://codyssey-5-project.onrender.com/api/keys`를 씁니다.  
그 경우에도 `--key-token` 또는 `.env`의 `KEY_SERVER_TOKEN`이 필요합니다.

5. 끝나면 같은 폴더에 `results\2026-08-20_travel_plan.md`가 생깁니다.

토큰은 Render Environment의 `KEY_SERVER_TOKEN`과 같아야 합니다.  
Kakao/Google이 주는 값이 아닙니다. 이 브랜치에서 만듭니다.

```bat
python scripts\make_key_server_token.py
```

출력 첫 줄을 Render와 `--key-token`에 똑같이 씁니다. 채팅·GitHub·Release 본문에는 올리지 마세요.  
단계: [루트 README 1단계](../README.md)

다른 명령:

```bat
travel_planner.exe --help
travel_planner.exe --list-models --key-server https://codyssey-5-project.onrender.com/api/keys --key-token 토큰
```

---

## 4. exe 옆에 `.env`가 있을 때

`load_runtime_env()`는 `app_dir()/.env`(exe와 같은 폴더)를 `override=True`로 읽습니다.  
이미 `GEMINI_API_KEY`가 있으면 `--key-server`를 안 준 한 서버를 부르지 않습니다.

개발자 PC에서만 이렇게 시험합니다. 평가용으로 `.env`를 exe와 같이 배포하지 마세요.

---

## 5. 콘솔에 나오는 메시지

- `키 서버 인증 실패` : `--key-token`이 틀렸거나 Render에 `KEY_SERVER_TOKEN`이 없음 (HTTP 401/403)
- `키 서버 요청 실패` : URL이 틀렸거나 Render가 잠자기 후 아직 안 깨어남. 30초 뒤 다시
- Kakao 401 / 키 길이 N자 : Render(또는 `.env`)의 `KAKAO_REST_API_KEY`가 REST 키가 아니거나 잘림. 보통 32자
- 모델 400 / `antigravity-` : `--model gemini-2.5-flash`를 지정

---

위로: [프로젝트 README](../README.md)  
`GET /api/keys` 구현: [server/README.md](../server/README.md)
