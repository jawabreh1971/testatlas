
import re, requests
from urllib.parse import urlparse

PRIVATE_NETS = (
    re.compile(r"^10\."),
    re.compile(r"^127\."),
    re.compile(r"^169\.254\."),
    re.compile(r"^172\.(1[6-9]|2[0-9]|3[0-1])\."),
    re.compile(r"^192\.168\."),
)

def is_private_host(host: str) -> bool:
    if not host:
        return True
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", host):
        for pat in PRIVATE_NETS:
            if pat.match(host):
                return True
    return False

def safe_fetch(url: str, max_chars: int = 120000):
    u = urlparse(url)
    if u.scheme not in ("http","https"):
        return {"ok": False, "error": "scheme_not_allowed"}
    if is_private_host(u.hostname or ""):
        return {"ok": False, "error": "private_host_blocked"}
    r = requests.get(url, timeout=30, headers={"User-Agent":"AtlasUUI/1.0"})
    text = r.text[:max_chars]
    return {"ok": True, "status": r.status_code, "content_type": r.headers.get("content-type",""), "text": text}
