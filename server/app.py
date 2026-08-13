"""
FastAPI 웹 서버.

제공자 키는 호스팅 환경변수에만 둔다. 브라우저/응답으로 키를 내려주지 않는다.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pipeline import PipelineError, list_usable_models, run_pipeline
from utils import check_api_keys

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="국내 여행지 추천", docs_url=None, redoc_url=None)


@app.get("/health")
def health():
    keys = check_api_keys(require_kakao=False)
    return {
        "ok": True,
        "gemini": bool(keys and keys[0]),
        "kakao": bool(os.environ.get("KAKAO_REST_API_KEY", "").strip()),
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


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    models = []
    keys = check_api_keys(require_kakao=False)
    if keys:
        try:
            models = list_usable_models(keys[0])
        except Exception:
            models = []
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "models": models,
            "default_model": "gemini-2.5-flash",
        },
    )
