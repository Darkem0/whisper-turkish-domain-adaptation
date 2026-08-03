param([switch]$NewWindow)
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw "Missing virtual environment: $Python" }
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'state'),(Join-Path $Root 'reports'),(Join-Path $Root 'logs') | Out-Null
foreach($name in 'supervisor.pid','watchdog.pid') { $pidPath=Join-Path $Root "state\$name"; if(Test-Path $pidPath) { $old=(Get-Content $pidPath -Raw).Trim(); if($old -and -not (Get-Process -Id $old -ErrorAction SilentlyContinue)) { Remove-Item -LiteralPath $pidPath -Force } } }
$p = Start-Process -FilePath $Python -ArgumentList '-m automation.supervisor' -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $Root 'logs\supervisor.stdout.log') -RedirectStandardError (Join-Path $Root 'logs\supervisor.stderr.log') -PassThru
$p.Id | Set-Content -LiteralPath (Join-Path $Root 'state\supervisor.pid')
$watchdog = Start-Process -FilePath powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Root\scripts\Watchdog-WhisperResearch.ps1`"" -WindowStyle Hidden -RedirectStandardOutput (Join-Path $Root 'logs\watchdog.stdout.log') -RedirectStandardError (Join-Path $Root 'logs\watchdog.stderr.log') -PassThru
$watchdog.Id | Set-Content -LiteralPath (Join-Path $Root 'state\watchdog.pid')
if ($NewWindow) { Start-Process powershell.exe -ArgumentList "-NoExit -File `"$Root\scripts\Watch-WhisperResearch.ps1`"" }
Write-Host "Supervisor PID: $($p.Id)"
Write-Host "Watchdog PID: $($watchdog.Id)"
Write-Host "Watcher: powershell -ExecutionPolicy Bypass -File `"$Root\scripts\Watch-WhisperResearch.ps1`""
