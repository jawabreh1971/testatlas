# Atlas v6 - VSCode Local Runner (VERBOSE + PROOF)
$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path "$PSScriptRoot").Path
$LOG  = Join-Path $ROOT "run_vscode.log"

"===== Atlas Runner START: $(Get-Date) =====" | Out-File -FilePath $LOG -Encoding UTF8
"ROOT=$ROOT" | Tee-Object -FilePath $LOG -Append

function Step($name, $block) {
  "`n--- $name ---" | Tee-Object -FilePath $LOG -Append
  & $block 2>&1 | Tee-Object -FilePath $LOG -Append
  if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
    throw "Step failed: $name (exit=$LASTEXITCODE). See $LOG"
  }
}

Step "Sanity check: folders" {
  if (!(Test-Path (Join-Path $ROOT "backend"))) { throw "Missing folder: backend" }
  if (!(Test-Path (Join-Path $ROOT "frontend"))) { throw "Missing folder: frontend" }
  "OK: backend/frontend exist"
}

Step "Tooling versions" {
  "where python: " + (Get-Command python -ErrorAction SilentlyContinue).Source
  "where npm: " + (Get-Command npm -ErrorAction SilentlyContinue).Source
  python --version
  npm --version
}

# ENV
$env:ATLAS_DB_PATH = Join-Path $ROOT "backend\data\app.db"
"ENV ATLAS_DB_PATH=$env:ATLAS_DB_PATH" | Tee-Object -FilePath $LOG -Append

# Backend
Step "Backend: create venv (if missing)" {
  Set-Location (Join-Path $ROOT "backend")
  if (!(Test-Path ".venv")) {
    "Creating .venv ..."
    python -m venv .venv
  } else {
    "OK: .venv exists"
  }
}

Step "Backend: install requirements" {
  Set-Location (Join-Path $ROOT "backend")
  & ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
  & ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
  "OK: requirements installed"
}

# Frontend
Step "Frontend: npm install (if missing)" {
  Set-Location (Join-Path $ROOT "frontend")
  if (!(Test-Path "node_modules")) {
    "Running npm install ..."
    npm install
  } else {
    "OK: node_modules exists"
  }
}

Step "Frontend: build (vite)" {
  Set-Location (Join-Path $ROOT "frontend")
  npm run build
  if (!(Test-Path "dist")) { throw "Build finished but dist/ not found" }
  "OK: dist exists"
}

# Copy dist -> backend/app/static
Step "Copy frontend dist -> backend/app/static" {
  Set-Location $ROOT
  $staticPath = Join-Path $ROOT "backend\app\static"
  if (Test-Path $staticPath) { Remove-Item -Recurse -Force $staticPath }
  New-Item -ItemType Directory -Force -Path $staticPath | Out-Null
  Copy-Item -Recurse -Force (Join-Path $ROOT "frontend\dist\*") $staticPath
  "OK: copied to $staticPath"
  "Static files count: " + (Get-ChildItem -Recurse $staticPath | Measure-Object).Count
}

# Proof markers
Step "PROOF: write marker file" {
  $marker = Join-Path $ROOT "RUNNER_PROOF.txt"
  "Atlas runner executed at $(Get-Date)" | Out-File -FilePath $marker -Encoding UTF8
  "OK: wrote $marker"
}

# Run backend
Step "Run backend (uvicorn)" {
  Set-Location (Join-Path $ROOT "backend")
  "Starting on http://localhost:8080"
  & ".\.venv\Scripts\python.exe" -m uvicorn "backend.app.main:app" --host "0.0.0.0" --port 8080
}

"===== Atlas Runner END: $(Get-Date) =====" | Tee-Object -FilePath $LOG -Append
