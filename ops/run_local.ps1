\
$ErrorActionPreference = "Stop"
$ROOT = (Resolve-Path "$PSScriptRoot\..").Path
$env:ATLAS_DB_PATH = $env:ATLAS_DB_PATH
if (-not $env:ATLAS_DB_PATH) { $env:ATLAS_DB_PATH = "$ROOT\backend\data\app.db" }
Set-Location "$ROOT\backend"
python -m venv .venv
& "$ROOT\backend\.venv\Scripts\pip.exe" install -r requirements.txt
& "$ROOT\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8080
