param([switch]$NewWindow)
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw "Missing virtual environment: $Python" }
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'state'),(Join-Path $Root 'reports'),(Join-Path $Root 'logs') | Out-Null
$p = Start-Process -FilePath $Python -ArgumentList '-m automation.supervisor' -WorkingDirectory $Root -WindowStyle Hidden -PassThru
$p.Id | Set-Content -LiteralPath (Join-Path $Root 'state\supervisor.pid')
$watchdog = Start-Process -FilePath powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Root\scripts\Watchdog-WhisperResearch.ps1`"" -WindowStyle Hidden -PassThru
$watchdog.Id | Set-Content -LiteralPath (Join-Path $Root 'state\watchdog.pid')
if ($NewWindow) { Start-Process powershell.exe -ArgumentList "-NoExit -File `"$Root\scripts\Watch-WhisperResearch.ps1`"" }
Write-Host "Supervisor PID: $($p.Id)"
Write-Host "Watchdog PID: $($watchdog.Id)"
Write-Host "Watcher: powershell -ExecutionPolicy Bypass -File `"$Root\scripts\Watch-WhisperResearch.ps1`""
