$ErrorActionPreference = "Stop"
Write-Host "[1/2] Installing backend deps (best-effort)..."
if (Test-Path ".\backend\requirements.txt") {
  python -m pip install -r .\backend\requirements.txt
} elseif (Test-Path ".\requirements.txt") {
  python -m pip install -r .\requirements.txt
}

Write-Host "[2/2] Installing frontend deps..."
if (Test-Path ".\frontend\package.json") {
  Push-Location ".\frontend"
  npm install
  Pop-Location
} elseif (Test-Path ".\package.json") {
  npm install
}
Write-Host "[DONE] Commit & push; Render redeploys."
