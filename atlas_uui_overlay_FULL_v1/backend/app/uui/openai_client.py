
import os, json, requests
from typing import Dict, Any

def get_cfg(settings: Dict[str, Any]):
    base = (settings.get("openaiBaseUrl") or "https://api.openai.com").rstrip("/")
    key  = settings.get("openaiApiKey") or os.getenv("OPENAI_API_KEY") or ""
    model = settings.get("openaiModel") or "gpt-4o-mini"
    temp = settings.get("temperature")
    try:
        temp = float(temp) if temp is not None else 0.2
    except Exception:
        temp = 0.2
    return base, key, model, temp

def stream_chat(settings: Dict[str, Any], messages):
    base, key, model, temp = get_cfg(settings)
    url = base + "/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": temp, "stream": True}
    r = requests.post(url, headers=headers, data=json.dumps(payload), stream=True, timeout=120)
    r.raise_for_status()
    for line in r.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("data:"):
            data = line[len("data:"):].strip()
        else:
            data = line.strip()
        if data == "[DONE]":
            break
        try:
            obj = json.loads(data)
            delta = obj["choices"][0]["delta"].get("content")
            if delta:
                yield delta
        except Exception:
            continue

def vision(settings: Dict[str, Any], image_data_url: str):
    base, key, model, temp = get_cfg(settings)
    url = base + "/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role":"user","content":[
                {"type":"text","text":"Describe the image briefly and extract any visible text."},
                {"type":"image_url","image_url":{"url": image_data_url}}
            ]}
        ],
        "temperature": temp
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()

def stt(settings: Dict[str, Any], audio_path: str):
    base, key, model, temp = get_cfg(settings)
    url = base + "/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {key}"}
    files = {"file": open(audio_path, "rb")}
    data = {"model": "whisper-1"}
    r = requests.post(url, headers=headers, files=files, data=data, timeout=180)
    r.raise_for_status()
    return r.json()
