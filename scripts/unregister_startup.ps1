<#
.SYNOPSIS
    Removes the PratikAI Windows startup scheduled task.
#>

$taskName = "PratikAI"

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "[OK] Removed scheduled task '$taskName'. PratikAI will no longer start automatically at login." -ForegroundColor Green
} else {
    Write-Host "[--] No '$taskName' scheduled task found — nothing to remove."
}
