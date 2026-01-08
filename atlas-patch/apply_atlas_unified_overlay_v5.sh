#!/usr/bin/env bash
set -euo pipefail
echo "[1/2] Install backend deps (best-effort)"
if [ -f "backend/requirements.txt" ]; then
  python3 -m pip install -r backend/requirements.txt || true
elif [ -f "requirements.txt" ]; then
  python3 -m pip install -r requirements.txt || true
fi

echo "[2/2] Install frontend deps"
if [ -f "frontend/package.json" ]; then
  (cd frontend && npm install)
elif [ -f "package.json" ]; then
  npm install
fi
echo "[DONE] Commit & push; Render redeploys."
