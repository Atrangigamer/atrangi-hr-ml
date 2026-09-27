$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if (Test-Path 'INSTALL_STATUS.json') {
        $installState = Get-Content 'INSTALL_STATUS.json' -Raw | ConvertFrom-Json
        $installState | Format-List
        $installer = Get-Process -Id $installState.installer_pid -ErrorAction SilentlyContinue
        Write-Output "Installer process present: $([bool]$installer)"
    }
    docker compose ps
    try {
        Invoke-RestMethod 'http://127.0.0.1:8000/health/ready' -TimeoutSec 5
    } catch {
        Write-Output "Service is not ready: $($_.Exception.Message)"
    }
    nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader
} finally { Pop-Location }
