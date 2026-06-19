# Start Arize Phoenix trace UI (required for http://localhost:6006)
Set-Location $PSScriptRoot\..
Write-Host "Starting Phoenix on http://localhost:6006 (OTLP gRPC on :4317)..."
.\venv\Scripts\phoenix serve
