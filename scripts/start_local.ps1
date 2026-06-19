# Start Enterprise RAG locally (Windows)
# Run from enterprise-rag folder: .\scripts\start_local.ps1

$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    .\venv\Scripts\pip install -r requirements.txt
}

$env:USE_MOCK_LLM = "true"
$env:PYTHONPATH = "."

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Enterprise RAG - Local Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting 3 services in separate windows..."
Write-Host ""

# API
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Root'; `$env:USE_MOCK_LLM='true'; `$env:PYTHONPATH='.'; .\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000"
)

Start-Sleep -Seconds 2

# Streamlit
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Root'; .\venv\Scripts\streamlit run streamlit_app/app.py --server.headless true --server.port 8501"
)

Start-Sleep -Seconds 1

# Phoenix
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Root'; .\venv\Scripts\phoenix serve"
)

Write-Host "Services starting..." -ForegroundColor Green
Write-Host ""
Write-Host "  Streamlit UI : http://localhost:8501  (login: admin / admin123)" -ForegroundColor Yellow
Write-Host "  API Docs     : http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  Phoenix      : http://localhost:6006" -ForegroundColor Yellow
Write-Host ""
Write-Host "First startup downloads ML models (~2 min). Wait then open Streamlit." -ForegroundColor Gray
Write-Host "Run tests: .\venv\Scripts\pytest tests\ -q" -ForegroundColor Gray
