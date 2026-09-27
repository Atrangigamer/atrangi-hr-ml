$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (-not (Test-Path 'models/resume.gguf')) { throw 'Models missing. Follow README.md model preparation first.' }
    docker compose up -d --build --wait --wait-timeout 600
    if ($LASTEXITCODE -ne 0) { throw 'Service did not become healthy. Run docker compose logs ml.' }
    Write-Output 'Service ready: http://127.0.0.1:8000/docs'
} finally { Pop-Location }
