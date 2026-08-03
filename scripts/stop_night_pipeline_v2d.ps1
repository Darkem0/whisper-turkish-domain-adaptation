$root = Split-Path -Parent $PSScriptRoot
foreach($path in @('runs\night_watchdog_v2d\watchdog.pid','runs\night_supervisor_v2d\supervisor.pid')) { $file=Join-Path $root $path; if(Test-Path $file){$p=[int](Get-Content $file -Raw); Stop-Process -Id $p -ErrorAction SilentlyContinue} }
