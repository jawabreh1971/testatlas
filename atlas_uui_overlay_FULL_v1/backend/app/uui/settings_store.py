
import json, os
from typing import Any, Dict

DEFAULT_PATH = os.getenv("UUI_SETTINGS_PATH", "backend/data/uui_settings.json")

def _ensure_dir(p: str):
    os.makedirs(os.path.dirname(p), exist_ok=True)

def load_settings(path: str = DEFAULT_PATH) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

def save_settings(data: Dict[str, Any], path: str = DEFAULT_PATH) -> None:
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data or {}, f, ensure_ascii=False, indent=2)
