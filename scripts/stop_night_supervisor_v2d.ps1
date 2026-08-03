$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$pidPath = Join-Path $root "runs\night_supervisor_v2d\supervisor.pid"
if (Test-Path -LiteralPath $pidPath) {
    $id = [int](Get-Content -LiteralPath $pidPath -Raw)
    $process = Get-Process -Id $id -ErrorAction SilentlyContinue
    if ($process) { Stop-Process -Id $id }
}
