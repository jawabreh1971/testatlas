import os
import requests
from .settings import get_setting

def _env_or_setting(env_key: str, setting_key: str) -> str | None:
    v = os.getenv(env_key)
    if v:
        return v.strip()
    s = get_setting(setting_key)
    return s.strip() if s else None

def chat(messages: list[dict], temperature: float = 0.2) -> dict:
    base_url = _env_or_setting("EXTERNAL_LLM_BASE_URL", "llm.base_url") or "https://api.openai.com"
    api_key  = _env_or_setting("EXTERNAL_LLM_API_KEY", "llm.api_key")
    model    = _env_or_setting("EXTERNAL_LLM_MODEL", "llm.model") or "gpt-4o-mini"

    if not api_key:
        return {"ok": False, "error": "Missing EXTERNAL_LLM_API_KEY (or settings llm.api_key)."}

    url = base_url.rstrip("/") + "/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": temperature}

    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code >= 400:
        return {"ok": False, "error": f"LLM HTTP {r.status_code}", "details": r.text[:2000]}
    data = r.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception:
        content = None
    return {"ok": True, "model": model, "content": content, "raw": data}
