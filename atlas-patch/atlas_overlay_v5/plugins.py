from __future__ import annotations

import io, os, json, zipfile, importlib.util
from typing import List

from fastapi import FastAPI, APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from .common import connect, ensure_dir, now_iso, require_admin

PLUGIN_ROOT = os.environ.get("ATLAS_PLUGIN_ROOT", "plugins_installed")

def _init_db() -> None:
    con = connect()
    try:
        con.execute("""
        CREATE TABLE IF NOT EXISTS plugins_registry (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          version TEXT NOT NULL,
          enabled INTEGER NOT NULL,
          manifest_json TEXT NOT NULL,
          installed_at TEXT NOT NULL
        )
        """)
        con.commit()
    finally:
        con.close()

def _plugin_dir(pid: str) -> str:
    ensure_dir(PLUGIN_ROOT)
    return os.path.join(PLUGIN_ROOT, pid)

def _load_router(router_py: str):
    spec = importlib.util.spec_from_file_location("plugin_router", router_py)
    if not spec or not spec.loader:
        raise RuntimeError("Cannot load plugin router module.")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    router = getattr(mod, "router", None)
    if router is None:
        raise RuntimeError("router not found in plugin backend/router.py")
    return router

def _auto_mount(app: FastAPI) -> List[str]:
    mounted: List[str] = []
    con = connect()
    try:
        rows = con.execute("SELECT id, enabled FROM plugins_registry").fetchall()
        for r in rows:
            if int(r["enabled"]) != 1:
                continue
            pid = r["id"]
            router_py = os.path.join(_plugin_dir(pid), "backend", "router.py")
            if not os.path.exists(router_py):
                continue
            try:
                app.include_router(_load_router(router_py))
                mounted.append(pid)
            except Exception:
                continue
    finally:
        con.close()
    return mounted

def install_plugins(app: FastAPI) -> None:
    _init_db()
    r = APIRouter(prefix="/api/plugins", tags=["plugins"])

    if not getattr(app.state, "_plugins_mounted_once", False):
        _auto_mount(app)
        app.state._plugins_mounted_once = True

    @r.get("")
    def list_plugins():
        con = connect()
        try:
            rows = con.execute("SELECT id, name, version, enabled, installed_at FROM plugins_registry ORDER BY installed_at DESC LIMIT 500").fetchall()
            items = [dict(x) for x in rows]
        finally:
            con.close()
        return {"ok": True, "items": items}

    @r.get("/{plugin_id}")
    def get_plugin(plugin_id: str):
        con = connect()
        try:
            row = con.execute("SELECT * FROM plugins_registry WHERE id=? LIMIT 1", (plugin_id,)).fetchone()
            if not row:
                return JSONResponse({"ok": False, "error": "NOT_FOUND"}, status_code=404)
            item = dict(row)
            item["manifest"] = json.loads(item["manifest_json"])
            item.pop("manifest_json", None)
        finally:
            con.close()
        return {"ok": True, "item": item}

    @r.post("/install")
    async def install_plugin(request: Request, file: UploadFile = File(...)):
        try:
            require_admin(dict(request.headers))
        except PermissionError as e:
            raise HTTPException(status_code=401, detail=str(e))

        blob = await file.read()
        if len(blob) > 25 * 1024 * 1024:
            return JSONResponse({"ok": False, "error": "ZIP_TOO_LARGE"}, status_code=413)

        z = zipfile.ZipFile(io.BytesIO(blob))
        names = z.namelist()

        manifest_path = None
        for n in names:
            if n.endswith("manifest.json") and n.count("/") == 1:
                manifest_path = n
                break
        if not manifest_path:
            return JSONResponse({"ok": False, "error": "manifest.json not found at <plugin_id>/manifest.json"}, status_code=422)

        pid = manifest_path.split("/")[0].strip()
        manifest = json.loads(z.read(manifest_path).decode("utf-8", errors="ignore"))
        name = str(manifest.get("name") or pid)
        version = str(manifest.get("version") or "0.1.0")

        out_dir = _plugin_dir(pid)
        ensure_dir(out_dir)

        for member in names:
            if not member.startswith(pid + "/"):
                continue
            if member.endswith("/"):
                ensure_dir(os.path.join(PLUGIN_ROOT, member))
                continue
            target = os.path.join(PLUGIN_ROOT, member)
            ensure_dir(os.path.dirname(target))
            with open(target, "wb") as f:
                f.write(z.read(member))

        router_py = os.path.join(out_dir, "backend", "router.py")
        if not os.path.exists(router_py):
            return JSONResponse({"ok": False, "error": "backend/router.py missing"}, status_code=422)

        con = connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO plugins_registry (id,name,version,enabled,manifest_json,installed_at) VALUES (?,?,?,?,?,?)",
                (pid, name, version, 1, json.dumps(manifest), now_iso())
            )
            con.commit()
        finally:
            con.close()

        try:
            app.include_router(_load_router(router_py))
        except Exception:
            pass

        return {"ok": True, "plugin_id": pid, "enabled": True}

    @r.post("/{plugin_id}/enable")
    def enable(plugin_id: str, request: Request):
        try:
            require_admin(dict(request.headers))
        except PermissionError as e:
            raise HTTPException(status_code=401, detail=str(e))

        con = connect()
        try:
            row = con.execute("SELECT id FROM plugins_registry WHERE id=? LIMIT 1", (plugin_id,)).fetchone()
            if not row:
                return JSONResponse({"ok": False, "error": "NOT_FOUND"}, status_code=404)
            con.execute("UPDATE plugins_registry SET enabled=1 WHERE id=?", (plugin_id,))
            con.commit()
        finally:
            con.close()

        router_py = os.path.join(_plugin_dir(plugin_id), "backend", "router.py")
        if os.path.exists(router_py):
            try:
                app.include_router(_load_router(router_py))
            except Exception:
                pass
        return {"ok": True, "enabled": True}

    @r.post("/{plugin_id}/disable")
    def disable(plugin_id: str, request: Request):
        try:
            require_admin(dict(request.headers))
        except PermissionError as e:
            raise HTTPException(status_code=401, detail=str(e))

        con = connect()
        try:
            row = con.execute("SELECT id FROM plugins_registry WHERE id=? LIMIT 1", (plugin_id,)).fetchone()
            if not row:
                return JSONResponse({"ok": False, "error": "NOT_FOUND"}, status_code=404)
            con.execute("UPDATE plugins_registry SET enabled=0 WHERE id=?", (plugin_id,))
            con.commit()
        finally:
            con.close()
        return {"ok": True, "enabled": False, "note": "Router remains mounted until restart; skipped on next boot."}

    @r.delete("/{plugin_id}")
    def remove(plugin_id: str, request: Request):
        try:
            require_admin(dict(request.headers))
        except PermissionError as e:
            raise HTTPException(status_code=401, detail=str(e))

        con = connect()
        try:
            con.execute("DELETE FROM plugins_registry WHERE id=?", (plugin_id,))
            con.commit()
        finally:
            con.close()

        try:
            import shutil
            shutil.rmtree(_plugin_dir(plugin_id), ignore_errors=True)
        except Exception:
            pass
        return {"ok": True, "removed": True, "note": "Restart to fully unload if router already mounted."}

    app.include_router(r)
