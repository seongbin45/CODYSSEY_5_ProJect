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
from fastapi.responses import HTMLResponse

from pipeline import PipelineError, list_usable_models, run_pipeline
from utils import check_api_keys

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
    return {
        "date": result["date"],
        "model": result["model"],
        "logs": result["logs"],
        "errors": result["errors"],
        "report_md": result["report_md"],
        "recommendation": result["recommendation"],
        "restaurants": result["restaurants"],
    }


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
