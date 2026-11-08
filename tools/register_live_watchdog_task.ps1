<#
.SYNOPSIS
    Registers the 24/7 Live Recorder Watchdog in Windows Task Scheduler.
.DESCRIPTION
    Runs at system startup / user logon with highest available privileges,
    ensuring continuous data recording even after Windows reboot.
#>

$TaskName = "AntigravityLiveRecorderWatchdog"
$PythonExe = (Get-Command python).Source
$ScriptPath = "d:\cbot-atgvt\research\live_recorder_daemon.py"

Write-Host "Registering Windows Scheduled Task: $TaskName..." -ForegroundColor Cyan

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$ScriptPath`"" -WorkingDirectory "d:\cbot-atgvt"
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 365) -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1)

try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "24/7 cTrader Live Recorder & Fleet Watchdog" -Force
    Write-Host "Successfully registered $TaskName in Task Scheduler!" -ForegroundColor Green
} catch {
    Write-Host "Could not register Task Scheduler task automatically (Requires Admin): $_" -ForegroundColor Yellow
    Write-Host "You can run this script as Administrator to enable auto-start on Windows boot." -ForegroundColor Yellow
}
