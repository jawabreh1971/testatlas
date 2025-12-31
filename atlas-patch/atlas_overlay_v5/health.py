from __future__ import annotations
from fastapi import FastAPI, APIRouter

def install_health(app: FastAPI) -> None:
    r = APIRouter(prefix="/api/factory", tags=["factory"])
    @r.get("/health")
    def health():
        return {"ok": True, "service": "atlas", "overlay": "v5"}
    app.include_router(r)
