Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$EnvLocal = Join-Path $BackendDir ".env.local"

if (-not (Test-Path -LiteralPath $EnvLocal)) {
    Write-Host "Missing backend/.env.local. Copy backend/.env.example and fill local test values."
}

Write-Host "Starting MailMind Celery worker with Windows-friendly --pool=solo"
Push-Location $BackendDir
try {
    uv run celery -A app.jobs.celery_app worker --loglevel=info --pool=solo
}
finally {
    Pop-Location
}
