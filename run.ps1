# NutriMate PowerShell Execution Script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting NutriMate Nutrition Planner Application..." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Cyan

if (Test-Path "$scriptDir\.venv\Scripts\python.exe") {
    & "$scriptDir\.venv\Scripts\python.exe" app.py
} elseif (Test-Path "$scriptDir\venv\Scripts\python.exe") {
    & "$scriptDir\venv\Scripts\python.exe" app.py
} else {
    Write-Host "[INFO] Setting up virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    & "$scriptDir\.venv\Scripts\pip.exe" install -r requirements.txt flask-cors
    & "$scriptDir\.venv\Scripts\python.exe" app.py
}
