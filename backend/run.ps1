# Runs the FinCore backend on Windows: creates the venv if missing, installs
# dependencies, then starts the API. Always operates on this script's own
# folder, so it doesn't matter which directory you launched it from.
#
# Usage:
#   .\run.ps1            # port 8000
#   .\run.ps1 -Port 8001 # custom port

param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

Write-Host "Installing dependencies..."
.\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.\venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host ""
Write-Host "Starting FinCore backend on http://localhost:$Port ..."
Write-Host "If you change this port, update frontend/vite.config.js's proxy target to match."
Write-Host ""
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port $Port
