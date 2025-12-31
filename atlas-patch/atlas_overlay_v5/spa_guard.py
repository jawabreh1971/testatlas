from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

def install_spa_guard(app: FastAPI) -> None:
    @app.middleware("http")
    async def _spa_api_guard(request: Request, call_next):
        resp = await call_next(request)
        path = request.url.path.lstrip("/")
        if path == "api" or path.startswith("api/"):
            ctype = (resp.headers.get("content-type") or "").lower()
            if "text/html" in ctype:
                return JSONResponse({"ok": False, "error": "NOT_FOUND"}, status_code=404)
        return resp
