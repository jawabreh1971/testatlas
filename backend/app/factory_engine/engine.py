import os, json, re
from datetime import datetime, timezone
from pathlib import Path

SAFE = re.compile(r"^[a-z0-9\-_.]+$")

def _safe_slug(s: str) -> str:
    s = s.strip().lower()
    if not SAFE.match(s):
        raise ValueError("Invalid slug. Use [a-z0-9-_.] only.")
    return s

def generate_plugin(base_dir: str, spec: dict) -> dict:
    slug = _safe_slug(spec.get("plugin_slug") or spec.get("product_slug") or "generated-plugin")
    title = spec.get("title") or slug
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    root = Path(base_dir) / f"{slug}_{ts}"
    root.mkdir(parents=True, exist_ok=False)

    manifest = {
        "slug": slug,
        "title": title,
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "routes": [
            {"prefix": f"/api/plugins/{slug}", "module": "router.py", "attr": "router"}
        ]
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    router_code = f'''from fastapi import APIRouter
router = APIRouter(prefix="/api/plugins/{slug}", tags=["plugin:{slug}"])

@router.get("/ping")
def ping():
    return {{"ok": True, "plugin": "{slug}", "title": "{title}"}}
'''
    (root / "router.py").write_text(router_code, encoding="utf-8")

    return {"ok": True, "path": str(root), "manifest": manifest}
