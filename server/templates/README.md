# `server/templates/` — 브라우저에 보이는 화면

이 폴더에는 **첫 화면 HTML 한 장**이 있습니다.  
파이썬이 이 파일을 읽어서 모델 목록만 끼워 넣은 뒤 그대로 브라우저에 보냅니다.

---

## 1. 파일이 하나인 이유

원래 Jinja 템플릿(`{% for %}`)을 쓰려 했으나, Starlette 버전에 따라 `TemplateResponse` 인자 순서가 달라 서버가 500을 냈습니다.  
그래서 `index.html`은 **일반 HTML + 브라우저 JavaScript**로 두었습니다.

서버(`app.py`의 `_render_index`)가 하는 일은 한 가지뿐입니다.

- `<select name="model"> ... </select>` 사이를, 사용 가능한 모델 `<option>`으로 바꿔 끼움

날짜 입력, 버튼, 로그, 리포트 표시는 모두 이 HTML 안의 스크립트가 합니다.

---

## 2. `index.html`을 구역으로 나누면

### 머리글

- 제목: 국내 여행지 추천
- 설명 문장
- 파란 버튼: **저장된 리포트 저장소 열기** → 같은 사이트의 `/results`
- 흰 버튼: **GitHub 코드 보기** → `fastapi-web` 브랜치

### 입력 폼

- 여행 날짜 (`<input type="date" name="date">`)
- 모델 (`<select name="model">`)
- **리포트 생성** 버튼 → `POST /api/plan`

### 결과

- 진행 로그 (`#logs`)
- 생성 후에만 보이는 버튼들 (`#result-actions`)
  - 저장된 Markdown 열기
  - 원본 JSON 열기
  - 저장소 전체 보기
- 리포트 본문 (`#report`)

---

## 3. 버튼을 눌렀을 때 (브라우저 안)

1. 폼 전송을 가로챕니다. (`event.preventDefault()`)
2. `FormData`로 `date`, `model`을 `/api/plan`에 POST 합니다.
3. 응답 JSON의 `logs`를 로그 칸에 넣습니다.
4. `report_md`를 `<pre>`로 보여 줍니다.
5. `report_url`, `raw_url`, `results_url`로 버튼을 만듭니다.

실패하면 `detail` 메시지를 빨간 글씨로 보여 줍니다.  
생성에는 보통 20~40초가 걸립니다.

---

## 4. 색이 어두운 이유와 버튼 규칙

배경은 짙은 남색입니다. 그냥 `<a>`만 쓰면 링크가 거의 안 보입니다.  
그래서 모든 이동 버튼은 `class="btn"` 또는 `class="btn btn-primary"`를 씁니다.

- `btn-primary` : 파란 배경, 흰 글씨 (중요한 이동)
- `btn` : 흰 배경, 검은 글씨 (보조 이동)

화면을 고칠 때는 이 클래스를 유지하세요.

---

## 5. 저장소 목록 페이지는 어디에 있나

`/results` 화면 HTML은 이 폴더가 아니라 `server/app.py`의 `results_index()` 안에 문자열로 있습니다.  
파일 목록이 매번 달라서 파이썬이 그때그때 만들기 때문입니다.

---

위로: [server/README.md](../README.md)  
프로젝트: [../../README.md](../../README.md)
