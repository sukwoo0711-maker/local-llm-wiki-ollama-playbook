param(
    [string]$TaskName = "LocalLlmWikiNightly",
    [string]$StartTime = "22:30",
    [string]$Model = "qwen2.5-coder:7b"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = "python"
$Script = Join-Path $PSScriptRoot "ollama_wiki_scout.py"
$LogDir = Join-Path $RepoRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Command = @"
Set-Location '$RepoRoot'
`$stamp = Get-Date -Format yyyy-MM-dd
python '$Script' gap-questions --model '$Model' --text 'Draft: administrative actions should be logged for audit review.' *> "logs\nightly-`$stamp.log"
"@

$Encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Command))
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -EncodedCommand $Encoded"
$Trigger = New-ScheduledTaskTrigger -Daily -At $StartTime
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Generate local LLM wiki candidate reports after work hours." -Force | Out-Null

Write-Host "Registered scheduled task: $TaskName at $StartTime"
Write-Host "Review logs under: $LogDir"
