$root = Split-Path -Parent $PSScriptRoot
Get-Content -LiteralPath (Join-Path $root 'runs\night_supervisor_v2d\state.json') -Raw
Get-Content -LiteralPath (Join-Path $root 'runs\night_watchdog_v2d\heartbeat.json') -Raw
