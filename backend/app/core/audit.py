import json
from datetime import datetime, timezone
from .db import db

def audit(event: str, meta: dict) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    with db() as conn:
        conn.execute(
            "INSERT INTO audit(ts,event,meta_json) VALUES (?,?,?)",
            (ts, event, json.dumps(meta, ensure_ascii=False)),
        )
