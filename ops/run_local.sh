#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export ATLAS_DB_PATH="${ATLAS_DB_PATH:-$ROOT/backend/data/app.db}"
cd "$ROOT/backend"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
