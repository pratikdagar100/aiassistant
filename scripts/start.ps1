<#
.SYNOPSIS
    Starts the PratikAI backend and frontend (and Ollama if it isn't already
    running), then runs a health check.
.PARAMETER NoFrontend
    Start only the backend (useful for headless/background operation).
#>

param(
    [switch]$NoFrontend
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Refresh PATH from the registry — a shell opened before Node/Ollama were
# installed (e.g. by scripts\setup.ps1 in the same session) would otherwise
# still have a stale PATH that can't find them.
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

$runDir = "$root\data\run"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$backendPidFile = "$runDir\backend.pid"
$frontendPidFile = "$runDir\frontend.pid"

function Test-ProcessAlive($pidFile) {
    if (-not (Test-Path $pidFile)) { return $false }
    $processId = Get-Content $pidFile -ErrorAction SilentlyContinue
    if (-not $processId) { return $false }
    return $null -ne (Get-Process -Id $processId -ErrorAction SilentlyContinue)
}

if (-not (Test-Path "$root\venv\Scripts\python.exe")) {
    Write-Host "[ERROR] venv not found. Run scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Ollama — winget installs it as a background service/tray app; only launch
# it ourselves if it isn't already answering on its API port.
try {
    Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version" -TimeoutSec 2 | Out-Null
    Write-Host "[OK] Ollama already running"
} catch {
    Write-Host "Starting Ollama..."
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

# Backend
if (Test-ProcessAlive $backendPidFile) {
    Write-Host "[OK] Backend already running (PID $(Get-Content $backendPidFile))"
} else {
    Write-Host "Starting backend..."
    $proc = Start-Process -FilePath "$root\venv\Scripts\python.exe" `
        -ArgumentList "-m", "app.main" `
        -WorkingDirectory $root `
        -WindowStyle Hidden `
        -RedirectStandardOutput "$root\data\logs\backend.out.log" `
        -RedirectStandardError "$root\data\logs\backend.err.log" `
        -PassThru
    $proc.Id | Out-File -Encoding ascii $backendPidFile
    Write-Host "[OK] Backend started (PID $($proc.Id))"
}

# Frontend
if (-not $NoFrontend) {
    if (Test-ProcessAlive $frontendPidFile) {
        Write-Host "[OK] Frontend already running (PID $(Get-Content $frontendPidFile))"
    } else {
        Write-Host "Starting frontend..."
        $proc = Start-Process -FilePath "npm.cmd" `
            -ArgumentList "run", "dev" `
            -WorkingDirectory "$root\frontend" `
            -WindowStyle Hidden `
            -RedirectStandardOutput "$root\data\logs\frontend.out.log" `
            -RedirectStandardError "$root\data\logs\frontend.err.log" `
            -PassThru
        $proc.Id | Out-File -Encoding ascii $frontendPidFile
        Write-Host "[OK] Frontend started (PID $($proc.Id))"
    }
}

Start-Sleep -Seconds 3
& "$PSScriptRoot\health_check.ps1"
