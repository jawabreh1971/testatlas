\
$ErrorActionPreference = "Stop"
$ROOT = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location "$ROOT\frontend"
npm install
npm run build
if (Test-Path "$ROOT\backend\app\static") { Remove-Item -Recurse -Force "$ROOT\backend\app\static" }
New-Item -ItemType Directory -Force -Path "$ROOT\backend\app\static" | Out-Null
Copy-Item -Recurse -Force "$ROOT\frontend\dist\*" "$ROOT\backend\app\static\"
Write-Host "OK: frontend dist copied to backend\app\static"
