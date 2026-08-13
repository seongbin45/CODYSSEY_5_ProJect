# 국내 여행지 추천 프로그램 (Travel Planner)

> FastAPI 웹 배포는 `fastapi-web` 브랜치의 [DEPLOY.md](DEPLOY.md)를 본다. 키는 GitHub에 올리지 않는다.

이 프로젝트는 **LLM API(Gemini)**와 **지도/장소 검색 API(Kakao Local)**를 조합하여, 특정 시기에 여행하기 좋은 국내 도시를 추천하고 맛집 정보를 포함한 여행 리포트를 자동 생성하는 파이프라인(CLI 프로그램)입니다.

---

## 1. 개요 및 파이프라인

단일 API 호출이 아니라, 이전 단계의 결과를 다음 단계의 입력으로 활용하는 흐름을 보여줍니다.

1. **사용자 입력**: 여행 날짜 (예: `2026-03-15`)
2. **1단계 (LLM)**: 날씨/행사 등을 고려해 여행하기 좋은 도시 1곳을 추천하고, 결과를 구조화된 JSON으로 강제 파싱합니다. (`POST` 요청)
3. **2단계 (Map)**: 1단계에서 추천받은 도시 이름을 기반으로 해당 지역의 맛집 정보를 검색합니다. (`GET` 요청)
4. **3단계 (TourAPI, 선택)**: 추천 도시의 공인 관광지/숙소를 조회합니다. 키가 없으면 건너뜁니다.
5. **4단계 (TMAP, 선택)**: 맛집 좌표를 이어 도보/대중교통 이동 시간을 조회합니다. 키가 없으면 건너뜁니다.
6. **5단계 (LLM)**: 추천·맛집·관광지·이동 정보를 합쳐 최종 여행 리포트(Markdown)를 생성합니다.

> **학습 목표**
> - REST API의 `GET`/`POST` 차이 이해 (requests를 이용한 직접 호출)
> - LLM 출력을 구조화(JSON)하여 다른 API의 입력으로 연계
> - 네트워크, 인증, 파싱 등 다양한 오류 상황(Error Handling) 대처
> - API 키를 소스코드에 하드코딩하지 않고 `.env`를 통해 안전하게 관리

---

## 2. 사전 준비 및 API 키 설정

필수 키는 2개입니다. TMAP은 있으면 일정 이동 정보를 보강합니다. **API 키는 절대 외부에 노출하지 마세요.**

### 2-1. 키 발급 위치

- **Google Gemini API Key**: [Google AI Studio](https://aistudio.google.com/apikey)에서 무료로 발급 가능
- **Kakao REST API Key**: [Kakao Developers](https://developers.kakao.com/) → 내 애플리케이션 → 애플리케이션 추가 → **REST API 키** 복사. 제품 설정에서 카카오맵을 ON
- **TMAP appKey (선택)**: [SK open API](https://openapi.sk.com/) → 앱 키(`TMAP_OPEN_API_APP_KEY`). Free TMAP + Free TMAP 대중교통
- **TourAPI 서비스키 (선택)**: 같은 `TOUR_API_SERVICE_KEY`로 아래를 사용합니다.
  - [국문 관광정보 KorService2](https://www.data.go.kr/data/15101578/openapi.do) — 공식 관광지/숙소
  - [관광지 집중률](https://www.data.go.kr/data/15128555/openapi.do)
  - [중심 관광지](https://www.data.go.kr/data/15128559/openapi.do)
  - [연관 관광지](https://www.data.go.kr/data/15128560/openapi.do)

### 2-2. API 키 설정 방법

프로젝트 루트 폴더에 `.env` 파일을 생성하고 키를 입력합니다.

```ini
# .env 파일 예시 (값은 넣지 말고 로컬에서만 채우세요)
GEMINI_API_KEY=
KAKAO_REST_API_KEY=
TMAP_OPEN_API_APP_KEY=
TOUR_API_SERVICE_KEY=
```

또는 운영체제 환경변수로 직접 설정할 수 있습니다.
- (macOS/Linux): `export GEMINI_API_KEY="your_key"`
- (Windows PowerShell): `$env:GEMINI_API_KEY="your_key"`

---

## 3. 실행 방법

### 3-1. 의존성 패키지 설치

Python 3.10 이상이 설치된 환경에서 다음 명령어를 실행합니다.

```bash
pip install -r requirements.txt
```

### 3-2. 프로그램 실행

터미널에서 `-date` 파라미터와 함께 실행합니다. 날짜는 반드시 `YYYY-MM-DD` 형식이어야 합니다.

```bash
python travel_planner.py -date "2026-03-15"
```

모델 이름은 코드에 고정하지 않습니다. 실행 시 Gemini `models.list`로 **이 API 키가 조회할 수 있는 모델 전체**를 받은 뒤, 번호나 모델 이름으로 고릅니다. 임베딩·이미지 전용처럼 `generateContent`가 없는 모델은 목록에는 보이지만 선택할 수 없습니다.

스크립트나 재실행이라면 `--model`로 건너뛸 수 있습니다.

```bash
python travel_planner.py --date "2026-03-15" --model gemini-2.5-flash
python travel_planner.py --list-models
python travel_planner.py --verify-models
```

`--verify-models`는 키가 볼 수 있는 모델을 하나씩 실제 호출합니다. 텍스트 생성과 JSON 생성이 모두 되면 통과로 저장하고, 이후 선택 화면은 그 실측 결과를 씁니다. 결과는 `results/gemini_model_compat.json`에 남습니다.

---

## 3-3. 키 서버 (평가용, 권장)

제공자 API 키는 exe에 넣지 않습니다. 평가 전에 제출자가 키 서버를 켜고, 평가자는 주소와 토큰만 사용합니다.

제출자:

```bat
python key_server.py --host 0.0.0.0 --port 8787
```

평가자:

```bat
travel_planner.exe --key-server http://제출자IP:8787/keys --key-token 토큰 --date "2026-08-20" --model gemini-2.5-flash
```

토큰은 `.env`의 `KEY_SERVER_TOKEN`입니다. 제공자 키를 모르면 401입니다.

exe를 다시 만들 때 `.env`는 포함하지 않습니다.

```bat
pip install pyinstaller
pyinstaller --noconfirm --clean --distpath export --workpath build travel_planner.spec
```

---

## 4. 결과물 확인

실행이 완료되면 `results/` 폴더 내에 2개의 파일이 생성됩니다.

1. **`YYYY-MM-DD_raw_data.json`**: 1차 추천 결과, 맛집 리스트, 파이프라인 중간에 발생한 에러 기록 등을 포함하는 원본 JSON 파일입니다.
2. **`YYYY-MM-DD_travel_plan.md`**: 최종 여행 리포트 문서입니다. Markdown 뷰어로 확인하시면 됩니다.

> **결과 캐싱 (보너스 구현)**
> 한 번 실행한 날짜에 대해 다시 실행하면, 캐시된 `_raw_data.json` 파일을 읽어와 API 호출 비용을 절약합니다. 데이터 갱신을 원하시면 `results` 폴더 안의 JSON 파일을 삭제 후 실행하세요.

---

## 5. 구조 (코드)

- `travel_planner.py`: CLI 진입점. argparse 처리 및 3단계 파이프라인 흐름을 제어합니다.
- `api_llm.py`: Gemini API 통신 모듈입니다. JSON 출력 제어 및 파싱 실패 시 재시도 로직이 포함되어 있습니다.
- `api_map.py`: Kakao Local API 통신 모듈입니다. 인증 실패 및 검색 결과 0건 등의 예외 처리를 담당합니다.
- `api_tmap.py`: TMAP 도보/대중교통 모듈입니다. 키가 없거나 실패해도 리포트 생성은 계속됩니다.
- `api_tour.py`: 한국관광공사 데이터랩 3종(중심/연관/집중률) 모듈입니다. 키가 없으면 생략합니다.
- `utils.py`: 환경변수 확인, 날짜 폼 검증, 파일 저장 등의 공통 유틸리티 모음입니다.
