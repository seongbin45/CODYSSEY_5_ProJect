# `server/templates/` — `GET /`이 보내는 HTML

이 폴더에는 `index.html` 한 파일이 있습니다.  
`server/app.py`의 `_render_index()`가 이 파일을 읽고, `<select name="model">` … `</select>` 사이만 모델 `<option>`으로 바꾼 뒤 `HTMLResponse`로 보냅니다.

---

## 1. 파일이 하나인 이유

처음에는 Jinja (`{% for %}`)와 `TemplateResponse`를 쓰려 했습니다.  
Starlette 버전에 따라 `TemplateResponse`의 `request` / `name` 인자 순서가 달라 서버가 500 (`unhashable dict`)을 냈습니다.

그래서 `index.html`은 **일반 HTML + `<script>`** 입니다. Jinja 문법이 없습니다.

`_render_index()`가 하는 일:

1. `index.html` 전체를 문자열로 읽음 (`app.py` 로드 시 한 번)
2. `'<select name="model">'` 위치와 `'</select>'` 위치를 찾음
3. 그 사이를 `list_usable_models()`가 준 이름들의 `<option>`으로 교체
4. 못 찾으면 원문 그대로 반환

날짜 입력, 버튼 클릭, 로그·리포트 표시는 모두 이 파일 안의 `fetch`가 합니다.

---

## 2. `index.html` 구역

### 위쪽 (`header-row`)

- `<h1>` : 국내 여행지 추천
- `<p class="lead">` : 설명 한 줄
- `<a class="btn btn-primary" href="/results">` : **저장된 리포트 저장소 열기**
- `<a class="btn" href="https://github.com/seongbin45/CODYSSEY_5_ProJect/tree/fastapi-web">` : **GitHub 코드 보기**

### 폼 (`#plan-form`)

- `<input type="date" name="date" required>` — 기본값 `2026-08-20`
- `<select name="model">` — 서버가 option을 채움
- `<button type="submit">리포트 생성</button>` → 아래 3절의 `POST /api/plan`

### 결과

- `<pre id="logs">` : 진행 로그
- `<div id="result-actions">` : 생성 후에만 보임 (`hidden` 제거)
  - `report_url` → 저장된 Markdown
  - `raw_url` → 원본 JSON
  - `results_url` → `/results`
- `<article id="report">` : 리포트 본문

---

## 3. **리포트 생성**을 눌렀을 때 (`<script>`)

1. `event.preventDefault()`로 일반 form GET/POST를 막음
2. `new FormData(form)`으로 `date`, `model`을 담음
3. `fetch("/api/plan", { method: "POST", body: data })`
4. 응답 JSON의 `logs`를 `#logs`에 넣음
5. `report_md`를 `#report`에 넣음
6. `report_url`, `raw_url`, `results_url`로 `#result-actions` 안의 `<a class="btn">`을 만듦

`res.ok`가 아니면 `body.detail`을 `#logs`에 `class="err"`로 넣습니다.  
서버에서 Gemini·Kakao를 부르므로 보통 20~40초입니다.

---

## 4. 버튼 색 (`<style>`)

`body` 배경은 `#0f1419`입니다. 기본 `<a>`만 쓰면 링크가 거의 안 보입니다.  
이동 링크는 반드시 `class="btn"` 또는 `class="btn btn-primary"`를 씁니다.

- `btn-primary` : 파란 배경 `#3b82f6`, 흰 글씨 (저장소 열기)
- `btn` : 흰 배경 `#f8fafc`, 글씨 `#0f172a` (GitHub, 생성 후 파일 링크)

---

## 5. `/results` 목록 HTML은 이 폴더에 없음

`GET /results` HTML은 `server/app.py`의 `results_index()`가 f-string으로 만듭니다.  
파일 목록이 실행마다 달라서 정적 HTML로 두지 않았습니다.

---

위로: [server/README.md](../README.md)  
프로젝트: [../../README.md](../../README.md)
