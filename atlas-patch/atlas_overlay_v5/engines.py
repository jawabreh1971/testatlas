from __future__ import annotations

import os, io, csv, json, uuid
from typing import Any, Dict, List, Tuple

from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse, Response, FileResponse

from .common import connect, ensure_dir, now_iso, sha256_bytes

ARTIFACTS_DIR = os.environ.get("ATLAS_ENGINE_ARTIFACTS_DIR", "engine_artifacts")

SPEC_SCHEMA: Dict[str, Any] = {
  "type": "object",
  "required": ["name", "kind", "modules"],
  "properties": {
    "name": {"type": "string", "minLength": 2},
    "kind": {"type": "string", "enum": ["plugin", "service", "app", "bundle"]},
    "modules": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["id", "type"],
        "properties": {
          "id": {"type": "string"},
          "type": {"type": "string", "enum": ["fastapi_router", "worker", "react_page", "db_migration"]},
          "config": {"type": "object"}
        }
      }
    },
    "meta": {"type": "object"},
  }
}

def _init_db() -> None:
    ensure_dir(ARTIFACTS_DIR)
    con = connect()
    try:
        con.execute("""
        CREATE TABLE IF NOT EXISTS engine_artifacts (
          id TEXT PRIMARY KEY,
          kind TEXT NOT NULL,
          filename TEXT NOT NULL,
          bytes INTEGER NOT NULL,
          sha256 TEXT NOT NULL,
          created_at TEXT NOT NULL,
          meta_json TEXT NOT NULL
        )
        """)
        con.commit()
    finally:
        con.close()

def _validate_spec(spec: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errs: List[str] = []
    if not isinstance(spec, dict):
        return False, ["spec must be an object"]
    name = spec.get("name")
    if not isinstance(name, str) or len(name.strip()) < 2:
        errs.append("name must be a string (min length 2)")
    kind = spec.get("kind")
    if kind not in {"plugin", "service", "app", "bundle"}:
        errs.append("kind must be one of: plugin|service|app|bundle")
    modules = spec.get("modules")
    if not isinstance(modules, list) or len(modules) < 1:
        errs.append("modules must be a non-empty array")
    else:
        for i, m in enumerate(modules):
            if not isinstance(m, dict):
                errs.append(f"modules[{i}] must be an object")
                continue
            mid = m.get("id")
            mtype = m.get("type")
            if not isinstance(mid, str) or not mid.strip():
                errs.append(f"modules[{i}].id required")
            if mtype not in {"fastapi_router", "worker", "react_page", "db_migration"}:
                errs.append(f"modules[{i}].type invalid")
    return (len(errs) == 0, errs)

def _readiness(spec: Dict[str, Any]) -> Dict[str, Any]:
    ok, errs = _validate_spec(spec)
    score = 0
    checks = []
    checks.append({"id": "spec_valid", "ok": ok, "weight": 40, "notes": "; ".join(errs) if errs else ""})
    if ok:
        score += 40
    mods = spec.get("modules", []) if isinstance(spec.get("modules"), list) else []
    has_api = any(isinstance(m, dict) and m.get("type") == "fastapi_router" for m in mods)
    has_ui = any(isinstance(m, dict) and m.get("type") == "react_page" for m in mods)
    has_db = any(isinstance(m, dict) and m.get("type") == "db_migration" for m in mods)
    has_worker = any(isinstance(m, dict) and m.get("type") == "worker" for m in mods)
    checks += [
        {"id": "has_api", "ok": has_api, "weight": 15, "notes": ""},
        {"id": "has_ui", "ok": has_ui, "weight": 15, "notes": ""},
        {"id": "has_db", "ok": has_db, "weight": 10, "notes": ""},
        {"id": "has_worker", "ok": has_worker, "weight": 10, "notes": ""},
    ]
    score += (15 if has_api else 0) + (15 if has_ui else 0) + (10 if has_db else 0) + (10 if has_worker else 0)
    has_meta = isinstance(spec.get("meta"), dict) and bool(spec.get("meta"))
    checks.append({"id": "meta_present", "ok": has_meta, "weight": 10, "notes": ""})
    score += 10 if has_meta else 0
    status = "PASS" if score >= 75 else ("WARN" if score >= 55 else "FAIL")
    return {"ok": True, "score": score, "status": status, "checks": checks}

def _md_report(spec: Dict[str, Any], readiness: Dict[str, Any]) -> str:
    name = str(spec.get("name", "Untitled"))
    kind = str(spec.get("kind", "n/a"))
    score = readiness.get("score", 0)
    status = readiness.get("status", "n/a")
    lines = []
    lines.append(f"# Readiness Report: {name}")
    lines.append("")
    lines.append(f"- Kind: **{kind}**")
    lines.append(f"- Status: **{status}**")
    lines.append(f"- Score: **{score}/100**")
    lines.append("")
    lines.append("## Checks")
    for c in readiness.get("checks", []):
        ok = "PASS" if c.get("ok") else "FAIL"
        notes = c.get("notes") or ""
        lines.append(f"- `{c.get('id')}`: **{ok}** (w={c.get('weight')}) {('- ' + notes) if notes else ''}")
    lines.append("")
    lines.append("## Recommendations")
    if readiness.get("status") == "FAIL":
        lines.append("- Fix schema validity and ensure at least one API module and UI module.")
    elif readiness.get("status") == "WARN":
        lines.append("- Add missing modules (UI/DB/Worker) and enrich meta.")
    else:
        lines.append("- Baseline looks good. Next: tests, observability, versioning policy.")
    return "\n".join(lines)

def _store_artifact(kind: str, filename: str, content: bytes, meta: Dict[str, Any]) -> Dict[str, Any]:
    ensure_dir(ARTIFACTS_DIR)
    aid = uuid.uuid4().hex
    sha = sha256_bytes(content)
    path = os.path.join(ARTIFACTS_DIR, f"{aid}__{filename}")
    with open(path, "wb") as f:
        f.write(content)
    con = connect()
    try:
        con.execute(
            "INSERT INTO engine_artifacts (id, kind, filename, bytes, sha256, created_at, meta_json) VALUES (?,?,?,?,?,?,?)",
            (aid, kind, path, len(content), sha, now_iso(), json.dumps(meta))
        )
        con.commit()
    finally:
        con.close()
    return {"id": aid, "kind": kind, "path": path, "bytes": len(content), "sha256": sha}

def install_engines(app: FastAPI) -> None:
    _init_db()
    r = APIRouter(prefix="/api/engines", tags=["engines"])

    @r.post("/readiness/report")
    async def readiness_report(payload: Dict[str, Any]):
        spec = payload.get("spec") or {}
        readiness = _readiness(spec)
        md = _md_report(spec, readiness)
        artifact = _store_artifact("readiness_md", "readiness.md", md.encode("utf-8"), {"name": spec.get("name"), "status": readiness.get("status")})
        return {"ok": True, "readiness": readiness, "markdown": md, "artifact": artifact}

    @r.post("/compare/csv")
    async def compare_csv(payload: Dict[str, Any]):
        a = payload.get("a") or {}
        b = payload.get("b") or {}
        ra = _readiness(a)
        rb = _readiness(b)
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["item", "a", "b", "delta"])
        w.writerow(["score", ra.get("score", 0), rb.get("score", 0), ra.get("score", 0) - rb.get("score", 0)])
        w.writerow(["status", ra.get("status", ""), rb.get("status", ""), ""])
        content = out.getvalue().encode("utf-8")
        artifact = _store_artifact("compare_csv", "compare.csv", content, {"a_name": a.get("name"), "b_name": b.get("name")})
        return Response(content=content, media_type="text/csv", headers={"X-Atlas-Artifact-Id": artifact["id"]})

    @r.get("/artifacts")
    def list_artifacts():
        con = connect()
        try:
            rows = con.execute("SELECT id, kind, filename, bytes, sha256, created_at, meta_json FROM engine_artifacts ORDER BY created_at DESC LIMIT 500").fetchall()
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
        return {"ok": True, "items": items}

    @r.get("/artifacts/{artifact_id}")
    def download_artifact(artifact_id: str):
        con = connect()
        try:
            row = con.execute("SELECT * FROM engine_artifacts WHERE id=? LIMIT 1", (artifact_id,)).fetchone()
            if not row:
                return JSONResponse({"ok": False, "error": "NOT_FOUND"}, status_code=404)
            path = row["filename"]
        finally:
            con.close()
        if not os.path.exists(path):
            return JSONResponse({"ok": False, "error": "FILE_MISSING"}, status_code=410)
        return FileResponse(path, filename=os.path.basename(path))

    @r.get("/spec/schema")
    def schema():
        return {"ok": True, "schema": SPEC_SCHEMA}

    app.include_router(r)
