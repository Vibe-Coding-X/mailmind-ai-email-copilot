Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $RepoRoot "frontend"
$EnvLocal = Join-Path $FrontendDir ".env.local"

if (-not (Test-Path -LiteralPath $EnvLocal)) {
    Write-Host "Missing frontend/.env.local. Copy frontend/.env.example for local API config."
}

Write-Host "Starting MailMind frontend at http://localhost:3000"
Push-Location $FrontendDir
try {
    npm run dev -- --port 3000
}
finally {
    Pop-Location
}
