# Atlas v6 Unified (Runtime + Internal Factory)

## What you get
- FastAPI backend serving a React (Vite) Windows-style UI as a single service.
- Chat endpoint with External LLM (OpenAI-compatible) via env or settings DB.
- Internal Factory Engine (Admin-only) to generate plugins into backend/app/plugins_generated/.

## Local run (Windows)
1) Backend
   - cd backend
   - python -m venv .venv
   - .\.venv\Scripts\activate
   - pip install -r requirements.txt
   - uvicorn app.main:app --host 0.0.0.0 --port 8080

2) Frontend
   - cd frontend
   - npm install
   - npm run build
   - Copy frontend/dist -> backend/app/static  (or run ops/build_frontend.ps1)

## Env
- EXTERNAL_LLM_BASE_URL
- EXTERNAL_LLM_API_KEY
- EXTERNAL_LLM_MODEL
- ATLAS_ADMIN_TOKEN (enables /api/admin/factory/*)
- ATLAS_DB_PATH (SQLite path, default backend/data/app.db)
