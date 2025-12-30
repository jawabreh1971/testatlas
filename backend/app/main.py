import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from .routers.health import router as health_router
from .routers.settings_api import router as settings_router
from .routers.chat_api import router as chat_router
from .routers.admin_factory import router as admin_factory_router
from .core.plugin_loader import load_generated_plugins

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"
GENERATED_PLUGINS_DIR = BASE_DIR / "plugins_generated"

app = FastAPI(title="Atlas v6 Unified", version="6.0.0")

# API
app.include_router(health_router)
app.include_router(settings_router)
app.include_router(chat_router)
app.include_router(admin_factory_router)

_loaded = load_generated_plugins(app, GENERATED_PLUGINS_DIR)

# Static (React build copied into backend/app/static)
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

@app.get("/", response_class=HTMLResponse)
def root():
    if INDEX_HTML.exists():
        return INDEX_HTML.read_text(encoding="utf-8")
    return "<h1>Atlas v6 Unified</h1><p>Frontend build missing. Run ops/build_frontend.(ps1|sh)</p>"

@app.get("/{path:path}", response_class=HTMLResponse)
def spa_fallback(path: str):
    # Single-page app fallback
    if INDEX_HTML.exists():
        return INDEX_HTML.read_text(encoding="utf-8")
    return "<h1>Atlas v6 Unified</h1><p>Frontend build missing.</p>"
