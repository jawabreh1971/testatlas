
"""Auto patch common Atlas main files to include UUI router and mount UI."""

import re, time, shutil
from pathlib import Path

CANDIDATES = [Path("backend/app/main.py"), Path("backend/app/app_fixed.py"), Path("backend/app/main_fixed.py")]

IMPORT_LINE = "from app.uui.router import router as uui_router\n"
INCLUDE_LINE = "app.include_router(uui_router)\n"
STATIC_IMPORT = "from fastapi.staticfiles import StaticFiles\n"
MOUNT_LINE = "app.mount(\"/atlas-uui\", StaticFiles(directory=\"uui/dist\", html=True), name=\"atlas-uui\")\n"

def patch(p: Path):
    s = p.read_text(encoding="utf-8", errors="ignore")
    if "app.uui.router" in s:
        print("Already patched:", p)
        return True
    m = re.search(r"^\s*app\s*=\s*FastAPI\(", s, flags=re.M)
    if not m:
        return False
    lines = s.splitlines(True)
    insert_at = 0
    for i, ln in enumerate(lines[:160]):
        if ln.startswith("from ") or ln.startswith("import "):
            insert_at = i+1
    lines.insert(insert_at, IMPORT_LINE)
    # after app creation line
    app_i = None
    for i, ln in enumerate(lines):
        if re.match(r"^\s*app\s*=\s*FastAPI\(", ln):
            app_i = i
            break
    if app_i is None:
        return False
    lines.insert(app_i+1, INCLUDE_LINE)
    # mount if dist exists
    if Path("uui/dist").exists():
        if "StaticFiles" not in "".join(lines):
            lines.insert(insert_at+1, STATIC_IMPORT)
        lines.insert(app_i+2, MOUNT_LINE)
    new = "".join(lines)
    bak = p.with_suffix(p.suffix + f".bak_{int(time.time())}")
    shutil.copyfile(p, bak)
    p.write_text(new, encoding="utf-8")
    print("Patched:", p, "backup:", bak)
    return True

def main():
    for p in CANDIDATES:
        if p.exists() and patch(p):
            return
    raise SystemExit("No candidate found. Use tools/uui_manual_patch.md")

if __name__ == "__main__":
    main()
