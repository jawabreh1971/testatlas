import os, json
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from ..core.security import require_admin
from ..core.audit import audit
from ..factory_engine.engine import generate_plugin

router = APIRouter(prefix="/api/admin/factory", tags=["admin-factory"])

GENERATED_DIR = os.path.join(os.path.dirname(__file__), "..", "plugins_generated")

class SpecIn(BaseModel):
    spec: dict

@router.get("/status")
def status():
    return {"ok": True, "enabled": bool(os.getenv("ATLAS_ADMIN_TOKEN","").strip())}

@router.post("/generate-plugin")
def gen(payload: SpecIn):
    require_admin()
    Path(GENERATED_DIR).mkdir(parents=True, exist_ok=True)
    audit("factory.generate_plugin.request", {"keys": list(payload.spec.keys())})
    out = generate_plugin(GENERATED_DIR, payload.spec)
    audit("factory.generate_plugin.done", {"path": out.get("path")})
    return out

@router.get("/list")
def list_generated():
    require_admin()
    Path(GENERATED_DIR).mkdir(parents=True, exist_ok=True)
    items = []
    for p in sorted(Path(GENERATED_DIR).glob("*")):
        if p.is_dir() and (p/"manifest.json").exists():
            try:
                manifest = json.loads((p/"manifest.json").read_text(encoding="utf-8"))
            except Exception:
                manifest = {"slug": p.name, "title": p.name}
            items.append({"dir": p.name, "manifest": manifest})
    return {"ok": True, "items": items}
