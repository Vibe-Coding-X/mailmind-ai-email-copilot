Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ConfigDir = "F:\WorkSpace\mailmind-local-config"
$BackendSource = Join-Path $ConfigDir "backend.env.local"
$FrontendSource = Join-Path $ConfigDir "frontend.env.local"
$BackendTarget = Join-Path $RepoRoot "backend\.env.local"
$FrontendTarget = Join-Path $RepoRoot "frontend\.env.local"

if (-not (Test-Path -LiteralPath $ConfigDir)) {
    Write-Host "Missing centralized config directory: $ConfigDir"
    Write-Host "Create backend.env.local and frontend.env.local there first."
    exit 1
}

if (-not (Test-Path -LiteralPath $BackendSource)) {
    Write-Host "Missing $BackendSource"
    exit 1
}

if (-not (Test-Path -LiteralPath $FrontendSource)) {
    Write-Host "Missing $FrontendSource"
    exit 1
}

Copy-Item -LiteralPath $BackendSource -Destination $BackendTarget -Force
Copy-Item -LiteralPath $FrontendSource -Destination $FrontendTarget -Force

if (-not (Test-Path -LiteralPath $BackendTarget)) {
    Write-Host "Failed to create backend/.env.local"
    exit 1
}

if (-not (Test-Path -LiteralPath $FrontendTarget)) {
    Write-Host "Failed to create frontend/.env.local"
    exit 1
}

Write-Host "Copied local env files into this worktree."
Write-Host "backend/.env.local: present"
Write-Host "frontend/.env.local: present"

$BackendIgnored = git -C $RepoRoot check-ignore -v "backend/.env.local"
$FrontendIgnored = git -C $RepoRoot check-ignore -v "frontend/.env.local"

if (-not $BackendIgnored) {
    Write-Host "backend/.env.local is not ignored by Git."
    exit 1
}

if (-not $FrontendIgnored) {
    Write-Host "frontend/.env.local is not ignored by Git."
    exit 1
}

Write-Host "backend/.env.local ignored: yes"
Write-Host "frontend/.env.local ignored: yes"
