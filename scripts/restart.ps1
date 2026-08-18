<#
.SYNOPSIS
    Restarts the PratikAI backend and frontend.
#>

$scriptDir = $PSScriptRoot
& "$scriptDir\stop.ps1"
Start-Sleep -Seconds 1
& "$scriptDir\start.ps1"
