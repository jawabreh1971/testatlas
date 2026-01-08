
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Any, Dict
import os, tempfile

from .settings_store import load_settings, save_settings
from .openai_client import stream_chat, vision as vision_call, stt as stt_call
from .web_bridge import safe_fetch

router = APIRouter(prefix="/api/uui", tags=["uui"])

@router.get("/health")
def health():
    return {"ok": True, "uui": "alive"}

@router.get("/settings/get")
def settings_get():
    return load_settings()

@router.post("/settings/set")
def settings_set(payload: Dict[str, Any]):
    cur = load_settings()
    cur.update(payload or {})
    save_settings(cur)
    return {"ok": True}

@router.post("/chat/stream")
def chat_stream(payload: Dict[str, Any]):
    settings = load_settings()
    messages = payload.get("messages") or []
    def gen():
        try:
            for chunk in stream_chat(settings, messages):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")

@router.post("/vision")
def vision(payload: Dict[str, Any]):
    settings = load_settings()
    img = payload.get("image_base64") or ""
    if not img:
        return {"ok": False, "error": "missing_image"}
    try:
        res = vision_call(settings, img)
        return {"ok": True, "response": res}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.post("/audio/stt")
async def audio_stt(file: UploadFile = File(...)):
    settings = load_settings()
    suffix = os.path.splitext(file.filename or "audio.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        res = stt_call(settings, tmp_path)
        return {"ok": True, "response": res}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        try: os.remove(tmp_path)
        except Exception: pass

import requests

def _proxy(settings: Dict[str, Any], base_path_key: str, path: str, payload: Dict[str, Any]):
    base_path = settings.get(base_path_key) or ""
    internal = os.getenv("ATLAS_INTERNAL_BASE_URL", "http://127.0.0.1:8000")
    url = internal.rstrip("/") + "/" + base_path.strip("/")
    url = url.rstrip("/") + "/" + path.strip("/")
    r = requests.post(url, json=payload, timeout=120)
    try:
        body = r.json()
    except Exception:
        body = r.text
    return {"ok": True, "status": r.status_code, "data": body}

@router.post("/v4/plan")
def v4_plan(payload: Dict[str, Any]):
    settings = load_settings()
    return _proxy(settings, "v4BasePath", "jobs/plan", payload)

@router.post("/v4/run")
def v4_run(payload: Dict[str, Any]):
    settings = load_settings()
    return _proxy(settings, "v4BasePath", "jobs/run", payload)

@router.post("/v4_1/plan")
def v41_plan(payload: Dict[str, Any]):
    settings = load_settings()
    return _proxy(settings, "v41BasePath", "jobs/plan", payload)

@router.post("/v4_1/run")
def v41_run(payload: Dict[str, Any]):
    settings = load_settings()
    return _proxy(settings, "v41BasePath", "jobs/run", payload)

@router.post("/web/fetch")
def web_fetch(payload: Dict[str, Any]):
    url = (payload or {}).get("url") or ""
    return safe_fetch(url)

@router.post("/logs/tail")
def logs_tail(payload: Dict[str, Any]):
    settings = load_settings()
    lines = int((payload or {}).get("lines") or 200)
    log_path = settings.get("logsPath") or os.getenv("UUI_LOG_PATH", "")
    if not log_path:
        return {"ok": False, "error": "logsPath_not_set"}
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.readlines()[-lines:]
        return {"ok": True, "lines": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}
