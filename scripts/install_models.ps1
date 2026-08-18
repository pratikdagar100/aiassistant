<#
.SYNOPSIS
    Pulls the local models PratikAI needs via Ollama.
.DESCRIPTION
    Phase 1 defines this script for the default LLM only. Later phases
    (Whisper/faster-whisper, Piper TTS, embedding models) add their own
    downloads here once those subsystems are implemented — this script is
    intentionally not run automatically by setup.ps1 so multi-gigabyte
    downloads always happen on an explicit, informed decision.
.PARAMETER Model
    Ollama model tag to pull. Defaults to the project default, qwen3:8b.
#>

param(
    [string]$Model = "qwen3:8b"
)

$ErrorActionPreference = 'Stop'
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

try {
    ollama --version | Out-Null
} catch {
    Write-Host "[ERROR] Ollama is not installed or not on PATH. Install it with:" -ForegroundColor Red
    Write-Host "  winget install --id Ollama.Ollama -e"
    exit 1
}

try {
    Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version" -TimeoutSec 3 | Out-Null
} catch {
    Write-Host "[ERROR] Ollama service is not responding on http://127.0.0.1:11434." -ForegroundColor Red
    Write-Host "  Start it with: ollama serve"
    exit 1
}

Write-Host "Pulling $Model via Ollama (this can take a while — several GB)..." -ForegroundColor Cyan
ollama pull $Model
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] ollama pull failed — see output above." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] $Model is installed." -ForegroundColor Green
ollama list
