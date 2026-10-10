# One-command launcher (Windows): installs dependencies on first run, then starts backend + frontend.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env - add your GROQ_API_KEY (or set LLM_MODE=ollama) for AI replies." -ForegroundColor Yellow
}

$py = Join-Path $root "venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Creating Python virtual environment..."
    python -m venv venv
}

$stamp = Join-Path $root "venv\.deps-installed"
if (-not (Test-Path $stamp) -or (Get-Item "backend\requirements.txt").LastWriteTime -gt (Get-Item $stamp).LastWriteTime) {
    Write-Host "Installing backend dependencies (first run takes a few minutes)..."
    & $py -m pip install --upgrade pip
    & $py -m pip install -r backend\requirements.txt
    New-Item $stamp -ItemType File -Force | Out-Null
}

if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Installing frontend dependencies..."
    Push-Location frontend
    npm install
    Pop-Location
}

$backend = Start-Process -FilePath $py -ArgumentList "main.py" -WorkingDirectory (Join-Path $root "backend") -PassThru -NoNewWindow
try {
    Write-Host ""
    Write-Host "Backend: http://127.0.0.1:8001   App: http://localhost:3000" -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop both."
    Push-Location frontend
    npm run dev
}
finally {
    Pop-Location
    if ($backend -and -not $backend.HasExited) { Stop-Process -Id $backend.Id -Force }
}
