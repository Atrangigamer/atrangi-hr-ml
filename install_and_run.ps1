param([string]$ExistingProcessIds = '', [int]$WaitForBuildProcessId = 0)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-Location $PSScriptRoot
$statusPath = Join-Path $PSScriptRoot 'INSTALL_STATUS.json'
$logPath = Join-Path $PSScriptRoot 'installation.log'
$pythonPath = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
$waitPids = @($ExistingProcessIds.Split(',', [System.StringSplitOptions]::RemoveEmptyEntries) | ForEach-Object { [int]$_ })

function Set-InstallStatus([string]$stage, [string]$message) {
    @{ stage=$stage; message=$message; updated_at=(Get-Date).ToString('o'); installer_pid=$PID } |
        ConvertTo-Json | Set-Content -LiteralPath $statusPath -Encoding utf8
    Write-Output "$(Get-Date -Format o) $stage : $message"
}

function Invoke-Checked([scriptblock]$command, [string]$label, [int]$Attempts = 1) {
    for ($attempt=1; $attempt -le $Attempts; $attempt++) {
        & $command
        if ($LASTEXITCODE -eq 0) { return }
        if ($attempt -eq $Attempts) { throw "$label failed with exit code $LASTEXITCODE. See installation.log." }
        Write-Output "$label encountered a failure; retry $($attempt+1)/$Attempts in 10 seconds."
        Start-Sleep -Seconds 10
    }
}

Start-Transcript -Path $logPath -Append | Out-Null
try {
    Set-InstallStatus 'INSTALLING' 'Preparing dependencies and CUDA build alongside existing model downloads.'
    if (-not (Test-Path -LiteralPath $pythonPath)) {
        Invoke-Checked { uv venv .venv --python 3.12 } 'Python environment creation'
    }
    Set-InstallStatus 'DEPENDENCIES' 'Installing local test and model-preparation dependencies.'
    Invoke-Checked { uv pip install --python $pythonPath -r requirements-dev.txt 'huggingface-hub>=0.34,<2' } 'Local dependencies'
    $env:HF_HUB_DISABLE_XET = '1'
    $env:HF_HUB_DOWNLOAD_TIMEOUT = '120'
    $env:HF_HOME = Join-Path $PSScriptRoot '.model-download-cache'
    Set-InstallStatus 'BUILDING' 'Building the CUDA image while any existing model download continues.'
    if ($WaitForBuildProcessId -gt 0) {
        # Wait for a build already started by the operator; never launch a competing build.
        $buildProcess = Get-Process -Id $WaitForBuildProcessId -ErrorAction SilentlyContinue
        if ($buildProcess) {
            if ($buildProcess.ProcessName -ne 'docker-compose') { throw 'Expected a docker-compose build process.' }
            $buildStarted = $buildProcess.StartTime
            do {
                Start-Sleep -Seconds 10
                $buildProcess = Get-Process -Id $WaitForBuildProcessId -ErrorAction SilentlyContinue
            } while ($buildProcess -and $buildProcess.StartTime -eq $buildStarted)
        }
        # Rebuild from cache to verify success/current source before trusting an image.
    }
    Invoke-Checked { docker compose --progress plain build } 'CUDA image build' 3
    Set-InstallStatus 'MODELS' 'Waiting for existing model downloads to finish.'
    while ($waitPids.Count -gt 0) {
        $waitPids = @($waitPids | Where-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue })
        if ($waitPids.Count -gt 0) { Start-Sleep -Seconds 30 }
    }
    if (-not (Test-Path 'models/model_manifest.json')) {
        Set-InstallStatus 'MODELS' 'Downloading multilingual model weights.'
        Invoke-Checked { & $pythonPath scripts/download_models.py } 'Model download' 3
    }
    Set-InstallStatus 'CUDA_CHECK' 'Checking actual CUDA tensor execution inside the built image.'
    Invoke-Checked { docker run --rm --gpus all --entrypoint python atrangi-hr-ml:cuda -c 'import torch; assert torch.version.cuda and torch.cuda.is_available(); a=torch.ones((32,32),device="cuda"); assert float((a@a).sum().item())==32768.0; print(torch.cuda.get_device_name(0),torch.version.cuda)' } 'CUDA tensor test'
    Set-InstallStatus 'STARTING' 'Loading models and waiting for service readiness.'
    Invoke-Checked { docker compose up -d --wait --wait-timeout 600 } 'Service startup'
    Set-InstallStatus 'TESTING' 'Testing both endpoints with a synthetic resume and professional text.'
    Invoke-Checked { & $pythonPath -c 'from reportlab.pdfgen import canvas; c=canvas.Canvas("synthetic-install-test.pdf"); lines=["Alex Rivera","alex.rivera@example.com","Customer service specialist with 3 years of experience.","Skills: customer service, inventory management, Excel.","Bachelor of Commerce, Example University, 2021."]; [c.drawString(60,760-i*24,t) for i,t in enumerate(lines)]; c.save()' } 'Synthetic resume preparation'
    Invoke-Checked { & $pythonPath test_client.py --pdf synthetic-install-test.pdf --text 'Customer service and inventory management' } 'Live endpoint tests'
    Set-InstallStatus 'READY' 'GPU checks and both endpoint smoke tests passed. Service: http://127.0.0.1:8000/docs'
} catch {
    Set-InstallStatus 'FAILED' $_.Exception.Message
    docker compose logs --tail 100 ml
    exit 1
} finally {
    Stop-Transcript | Out-Null
}
