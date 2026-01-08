from __future__ import annotations

from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse
import json, time, zipfile, hashlib, os, uuid

# Persistent exports (Render disk or docker volume)
EXPORT_DIR = Path(os.getenv("ATLAS_EXPORT_DIR", "/data/exports"))
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def spec_schema() -> dict:
    return {
        "schema_version": "1.0",
        "platform": {"brand":"Atlas","name":"Atlas – <Product>","slug":"atlas_product","domain":"<domain>"},
        "modules": ["projects","chat","files","ocr","rbac"],
        "plugins": {"enabled": True, "runtime": "atlas_plugin_runtime_v1"},
        "deploy": {"profile": "onprem_dockercompose", "db":"sqlite_volume", "storage":"volume", "ports":{"web":5173,"api":8000}},
        "providers": {"ocr":"external_provider","llm":"external_provider","storage":"local_volume"}
    }

def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def list_exports() -> list[dict]:
    items = []
    for p in sorted(EXPORT_DIR.glob("*.zip"), key=lambda x: x.stat().st_mtime, reverse=True):
        items.append({
            "artifact": p.name,
            "bytes": p.stat().st_size,
            "sha256": _sha256_file(p),
            "mtime": int(p.stat().st_mtime),
        })
    return items

# --- Presets (v4) ---
PRESETS = [
    {"preset_id":"atlas_pmx_onprem_v1","name":"Atlas PMX — Project Management eXported Platform","domain":"project_management","deploy_profile":"onprem_dockercompose"},
    {"preset_id":"atlas_dms_onprem_v1","name":"Atlas DMS — Document Control eXported Platform","domain":"document_control","deploy_profile":"onprem_dockercompose"},
    {"preset_id":"atlas_qaqc_onprem_v1","name":"Atlas QCX — QA/QC eXported Platform","domain":"qa_qc","deploy_profile":"onprem_dockercompose"},
    {"preset_id":"atlas_hse_onprem_v1","name":"Atlas HSEX — HSE eXported Platform","domain":"hse","deploy_profile":"onprem_dockercompose"},
    {"preset_id":"atlas_media_onprem_v1","name":"Atlas MEX — Media Analyzer eXported Platform","domain":"media_analysis","deploy_profile":"onprem_dockercompose"},
]

def list_presets() -> list[dict]:
    return PRESETS

def _build_pmx_package(tmpdir: Path) -> Path:
    # Minimal real client package (same spirit as atlas_pmx_onprem_v1.zip delivered)
    pkg = tmpdir / "atlas_pmx_onprem_v1"
    pkg.mkdir(parents=True, exist_ok=True)

    def w(rel: str, content: str):
        p = pkg / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    # Backend
    w("backend/app/__init__.py", "")
    w("backend/app/main.py",
      "from fastapi import FastAPI, UploadFile, File\n"
      "from pydantic import BaseModel\n"
      "from typing import Optional, List, Dict, Any\n"
      "import os, sqlite3, uuid, time\n\n"
      "APP_NAME=os.getenv('ATLAS_PRODUCT_NAME','Atlas PMX')\n"
      "DB_PATH=os.getenv('ATLAS_DB_PATH','/data/app.db')\n"
      "UPLOAD_DIR=os.getenv('ATLAS_UPLOAD_DIR','/data/uploads')\n"
      "os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)\n"
      "os.makedirs(UPLOAD_DIR, exist_ok=True)\n\n"
      "def db():\n"
      "  con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row; return con\n\n"
      "def init_db():\n"
      "  con=db(); cur=con.cursor()\n"
      "  cur.execute('CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,name TEXT,description TEXT,created_at INTEGER)')\n"
      "  cur.execute('CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,project_id TEXT,title TEXT,status TEXT,due_date TEXT,created_at INTEGER)')\n"
      "  cur.execute('CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY,project_id TEXT,filename TEXT,mime TEXT,size INTEGER,created_at INTEGER)')\n"
      "  con.commit(); con.close()\n\n"
      "init_db()\n"
      "app=FastAPI(title=APP_NAME, version='1.0.0')\n\n"
      "@app.get('/healthz')\n"
      "def healthz(): return {'ok':True,'product':APP_NAME}\n\n"
      "class ProjectIn(BaseModel):\n"
      "  name: str\n"
      "  description: Optional[str] = ''\n\n"
      "@app.get('/api/projects')\n"
      "def list_projects():\n"
      "  con=db(); rows=con.execute('SELECT * FROM projects ORDER BY created_at DESC').fetchall(); con.close()\n"
      "  return {'items':[dict(r) for r in rows]}\n\n"
      "@app.post('/api/projects')\n"
      "def create_project(p: ProjectIn):\n"
      "  pid=str(uuid.uuid4()); con=db(); con.execute('INSERT INTO projects VALUES(?,?,?,?)',(pid,p.name,p.description or '',int(time.time()))); con.commit(); con.close();\n"
      "  return {'id':pid}\n\n"
      "@app.post('/api/files/upload')\n"
      "async def upload(project_id: str, file: UploadFile = File(...)):\n"
      "  data=await file.read(); fid=str(uuid.uuid4());\n"
      "  with open(os.path.join(UPLOAD_DIR,f'{fid}_{file.filename}'),'wb') as f: f.write(data)\n"
      "  con=db(); con.execute('INSERT INTO files VALUES(?,?,?,?,?,?)',(fid,project_id,file.filename,file.content_type or '',len(data),int(time.time()))); con.commit(); con.close();\n"
      "  return {'id':fid,'filename':file.filename}\n"
    )
    w("backend/requirements.txt", "fastapi==0.115.0\nuvicorn==0.30.6\npython-multipart==0.0.9\npydantic==2.8.2\n")
    w("backend/Dockerfile",
      "FROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt /app/requirements.txt\n"
      "RUN pip install --no-cache-dir -r requirements.txt\nCOPY app /app/app\nEXPOSE 8000\n"
      "CMD ['uvicorn','app.main:app','--host','0.0.0.0','--port','8000']\n"
    )

    # Frontend (minimal placeholder)
    w("frontend/README.md", "Atlas PMX UI (Windows-style) - scaffold.\n")
    w("frontend/Dockerfile",
      "FROM nginx:alpine\nCOPY . /usr/share/nginx/html\nEXPOSE 80\n"
    )

    # Ops
    w("ops/docker-compose.yml",
      "services:\n"
      "  api:\n"
      "    build: { context: ./backend, dockerfile: Dockerfile }\n"
      "    environment:\n"
      "      - ATLAS_PRODUCT_NAME=Atlas PMX\n"
      "      - ATLAS_DB_PATH=/data/app.db\n"
      "      - ATLAS_UPLOAD_DIR=/data/uploads\n"
      "    volumes: [ 'atlas_pmx_data:/data' ]\n"
      "    ports: [ '8000:8000' ]\n"
      "  web:\n"
      "    build: { context: ./frontend, dockerfile: Dockerfile }\n"
      "    ports: [ '5173:80' ]\n"
      "volumes: { atlas_pmx_data: {} }\n"
    )
    w(".env.example", "JWT_SECRET=change_me_strong\n")
    w("README_DEPLOY.md", "Run: docker compose -f ops/docker-compose.yml up -d --build\n")
    w("plugins/README.md", "Drop plugins here.\n")

    # Zip
    zip_path = tmpdir / "atlas_pmx_onprem_v1.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in pkg.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(pkg))
    return zip_path

def export_from_payload(payload: dict) -> dict:
    preset_id = payload.get("preset_id")
    spec = payload.get("spec")

    if preset_id and not spec:
        if preset_id != "atlas_pmx_onprem_v1":
            # v4: ship PMX first; others are reserved for v5 templates
            raise HTTPException(400, "v4 supports preset atlas_pmx_onprem_v1 only (others reserved for v5 templates).")
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            built_zip = _build_pmx_package(tmp)
            artifact = built_zip.name
            target = EXPORT_DIR / artifact
            target.write_bytes(built_zip.read_bytes())
            return {"status":"ok","artifact":artifact,"download_url":f"/api/factory/download/{artifact}","sha256":_sha256_file(target),"mode":"preset"}

    if spec and not preset_id:
        # v4: allow custom spec but map to PMX builder for now
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            built_zip = _build_pmx_package(tmp)
            artifact = f"{spec.get('platform',{}).get('slug','atlas_product')}_onprem_v1.zip"
            target = EXPORT_DIR / artifact
            target.write_bytes(built_zip.read_bytes())
            return {"status":"ok","artifact":artifact,"download_url":f"/api/factory/download/{artifact}","sha256":_sha256_file(target),"mode":"spec-mapped"}

    raise HTTPException(400, "Provide either {preset_id} OR {spec}.")

def download_export(artifact: str):
    p = EXPORT_DIR / artifact
    if not p.exists():
        raise HTTPException(404, "artifact not found")
    return FileResponse(str(p), filename=p.name, media_type="application/zip")
