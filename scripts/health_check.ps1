<#
.SYNOPSIS
    Checks the health of every PratikAI component and prints READY/WARNING/ERROR.
.DESCRIPTION
    Phase 1: checks Python, the venv, Node, Ollama, and the backend's own
    /api/health endpoint (which in turn checks the database and logging).
    Later phases extend this script as STT/TTS/vision/avatar come online.
#>

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

function Write-Status($name, $status, $detail = '') {
    $color = switch ($status) {
        'READY'   { 'Green' }
        'WARNING' { 'Yellow' }
        'ERROR'   { 'Red' }
        default   { 'Gray' }
    }
    $line = "[{0,-9}] {1}" -f $status, $name
    if ($detail) { $line += " — $detail" }
    Write-Host $line -ForegroundColor $color
}

Write-Host "`nPratikAI Health Check`n======================" -ForegroundColor Cyan

# Python venv
if (Test-Path "$root\venv\Scripts\python.exe") {
    $pyVer = & "$root\venv\Scripts\python.exe" --version 2>&1
    Write-Status "Python venv" "READY" $pyVer
} else {
    Write-Status "Python venv" "ERROR" "venv not found — run scripts\setup.ps1"
}

# Node / npm
try {
    $nodeVer = node --version 2>&1
    Write-Status "Node.js" "READY" $nodeVer
} catch {
    Write-Status "Node.js" "ERROR" "not found on PATH"
}

# Ollama
try {
    $ollamaVer = ollama --version 2>&1
    Write-Status "Ollama CLI" "READY" $ollamaVer
} catch {
    Write-Status "Ollama CLI" "ERROR" "not found on PATH — install from https://ollama.com"
}

# Backend health endpoint (covers database + logging + ollama connectivity)
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8756/api/health" -TimeoutSec 3
    Write-Status "Backend API" $health.status "phase $($health.phase)"
    foreach ($check in $health.checks.PSObject.Properties) {
        $detail = if ($check.Value.detail) { $check.Value.detail } else { '' }
        Write-Status "  -> $($check.Name)" $check.Value.status $detail
    }
} catch {
    Write-Status "Backend API" "ERROR" "not reachable at http://127.0.0.1:8756 — run scripts\start.ps1"
}

# Frontend dev server
try {
    $null = Invoke-WebRequest -Uri "http://127.0.0.1:5173" -TimeoutSec 3 -UseBasicParsing
    Write-Status "Frontend" "READY" "http://127.0.0.1:5173"
} catch {
    Write-Status "Frontend" "WARNING" "not reachable at http://127.0.0.1:5173 — run scripts\start.ps1"
}

Write-Host ""
