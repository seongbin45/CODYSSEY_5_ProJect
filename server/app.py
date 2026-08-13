"""
FastAPI 웹 서버.

제공자 키는 호스팅 환경변수에만 둔다. 브라우저/응답으로 키를 내려주지 않는다.
Jinja TemplateResponse 는 Starlette 버전마다 인자 순서가 달라서 쓰지 않는다.
"""

import html
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from pipeline import PipelineError, list_usable_models, run_pipeline
from utils import check_api_keys, results_dir

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INDEX_HTML = (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")

app = FastAPI(title="국내 여행지 추천", docs_url=None, redoc_url=None)


def _render_index(models, default_model="gemini-2.5-flash"):
    choices = models or [default_model]
    options = []
    for item in choices:
        selected = " selected" if item == default_model else ""
        options.append(
            f'<option value="{html.escape(item)}"{selected}>{html.escape(item)}</option>'
        )
    page = INDEX_HTML
    # 서버에서 모델 목록만 채워 넣고, 나머지 화면은 정적 HTML이다.
    start = page.find('<select name="model">')
    end = page.find("</select>", start)
    if start == -1 or end == -1:
        return page
    select = '<select name="model">\n' + "\n".join(options) + "\n        </select>"
    return page[:start] + select + page[end + len("</select>"):]


@app.get("/health")
def health():
    keys = check_api_keys(require_kakao=False)
    kakao = (keys[1] if keys else "") or ""
    return {
        "ok": True,
        "gemini": bool(keys and keys[0]),
        "kakao": bool(kakao),
        "kakao_key_len": len(kakao),
    }


@app.get("/api/models")
def api_models():
    keys = check_api_keys(require_kakao=False)
    if not keys:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY 가 서버에 없습니다.")
    try:
        return {"models": list_usable_models(keys[0])}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/plan")
def api_plan(date: str = Form(...), model: str = Form(""), use_cache: bool = Form(True)):
    try:
        result = run_pipeline(date, model_name=model or None, use_cache=use_cache)
    except PipelineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    date = result["date"]
    return {
        "date": date,
        "model": result["model"],
        "logs": result["logs"],
        "errors": result["errors"],
        "report_md": result["report_md"],
        "recommendation": result["recommendation"],
        "restaurants": result["restaurants"],
        "report_url": f"/results/{date}_travel_plan.md",
        "raw_url": f"/results/{date}_raw_data.json",
        "results_url": "/results",
    }


def _safe_result_file(name):
    if not name or "/" in name or "\\" in name or name.startswith("."):
        raise HTTPException(status_code=400, detail="잘못된 파일 이름입니다.")
    if not (name.endswith(".md") or name.endswith(".json")):
        raise HTTPException(status_code=400, detail="md 또는 json만 열 수 있습니다.")
    path = Path(results_dir()) / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="파일이 없습니다.")
    return path


@app.get("/results", response_class=HTMLResponse)
def results_index():
    folder = Path(results_dir())
    files = sorted(
        [item.name for item in folder.iterdir() if item.suffix in {".md", ".json"}],
        reverse=True,
    )
    rows = []
    for name in files:
        rows.append(
            f'<li><a href="/results/{html.escape(name)}">{html.escape(name)}</a></li>'
        )
    body = "\n".join(rows) if rows else "<li class='muted'>아직 저장된 파일이 없습니다.</li>"
    return HTMLResponse(
        f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><title>저장된 리포트</title>
<style>
body {{ font-family: sans-serif; background:#0f1419; color:#e7ecf1; margin:0; }}
main {{ max-width:880px; margin:0 auto; padding:32px 20px; }}
a.btn {{ display:inline-flex; padding:10px 14px; border-radius:8px; background:#3b82f6; color:#fff; font-weight:600; text-decoration:none; }}
ul {{ line-height:2; padding-left:0; list-style:none; }}
ul a {{ color:#bfdbfe; font-size:1.05rem; }}
.muted {{ color:#cbd5e1; }}
</style></head>
<body><main>
  <p><a class="btn" href="/">추천 페이지로 돌아가기</a></p>
  <h1>저장된 리포트</h1>
  <p class="muted">서버 results 폴더의 Markdown / JSON 입니다.</p>
  <ul>{body}</ul>
</main></body></html>"""
    )


@app.get("/results/{name}")
def results_file(name: str):
    path = _safe_result_file(name)
    media = "text/markdown" if path.suffix == ".md" else "application/json"
    return FileResponse(path, media_type=media, filename=path.name)


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def home():
    models = []
    keys = check_api_keys(require_kakao=False)
    if keys:
        try:
            models = list_usable_models(keys[0])
        except Exception:
            models = []
    return HTMLResponse(_render_index(models))
