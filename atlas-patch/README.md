# Atlas Unified Factory Production Overlay Patch v5

Goal: "Close it for real" as a production-grade mini-factory on VSCode + GitHub + Render,
with minimal risk and without rebuilding from scratch.

This v5 patch is an OVERLAY (drop-in) that:
- Keeps SPA/API separation (no HTML under /api/*).
- Adds Windows-style React UI pages:
  - Chat (stored) + Mic (Speech Recognition in browser + audio upload stub)
  - Camera (WebRTC preview)
  - Web Learning Hub (Wikipedia/ArXiv/Crossref/RSS + URL fetch)
  - Video API (analyze URL stub + artifacts)
  - Builder/Foundry (generate product/plugin templates as ZIP artifacts)
  - Hooks (webhooks registry)
- Backend adds:
  - Learn Store (knowledge items) + lightweight search
  - Web providers (Wikipedia summary API, arXiv API, Crossref works, RSS fetch, URL fetch)
  - Media endpoints (STT stub, video analyze stub)
  - Builder Engine v2 (templates with Dockerfile, render.yaml, GitHub Actions)
  - Hooks registry (store + list)
  - Optional external LLM integration for /api/chat if EXTAPI_KEY is set (env).
    (This is optional and safe; if not configured, chat remains stored + MVP response.)

## New env vars (Render)
- ATLAS_DB_PATH=/var/data/app.db (recommended + persistent disk)
- ATLAS_ADMIN_TOKEN=... (optional for admin ops; if unset, admin ops are open)
- EXTAPI_KEY=... (optional: external LLM key)
- EXTERNAL_LLM_MODEL=gpt-4o-mini (optional)

## Apply
Run from repo root:
Windows:
python .\apply_atlas_unified_overlay_v5.py
powershell -ExecutionPolicy Bypass -File .\apply_atlas_unified_overlay_v5.ps1

Linux/mac:
python3 apply_atlas_unified_overlay_v5.py
bash apply_atlas_unified_overlay_v5.sh

Commit + push. Render redeploys.

## Smoke tests
BASE="https://testatlas.onrender.com"

curl -sS "$BASE/api/factory/health"
curl -sS "$BASE/api/learn/items?limit=5"
curl -sS "$BASE/api/web/wikipedia/summary?title=Artificial_intelligence" | head
