param(
    [string]$TaskName = "AgentsRulesSelfAuditNightly",
    [string]$TargetRepo = (Split-Path -Parent $PSScriptRoot),
    [string]$StartTime = "22:45"
)

$ErrorActionPreference = "Stop"

$PlaybookRoot = Split-Path -Parent $PSScriptRoot
$Script = Join-Path $PSScriptRoot "rules_self_audit.py"
$ResolvedTargetRepo = (Resolve-Path $TargetRepo).Path
$ReportDir = Join-Path $ResolvedTargetRepo "reports"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

$Command = @"
`$env:PYTHONUTF8 = '1'
Set-Location '$PlaybookRoot'
`$stamp = Get-Date -Format yyyy-MM-dd
`$report = Join-Path '$ReportDir' "agents-audit-`$stamp.md"
python '$Script' --repo '$ResolvedTargetRepo' --include-skill-references --out `$report *> (Join-Path '$ReportDir' "agents-audit-`$stamp.log")
"@

$Encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Command))
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -EncodedCommand $Encoded"
$Trigger = New-ScheduledTaskTrigger -Daily -At $StartTime
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Generate read-only AGENTS/rules self-audit reports after work hours." -Force | Out-Null

Write-Host "Registered scheduled task: $TaskName at $StartTime"
Write-Host "Target repo: $ResolvedTargetRepo"
Write-Host "Review reports under: $ReportDir"
