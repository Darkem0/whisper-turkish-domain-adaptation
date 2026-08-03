$root = Split-Path -Parent $PSScriptRoot
$watchdog = Join-Path $PSScriptRoot 'night_watchdog_v2d.ps1'
$run = Join-Path $root 'runs\night_watchdog_v2d'
New-Item -ItemType Directory -Force -Path $run | Out-Null
$arguments = '-NoProfile -ExecutionPolicy Bypass -File "{0}"' -f $watchdog
$p = Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $run 'launcher.stdout.log') -RedirectStandardError (Join-Path $run 'launcher.stderr.log') -PassThru
$p.Id
