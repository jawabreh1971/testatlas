import json
from pathlib import Path
from fastapi import FastAPI
from importlib.util import spec_from_file_location, module_from_spec

def _load_router_from_file(py_path: Path, attr: str = "router"):
    spec = spec_from_file_location(py_path.stem, py_path)
    if not spec or not spec.loader:
        return None
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return getattr(mod, attr, None)

def load_generated_plugins(app: FastAPI, generated_root: Path) -> list[dict]:
    loaded = []
    if not generated_root.exists():
        return loaded
    for d in sorted(generated_root.glob("*")):
        if not d.is_dir():
            continue
        mf = d / "manifest.json"
        if not mf.exists():
            continue
        try:
            manifest = json.loads(mf.read_text(encoding="utf-8"))
        except Exception:
            continue
        for r in manifest.get("routes", []):
            mod_file = d / r.get("module", "router.py")
            attr = r.get("attr", "router")
            router = _load_router_from_file(mod_file, attr)
            if router:
                app.include_router(router)
                loaded.append({"dir": d.name, "slug": manifest.get("slug"), "title": manifest.get("title")})
    return loaded
