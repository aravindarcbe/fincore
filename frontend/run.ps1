# Runs the FinCore frontend on Windows: installs dependencies if missing,
# then starts the dev server. Always operates on this script's own folder,
# so it doesn't matter which directory you launched it from.
#
# Usage:
#   .\run.ps1            # port 5173
#   .\run.ps1 -Port 5174 # custom port

param(
    [int]$Port = 5173
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\node_modules")) {
    Write-Host "Installing dependencies..."
    npm install
}

Write-Host ""
Write-Host "Starting FinCore frontend on http://localhost:$Port ..."
Write-Host "Make sure the backend (backend\run.ps1) is running too - this proxies /api to it."
Write-Host ""
npm run dev -- --port $Port
