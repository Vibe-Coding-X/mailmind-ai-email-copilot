Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Opening backend, worker, and frontend dev processes."
Start-Process powershell -WindowStyle Hidden -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    (Join-Path $RepoRoot "scripts\dev-backend.ps1")
)
Start-Process powershell -WindowStyle Hidden -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    (Join-Path $RepoRoot "scripts\dev-worker.ps1")
)
Start-Process powershell -WindowStyle Hidden -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    (Join-Path $RepoRoot "scripts\dev-frontend.ps1")
)
