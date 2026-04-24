$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "   ROMAN-SCRIBE AI - INITIAL SETUP     " -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# 1. Environment Detection (Laragon)
$laragonPython = "C:\laragon\bin\python\python-3.13"
$laragonNode = "C:\laragon\bin\nodejs\node-v22"

if (Test-Path $laragonPython) {
    $env:Path = "$laragonPython;" + $env:Path
}
if (Test-Path $laragonNode) {
    $env:Path = "$laragonNode;" + $env:Path
}

# 2. Python Backend Setup
Write-Host "`n--- [1/4] Setting up Python Virtual Environment ---" -ForegroundColor Yellow
cd e:\notetaking\roman-scribe-api
if (-Not (Test-Path venv)) {
    python -m venv venv
    Write-Host "Created new Virtual Environment."
}
.\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Playwright Setup (to E: drive cache)
Write-Host "`n--- [2/4] Installing Playwright Browsers (E: Drive) ---" -ForegroundColor Yellow
$env:PLAYWRIGHT_BROWSERS_PATH = "E:/notetaking/.cache/playwright"
.\venv\Scripts\python.exe -m playwright install chromium

# 4. React UI Setup
Write-Host "`n--- [3/4] Installing UI Dependencies ---" -ForegroundColor Yellow
cd e:\notetaking\roman-scribe-ui
npm install

# 5. Model Cache Check
Write-Host "`n--- [4/4] Environment Check ---" -ForegroundColor Yellow
if (-Not (Test-Path "E:\notetaking\.cache")) {
    New-Item -ItemType Directory -Path "E:\notetaking\.cache" -Force | Out-Null
}

Write-Host "`n======================================" -ForegroundColor Green
Write-Host "   SETUP COMPLETE!                     " -ForegroundColor Green
Write-Host "   Run 'start.ps1' to launch app.      " -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
