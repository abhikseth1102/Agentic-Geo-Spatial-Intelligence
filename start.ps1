$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.runtime/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Create the .runtime Python environment using the README first.'
}
if (-not (Test-Path -LiteralPath 'data/atlas/speed_model.joblib')) {
    & $projectPython scripts/train_benchmark.py
    if ($LASTEXITCODE -ne 0) { throw 'Model preparation failed.' }
}
if (-not (Test-Path -LiteralPath 'frontend/dist/index.html')) {
    Push-Location frontend
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
}
Write-Host 'Open http://127.0.0.1:8080 in your browser. Press Ctrl+C to stop.'
& $projectPython -m uvicorn backend.main:app --host 127.0.0.1 --port 8080
