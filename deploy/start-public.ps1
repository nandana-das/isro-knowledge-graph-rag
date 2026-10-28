# Make the live KG-RAG API reachable from the hosted website.
# Starts Ollama (if needed), the API, and an ngrok tunnel on your static domain.
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File deploy\start-public.ps1
# Stop: close the two windows it opens (API and ngrok).

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $PSScriptRoot "public.env"

if (-not (Test-Path $EnvFile)) {
    Write-Host "Missing deploy\public.env. Copy deploy\public.env.example to deploy\public.env and fill it in." -ForegroundColor Red
    exit 1
}
$Config = @{}
Get-Content $EnvFile | Where-Object { $_ -match '^\s*[A-Z_]+\s*=' } | ForEach-Object {
    $Name, $Value = $_ -split '=', 2
    $Config[$Name.Trim()] = $Value.Trim()
}
foreach ($Key in "NGROK_DOMAIN", "FRONTEND_ORIGIN") {
    if (-not $Config[$Key] -or $Config[$Key] -like "*your-*") {
        Write-Host "Set $Key in deploy\public.env first." -ForegroundColor Red
        exit 1
    }
}
$Domain = $Config["NGROK_DOMAIN"] -replace '^https?://', '' -replace '/$', ''

if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Host "ngrok is not installed. See deploy\README.md, step 1." -ForegroundColor Red
    exit 1
}
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "Project virtual environment not found at $Python" -ForegroundColor Red
    exit 1
}

# 1. Ollama
try {
    Invoke-RestMethod http://127.0.0.1:11434/api/version -TimeoutSec 3 | Out-Null
    Write-Host "Ollama: already running"
} catch {
    Write-Host "Ollama: starting"
    Start-Process ollama -ArgumentList "serve" -WindowStyle Minimized
    Start-Sleep -Seconds 5
}

# 2. API (live mode), allowing the website's address
$Origins = "http://localhost:5173,http://127.0.0.1:5173," + $Config["FRONTEND_ORIGIN"]
$ApiCommand = "`$env:HF_HUB_OFFLINE='1'; `$env:TRANSFORMERS_OFFLINE='1'; `$env:KG_RAG_CORS_ORIGINS='$Origins'; " +
              "Set-Location '$Root'; & '$Python' -m src.api"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $ApiCommand
Write-Host "API: starting in a new window (about 2-3 minutes to warm up)"

# 3. Tunnel
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ngrok http 8000 --url=https://$Domain"
Write-Host "ngrok: tunnel starting in a new window"

Write-Host ""
Write-Host "Live API (public): https://$Domain/api/health" -ForegroundColor Green
Write-Host "Website:           $($Config['FRONTEND_ORIGIN'])" -ForegroundColor Green
Write-Host "The website switches from 'offline' to 'live' by itself once the API is ready."
