from __future__ import annotations
from fastapi import FastAPI
from .health import install_health
from .spa_guard import install_spa_guard
from .plugins import install_plugins
from .engines import install_engines
from .foundry import install_foundry
from .chat_store import install_chat_store
from .learn_store import install_learn_store
from .web_hub import install_web_hub
from .media import install_media
from .builder_v2 import install_builder_v2
from .hooks import install_hooks

VERSION = "overlay-v5.0.0"

def install_overlay_v5(app: FastAPI) -> None:
    install_health(app)
    install_plugins(app)
    install_engines(app)
    install_foundry(app)
    install_chat_store(app)
    install_learn_store(app)
    install_web_hub(app)
    install_media(app)
    install_builder_v2(app)
    install_hooks(app)
    install_spa_guard(app)
