from __future__ import annotations
import os, time, sqlite3, hashlib
from typing import Dict

def env(key: str, default: str = "") -> str:
    v = os.environ.get(key, "").strip()
    return v if v else default

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def ensure_dir(path: str) -> None:
    if path:
        os.makedirs(path, exist_ok=True)

def db_path() -> str:
    return env("ATLAS_DB_PATH", "backend/data/app.db")

def connect() -> sqlite3.Connection:
    p = db_path()
    ensure_dir(os.path.dirname(p))
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    return con

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def admin_expected() -> str:
    return env("ATLAS_ADMIN_TOKEN", "").strip()

def require_admin(headers: Dict[str, str]) -> None:
    exp = admin_expected()
    if not exp:
        return
    token = (headers.get("X-Atlas-Admin-Token") or "").strip()
    if not token:
        raise PermissionError("Admin token required (X-Atlas-Admin-Token).")
    if token != exp:
        raise PermissionError("Invalid admin token.")
