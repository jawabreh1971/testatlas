from datetime import datetime, timezone
from .db import db

def get_setting(k: str) -> str | None:
    with db() as conn:
        row = conn.execute("SELECT v FROM settings WHERE k = ?", (k,)).fetchone()
        return row[0] if row else None

def set_setting(k: str, v: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    with db() as conn:
        conn.execute(
            "INSERT INTO settings(k,v,updated_at) VALUES (?,?,?) "
            "ON CONFLICT(k) DO UPDATE SET v=excluded.v, updated_at=excluded.updated_at",
            (k, v, ts),
        )

def list_settings(prefix: str | None = None) -> list[tuple[str,str,str]]:
    with db() as conn:
        if prefix:
            return list(conn.execute("SELECT k,v,updated_at FROM settings WHERE k LIKE ? ORDER BY k", (prefix + "%",)))
        return list(conn.execute("SELECT k,v,updated_at FROM settings ORDER BY k"))
