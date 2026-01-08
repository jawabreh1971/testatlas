from __future__ import annotations
import re, json, xml.etree.ElementTree as ET
from typing import Any, Dict, List
from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
import requests

UA = "AtlasWebHub/1.0"

def _clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    return s

def _extract_basic(html: str) -> Dict[str, Any]:
    # Lightweight extraction: title + first ~6 paragraphs text
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I|re.S)
    if m:
        title = _clean_text(re.sub(r"<.*?>", "", m.group(1)))
    # strip scripts/styles
    html2 = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    # get paragraphs
    paras = re.findall(r"(?is)<p[^>]*>(.*?)</p>", html2)[:12]
    txts = []
    for p in paras:
        t = _clean_text(re.sub(r"<.*?>", "", p))
        if len(t) > 60:
            txts.append(t)
    return {"title": title, "snippets": txts[:6]}

def install_web_hub(app: FastAPI) -> None:
    r = APIRouter(prefix="/api/web", tags=["web"])

    @r.post("/fetch")
    def fetch_url(payload: Dict[str, Any]):
        url = str(payload.get("url") or "").strip()
        if not url.startswith(("http://","https://")):
            return JSONResponse({"ok": False, "error":"invalid_url"}, status_code=422)
        rr = requests.get(url, headers={"User-Agent": UA}, timeout=25)
        data = _extract_basic(rr.text)
        return {"ok": True, "url": url, "status": rr.status_code, **data}

    @r.get("/wikipedia/summary")
    def wiki_summary(title: str):
        title = title.strip()
        if not title:
            return JSONResponse({"ok": False, "error":"title_required"}, status_code=422)
        api = "https://en.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(title)
        rr = requests.get(api, headers={"User-Agent": UA}, timeout=20)
        if rr.status_code != 200:
            return JSONResponse({"ok": False, "status": rr.status_code}, status_code=rr.status_code)
        j = rr.json()
        return {"ok": True, "title": j.get("title"), "extract": j.get("extract"), "url": (j.get("content_urls") or {}).get("desktop",{}).get("page","")}

    @r.get("/arxiv/search")
    def arxiv_search(q: str, limit: int = 5):
        limit = max(1, min(int(limit), 20))
        q = q.strip()
        if not q:
            return JSONResponse({"ok": False, "error":"q_required"}, status_code=422)
        url = f"http://export.arxiv.org/api/query?search_query=all:{requests.utils.quote(q)}&start=0&max_results={limit}"
        rr = requests.get(url, headers={"User-Agent": UA}, timeout=25)
        root = ET.fromstring(rr.text)
        ns = {"a":"http://www.w3.org/2005/Atom"}
        items = []
        for e in root.findall("a:entry", ns):
            items.append({
                "title": _clean_text((e.findtext("a:title", default="", namespaces=ns) or "")),
                "id": (e.findtext("a:id", default="", namespaces=ns) or ""),
                "published": (e.findtext("a:published", default="", namespaces=ns) or ""),
                "summary": _clean_text((e.findtext("a:summary", default="", namespaces=ns) or ""))[:1000],
            })
        return {"ok": True, "q": q, "items": items}

    @r.get("/crossref/works")
    def crossref_works(q: str, rows: int = 5):
        rows = max(1, min(int(rows), 20))
        q = q.strip()
        if not q:
            return JSONResponse({"ok": False, "error":"q_required"}, status_code=422)
        url = "https://api.crossref.org/works"
        rr = requests.get(url, params={"query": q, "rows": rows}, headers={"User-Agent": UA}, timeout=25)
        j = rr.json()
        out = []
        for it in (j.get("message", {}).get("items") or []):
            title = (it.get("title") or [""])[0]
            doi = it.get("DOI","")
            out.append({"title": title, "doi": doi, "type": it.get("type",""), "issued": (it.get("issued",{}).get("date-parts") or [[]])[0]})
        return {"ok": True, "q": q, "items": out}

    @r.get("/rss")
    def rss(url: str, limit: int = 10):
        limit = max(1, min(int(limit), 30))
        if not url.startswith(("http://","https://")):
            return JSONResponse({"ok": False, "error":"invalid_url"}, status_code=422)
        rr = requests.get(url, headers={"User-Agent": UA}, timeout=25)
        root = ET.fromstring(rr.text)
        items = []
        for it in root.findall(".//item")[:limit]:
            items.append({
                "title": _clean_text(it.findtext("title","")),
                "link": _clean_text(it.findtext("link","")),
                "pubDate": _clean_text(it.findtext("pubDate","")),
            })
        return {"ok": True, "items": items}

    app.include_router(r)
