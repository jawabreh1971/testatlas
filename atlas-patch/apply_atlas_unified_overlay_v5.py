#!/usr/bin/env python3
from __future__ import annotations
import re, sys, time, json
from pathlib import Path

INJECT_IMPORT = "from atlas_overlay_v5 import install_overlay_v5"
INJECT_CALL = "install_overlay_v5(app)"

BACKEND_CANDIDATES = ["backend/app/main.py","backend/main.py","app/main.py","main.py"]
REQ_CANDIDATES = ["backend/requirements.txt","requirements.txt"]
PKG_CANDIDATES = ["frontend/package.json","package.json"]
MAIN_CANDIDATES = ["frontend/src/main.tsx","src/main.tsx"]

def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")

def write_text(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8")

def find_backend_entry(root: Path) -> Path | None:
    for rel in BACKEND_CANDIDATES:
        p = root / rel
        if p.exists() and p.is_file():
            if "FastAPI(" in read_text(p):
                return p
    for p in root.rglob("*.py"):
        sp = str(p).lower()
        if any(x in sp for x in [".venv","venv","node_modules","__pycache__","dist","build"]):
            continue
        t = read_text(p)
        if "FastAPI(" in t and re.search(r"\bapp\s*=\s*FastAPI\(", t):
            return p
    return None

def copy_overlay(root: Path) -> None:
    src_dir = Path(__file__).resolve().parent / "atlas_overlay_v5"
    dst_dir = root / "atlas_overlay_v5"
    dst_dir.mkdir(parents=True, exist_ok=True)
    for fp in src_dir.rglob("*"):
        if fp.is_file():
            rel = fp.relative_to(src_dir)
            out = dst_dir / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(fp.read_text(encoding="utf-8"), encoding="utf-8")
    print("[OK] Copied atlas_overlay_v5/")

def ensure_requirements(root: Path) -> None:
    req = None
    for rel in REQ_CANDIDATES:
        p = root / rel
        if p.exists():
            req = p
            break
    if not req:
        print("[SKIP] requirements.txt not found")
        return
    txt = read_text(req)
    add = []
    if not re.search(r"(?im)^requests\b", txt):
        add.append("requests>=2.31.0")
    if add:
        txt = txt.rstrip() + "\n" + "\n".join(add) + "\n"
        write_text(req, txt)
        print(f"[OK] Updated requirements: {req}")

def inject_backend(entry: Path) -> None:
    src = read_text(entry)
    if "install_overlay_v5(" in src:
        print("[OK] Backend already injected")
        return
    # Remove older overlay imports/calls if present (v3/v4) to avoid double mount
    src = re.sub(r"(?m)^from\s+atlas_overlay_v3\s+import\s+install_overlay_v3\s*\n", "", src)
    src = re.sub(r"(?m)^from\s+atlas_overlay_v4\s+import\s+install_overlay_v4\s*\n", "", src)
    src = re.sub(r"(?m)^\s*install_overlay_v3\(app\)\s*\n", "", src)
    src = re.sub(r"(?m)^\s*install_overlay_v4\(app\)\s*\n", "", src)

    lines = src.splitlines(True)
    insert_at = 0
    for i, line in enumerate(lines[:260]):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = i + 1
    lines.insert(insert_at, INJECT_IMPORT + "\n")
    src = "".join(lines)

    src2 = re.sub(r"(?m)^(\s*app\s*=\s*FastAPI\([^\n]*\)\s*)$", r"\1\n" + INJECT_CALL + "\n", src, count=1)
    if src2 == src:
        src2 = re.sub(r"(?ms)^(\s*app\s*=\s*FastAPI\((?:.*?)\)\s*)$", r"\1\n" + INJECT_CALL + "\n", src, count=1)
    if src2 == src:
        raise RuntimeError("Could not find app = FastAPI(...) to inject after.")
    ts = time.strftime("%Y%m%d_%H%M%S")
    bak = entry.with_suffix(entry.suffix + f".bak.{ts}")
    bak.write_text(read_text(entry), encoding="utf-8")
    write_text(entry, src2)
    print(f"[OK] Injected overlay v5 into {entry} (backup: {bak})")

def patch_frontend(root: Path) -> None:
    pkg = None
    for rel in PKG_CANDIDATES:
        p = root / rel
        if p.exists():
            pkg = p
            break
    if not pkg:
        print("[SKIP] package.json not found")
        return
    data = json.loads(read_text(pkg))
    deps = data.get("dependencies", {}) or {}
    deps.setdefault("@fluentui/react-components", "^9.60.0")
    deps.setdefault("@fluentui/react-icons", "^2.0.251")
    data["dependencies"] = deps
    write_text(pkg, json.dumps(data, indent=2) + "\n")
    print(f"[OK] Ensured Fluent deps in {pkg}")

    mainp = None
    for rel in MAIN_CANDIDATES:
        p = root / rel
        if p.exists():
            mainp = p
            break
    if not mainp:
        print("[SKIP] main.tsx not found")
        return

    tpl = Path(__file__).resolve().parent / "frontend_templates" / "AppShell.tsx"
    app_shell = mainp.parent / "AppShell.tsx"
    app_shell.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")

    patched = (
      'import React from "react";\n'
      'import ReactDOM from "react-dom/client";\n'
      'import AppShell from "./AppShell";\n\n'
      'ReactDOM.createRoot(document.getElementById("root")!).render(\n'
      '  <React.StrictMode>\n'
      '    <AppShell />\n'
      '  </React.StrictMode>\n'
      ');\n'
    )
    write_text(mainp, patched)
    print(f"[OK] Patched frontend entry {mainp}")

def main():
    root = Path(".").resolve()
    entry = find_backend_entry(root)
    if not entry:
        print("[ERR] Could not locate backend entry. Run from repo root.")
        sys.exit(2)

    copy_overlay(root)
    ensure_requirements(root)
    inject_backend(entry)
    patch_frontend(root)
    print("[DONE] Atlas Unified Overlay v5 applied.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
