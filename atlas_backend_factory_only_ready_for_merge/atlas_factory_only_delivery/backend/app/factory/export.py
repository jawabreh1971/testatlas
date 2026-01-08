from fastapi import APIRouter, HTTPException
from pathlib import Path
import zipfile, json, tempfile, shutil, hashlib

router = APIRouter(prefix="/api/factory", tags=["factory"])

BASE = Path(__file__).resolve().parents[3]
TEMPLATES = BASE / "templates"

def _hash_file(p: Path):
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()

def _copytree(src: Path, dst: Path):
    for p in src.rglob("*"):
        if p.is_dir():
            continue
        target = dst / p.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(p.read_bytes())

@router.post("/export")
def export_platform(spec: dict):
    # Basic validation
    try:
        platform = spec["platform"]
        modules = spec.get("modules", [])
        deploy = spec.get("deploy", {})
    except Exception as e:
        raise HTTPException(400, f"Invalid spec: {e}")

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / f"{platform.get('slug','atlas_platform')}_onprem_v1"
        out.mkdir(parents=True, exist_ok=True)

        # Core
        _copytree(TEMPLATES / "core" / "backend", out / "backend")
        _copytree(TEMPLATES / "core" / "frontend", out / "frontend")

        # Modules
        for m in modules:
            mod = TEMPLATES / "modules" / m
            if mod.exists():
                _copytree(mod, out / "backend" / "modules" / m)

        # Deploy profile
        profile = deploy.get("profile", "onprem_dockercompose")
        _copytree(TEMPLATES / "deploy_profiles" / profile, out / "ops")

        # Write README and env example
        (out / "README_DEPLOY.md").write_text("Run: docker compose up -d\n", encoding="utf-8")
        (out / ".env.example").write_text("JWT_SECRET=change_me\nOCR_API_KEY=change_me\n", encoding="utf-8")

        # Zip
        zip_path = Path(td) / f"{out.name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in out.rglob("*"):
                if p.is_file():
                    z.write(p, p.relative_to(out))

        checksum = _hash_file(zip_path)
        return {"status":"ok","artifact":zip_path.name,"checksum":checksum}