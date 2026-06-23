Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$EnvLocal = Join-Path $BackendDir ".env.local"

if (-not (Test-Path -LiteralPath $EnvLocal)) {
    Write-Host "Missing backend/.env.local. Copy backend/.env.example and fill local test values."
}

Write-Host "Starting MailMind backend at http://localhost:8000"
Push-Location $BackendDir
try {
    uv run uvicorn app.main:app --reload --host localhost --port 8000
}
finally {
    Pop-Location
}
