
#!/usr/bin/env bash
set -e
cd backend
export ATLAS_ADDONS="uui,v4,v4_1"
export ATLAS_INTERNAL_BASE_URL="${ATLAS_INTERNAL_BASE_URL:-http://127.0.0.1:8000}"
uvicorn app.main:app --reload --port 8000
