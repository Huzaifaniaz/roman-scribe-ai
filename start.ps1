# Roman-Scribe AI Daily Launcher
$ErrorActionPreference = "Stop"

$laragonPython = "C:\laragon\bin\python\python-3.13"
$laragonNode = "C:\laragon\bin\nodejs\node-v22"
$env:Path = "$laragonPython;$laragonNode;" + $env:Path

Write-Host "Checking environment..." -ForegroundColor Cyan
if (-Not (Test-Path "e:\notetaking\roman-scribe-api\venv")) {
    Write-Host "ERROR: Virtual Environment not found. Please run 'setup.ps1' first!" -ForegroundColor Red
    pause
    exit
}

cd e:\notetaking\roman-scribe-api
.\venv\Scripts\activate

# Set Playwright path for this session
$env:PLAYWRIGHT_BROWSERS_PATH = "E:/notetaking/.cache/playwright"

Write-Host "Launching Roman-Scribe AI..." -ForegroundColor Green
python main.py
