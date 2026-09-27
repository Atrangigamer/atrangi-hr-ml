$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    docker compose stop
    if ($LASTEXITCODE -ne 0) { throw 'Docker could not stop the service.' }
} finally { Pop-Location }
