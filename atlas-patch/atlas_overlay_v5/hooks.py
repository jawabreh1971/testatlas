from __future__ import annotations
import json
from typing import Any, Dict
from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from .common import connect, now_iso, require_admin

def _init_db() -> None:
    con = connect()
    try:
        con.execute("""
        CREATE TABLE IF NOT EXISTS hooks_registry (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          url TEXT NOT NULL,
          event TEXT NOT NULL,
          secret TEXT NOT NULL,
          enabled INTEGER NOT NULL,
          updated_at TEXT NOT NULL
        )
        """)
        con.commit()
    finally:
        con.close()

def install_hooks(app: FastAPI) -> None:
    _init_db()
    r = APIRouter(prefix="/api/hooks", tags=["hooks"])

    @r.get("")
    def list_hooks(limit: int = 100):
        limit = max(1, min(int(limit), 200))
        con = connect()
        try:
            rows = con.execute("SELECT id,name,url,event,enabled,updated_at FROM hooks_registry ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
            return {"ok": True, "items": [dict(x) for x in rows]}
        finally:
            con.close()

    @r.post("")
    async def upsert(request: Request, payload: Dict[str, Any]):
        try:
            require_admin(dict(request.headers))
        except PermissionError as e:
            raise HTTPException(status_code=401, detail=str(e))
        hid = str(payload.get("id") or "").strip() or __import__("uuid").uuid4().hex
        name = str(payload.get("name") or "hook").strip()[:80]
        url = str(payload.get("url") or "").strip()[:1000]
        event = str(payload.get("event") or "any").strip()[:80]
        secret = str(payload.get("secret") or "").strip()[:200]
        enabled = 1 if bool(payload.get("enabled", True)) else 0
        if not url.startswith(("http://","https://")):
            return JSONResponse({"ok": False, "error":"invalid_url"}, status_code=422)
        con = connect()
        try:
            con.execute(
              "INSERT OR REPLACE INTO hooks_registry (id,name,url,event,secret,enabled,updated_at) VALUES (?,?,?,?,?,?,?)",
              (hid, name, url, event, secret, enabled, now_iso())
            )
            con.commit()
        finally:
            con.close()
        return {"ok": True, "id": hid}

    app.include_router(r)
