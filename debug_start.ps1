Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
$env:Path += ";C:\Program Files\nodejs"

Write-Host "--- Installing UI Dependencies ---"
cd e:\notetaking\roman-scribe-ui
npm install

Write-Host "--- Starting Backend ---"
cd e:\notetaking\roman-scribe-api
Start-Process -NoNewWindow -FilePath ".\venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"

Write-Host "--- Starting Frontend ---"
cd e:\notetaking\roman-scribe-ui
npm run dev
