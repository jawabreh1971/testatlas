import os
from fastapi import Header, HTTPException

def require_admin(x_atlas_admin_token: str | None = Header(default=None)) -> None:
    expected = os.getenv("ATLAS_ADMIN_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Admin token not configured (ATLAS_ADMIN_TOKEN missing).")
    if not x_atlas_admin_token or x_atlas_admin_token.strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid admin token.")
