<#
.SYNOPSIS
    Stops the PratikAI backend and frontend processes started by start.ps1.
    Does NOT stop Ollama (it runs as a shared background service).
#>

$root = Split-Path -Parent $PSScriptRoot
$runDir = "$root\data\run"

function Stop-Tracked($name, $pidFile) {
    if (-not (Test-Path $pidFile)) {
        Write-Host "[--] $name not running (no PID file)"
        return
    }
    $processId = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($processId -and (Get-Process -Id $processId -ErrorAction SilentlyContinue)) {
        # taskkill /T kills the full process tree — needed because npm.cmd
        # spawns node.exe as a child that Stop-Process alone would leave running.
        taskkill /PID $processId /T /F | Out-Null
        Write-Host "[OK] Stopped $name (PID $processId)"
    } else {
        Write-Host "[--] $name not running (stale PID file)"
    }
    Remove-Item $pidFile -ErrorAction SilentlyContinue
}

Stop-Tracked "Frontend" "$runDir\frontend.pid"
Stop-Tracked "Backend" "$runDir\backend.pid"
