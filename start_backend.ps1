# ── Start Backend ─────────────────────────────────────────────────────────────
# Run this from the project root: .\start_backend.ps1

$projectRoot = $PSScriptRoot
$venvPython  = Join-Path $projectRoot "venv\Scripts\python.exe"
$uvicorn     = Join-Path $projectRoot "venv\Scripts\uvicorn.exe"
$backendDir  = Join-Path $projectRoot "backend"

Write-Host "⚡ Starting AI Business Intelligence Backend..." -ForegroundColor Green
Write-Host "   Backend dir : $backendDir" -ForegroundColor Gray
Write-Host "   API docs    : http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Run uvicorn with backend/ as the app directory so relative imports work
Set-Location $backendDir
& $uvicorn main:app --reload --host 0.0.0.0 --port 8000
