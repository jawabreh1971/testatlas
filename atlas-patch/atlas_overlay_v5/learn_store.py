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
        CREATE TABLE IF NOT EXISTS learn_items (
          id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          source TEXT NOT NULL,
          url TEXT NOT NULL,
          tags TEXT NOT NULL,
          content TEXT NOT NULL,
          created_at TEXT NOT NULL
        )
        """)
        con.commit()
    finally:
        con.close()

def install_learn_store(app: FastAPI) -> None:
    _init_db()
    r = APIRouter(prefix="/api/learn", tags=["learn"])

    @r.get("/items")
    def list_items(q: str = "", limit: int = 50):
        limit = max(1, min(int(limit), 200))
        con = connect()
        try:
            if q.strip():
                like = f"%{q.strip()}%"
                rows = con.execute(
                    "SELECT id,title,source,url,tags,created_at FROM learn_items WHERE title LIKE ? OR tags LIKE ? ORDER BY created_at DESC LIMIT ?",
                    (like, like, limit)
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT id,title,source,url,tags,created_at FROM learn_items ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return {"ok": True, "items": [dict(x) for x in rows]}
        finally:
            con.close()

    @r.get("/items/{item_id}")
    def get_item(item_id: str):
        con = connect()
        try:
            row = con.execute("SELECT * FROM learn_items WHERE id=? LIMIT 1", (item_id,)).fetchone()
            if not row:
                return JSONResponse({"ok": False, "error":"NOT_FOUND"}, status_code=404)
            return {"ok": True, "item": dict(row)}
        finally:
            con.close()

    @r.post("/items")
    async def add_item(request: Request, payload: Dict[str, Any]):
        try:
            require_admin(dict(request.headers))
        except PermissionError as e:
            raise HTTPException(status_code=401, detail=str(e))
        title = str(payload.get("title") or "").strip()[:300]
        source = str(payload.get("source") or "manual").strip()[:80]
        url = str(payload.get("url") or "").strip()[:1000]
        tags = str(payload.get("tags") or "").strip()[:300]
        content = str(payload.get("content") or "").strip()
        if not title or not content:
            return JSONResponse({"ok": False, "error":"title_and_content_required"}, status_code=422)
        item_id = __import__("uuid").uuid4().hex
        con = connect()
        try:
            con.execute(
                "INSERT INTO learn_items (id,title,source,url,tags,content,created_at) VALUES (?,?,?,?,?,?,?)",
                (item_id, title, source, url, tags, content, now_iso())
            )
            con.commit()
        finally:
            con.close()
        return {"ok": True, "id": item_id}

    app.include_router(r)
