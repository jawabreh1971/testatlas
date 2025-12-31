from __future__ import annotations
import base64, json
from typing import Any, Dict
from fastapi import FastAPI, APIRouter, UploadFile, File, Request, HTTPException
from fastapi.responses import JSONResponse
from .common import require_admin
from .engines import _store_artifact  # type: ignore

def install_media(app: FastAPI) -> None:
    r = APIRouter(prefix="/api/media", tags=["media"])

    @r.post("/stt")
    async def stt(payload: Dict[str, Any] | None = None, file: UploadFile | None = File(default=None)):
        # Stub: store audio as artifact; transcription is client-side (browser SpeechRecognition) or external pipeline.
        if file is not None:
            content = await file.read()
            art = _store_artifact("audio", file.filename or "audio.wav", content, {"kind":"audio"})
            return {"ok": True, "mode":"upload", "artifact": art, "text": ""}
        payload = payload or {}
        b64 = str(payload.get("audio_b64") or "")
        if not b64:
            return JSONResponse({"ok": False, "error":"audio_b64_or_file_required"}, status_code=422)
        content = base64.b64decode(b64.encode("utf-8"), validate=False)
        art = _store_artifact("audio", "audio.bin", content, {"kind":"audio_b64"})
        return {"ok": True, "mode":"b64", "artifact": art, "text": ""}

    @r.post("/video/analyze")
    def video_analyze(payload: Dict[str, Any]):
        # Stub: stores request as artifact and returns minimal metadata.
        url = str(payload.get("url") or "").strip()
        if not url.startswith(("http://","https://")):
            return JSONResponse({"ok": False, "error":"invalid_url"}, status_code=422)
        meta = {"url": url, "note":"Video analyze is stub in v5. Next step: provider plugins (yt-dlp/ffprobe) in controlled env."}
        art = _store_artifact("video_request", "video_request.json", json.dumps(meta, indent=2).encode("utf-8"), {"kind":"video_request"})
        return {"ok": True, "meta": meta, "artifact": art}

    app.include_router(r)
