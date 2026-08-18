<#
.SYNOPSIS
    Registers a Windows Scheduled Task that starts PratikAI at user logon.
.DESCRIPTION
    Uses Task Scheduler (visible in taskschd.msc / Task Manager > Startup),
    not a hidden registry Run key — startup must be transparent and
    user-controllable, never stealth persistence. Runs with the current
    user's normal privileges (no elevation, no admin requirement).
#>

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$taskName = "PratikAI"

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$root\scripts\start.ps1`"" `
    -WorkingDirectory $root

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)  # no time limit

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal -Description "Starts PratikAI backend and frontend at login." -Force | Out-Null

Write-Host "[OK] Registered scheduled task '$taskName' — PratikAI will start at your next login." -ForegroundColor Green
Write-Host "View/manage it in Task Scheduler (taskschd.msc) under Task Scheduler Library."
Write-Host "To disable: scripts\unregister_startup.ps1"
