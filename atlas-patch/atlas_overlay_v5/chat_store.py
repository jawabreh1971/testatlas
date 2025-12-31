from __future__ import annotations
import json, os
from typing import Any, Dict, List
from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from .common import connect, now_iso

def _init_db() -> None:
    con = connect()
    try:
        con.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
          id TEXT PRIMARY KEY,
          role TEXT NOT NULL,
          content TEXT NOT NULL,
          meta_json TEXT NOT NULL,
          created_at TEXT NOT NULL
        )
        """)
        con.commit()
    finally:
        con.close()

def _mvp_reply(user_text: str) -> Dict[str, str]:
    return {"role":"assistant","content":"OK. Stored. Use Engines/Foundry/Web Hub to produce outputs."}

def install_chat_store(app: FastAPI) -> None:
    _init_db()
    r = APIRouter(prefix="/api/chat", tags=["chat"])

    @r.post("")
    async def chat_post(payload: Dict[str, Any]):
        msgs = payload.get("messages") or []
        if not isinstance(msgs, list):
            return JSONResponse({"ok": False, "error": "messages must be list"}, status_code=422)

        con = connect()
        try:
            last_user = ""
            for m in msgs[-20:]:
                role = str(m.get("role") or "user")
                content = str(m.get("content") or "")
                if not content:
                    continue
                if role in ("user","owner"):
                    last_user = content
                mid = __import__("uuid").uuid4().hex
                con.execute(
                    "INSERT INTO chat_history (id, role, content, meta_json, created_at) VALUES (?,?,?,?,?)",
                    (mid, role, content, json.dumps({}), now_iso())
                )

            # Optional external LLM (safe-off by default)
            # If EXTAPI_KEY is present, we keep it minimal and resilient.
            reply = _mvp_reply(last_user)
            ext_key = os.environ.get("EXTAPI_KEY","").strip()
            ext_model = os.environ.get("EXTERNAL_LLM_MODEL","gpt-4o-mini").strip() or "gpt-4o-mini"
            if ext_key:
                try:
                    import requests
                    # OpenAI-compatible endpoint can be set later; keep default.
                    base = os.environ.get("EXTERNAL_LLM_BASE_URL","https://api.openai.com").strip() or "https://api.openai.com"
                    url = base.rstrip("/") + "/v1/chat/completions"
                    body = {"model": ext_model, "messages": [{"role":"user","content": last_user}], "temperature": float(payload.get("temperature", 0.2))}
                    rr = requests.post(url, headers={"Authorization": f"Bearer {ext_key}", "Content-Type":"application/json"}, json=body, timeout=30)
                    if rr.status_code == 200:
                        data = rr.json()
                        txt = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
                        if txt.strip():
                            reply = {"role":"assistant","content": txt.strip()[:8000]}
                except Exception:
                    pass

            rid = __import__("uuid").uuid4().hex
            con.execute(
                "INSERT INTO chat_history (id, role, content, meta_json, created_at) VALUES (?,?,?,?,?)",
                (rid, "assistant", reply["content"], json.dumps({"mvp": not bool(ext_key)}), now_iso())
            )
            con.commit()
        finally:
            con.close()

        return {"ok": True, "reply": reply}

    @r.get("/history")
    def history(limit: int = 50):
        limit = max(1, min(int(limit), 200))
        con = connect()
        try:
            rows = con.execute("SELECT role, content, meta_json, created_at FROM chat_history ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            items = []
            for x in rows:
                d = dict(x)
                try:
                    d["meta"] = json.loads(d.get("meta_json") or "{}")
                except Exception:
                    d["meta"] = {}
                d.pop("meta_json", None)
                items.append(d)
        finally:
            con.close()
        return {"ok": True, "items": list(reversed(items))}

    app.include_router(r)
