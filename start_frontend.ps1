# ── Start Frontend ────────────────────────────────────────────────────────────
# Run this from the project root: .\start_frontend.ps1

$projectRoot  = $PSScriptRoot
$streamlit    = Join-Path $projectRoot "venv\Scripts\streamlit.exe"
$frontendApp  = Join-Path $projectRoot "frontend\app.py"

Write-Host "⚡ Starting Clarity AI Frontend..." -ForegroundColor Green
Write-Host "   App file : $frontendApp" -ForegroundColor Gray
Write-Host "   URL      : http://localhost:8501" -ForegroundColor Cyan
Write-Host ""

& $streamlit run $frontendApp --server.port 8501
