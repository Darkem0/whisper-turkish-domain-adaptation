$Root = Split-Path -Parent $PSScriptRoot
$PidPath = Join-Path $Root 'state\supervisor.pid'
$RestartPath = Join-Path $Root 'state\watchdog_restarts.txt'
$restarts = if (Test-Path $RestartPath) { [int](Get-Content $RestartPath -Raw) } else { 0 }
while ($true) {
  Start-Sleep -Seconds 5
  if (-not (Test-Path $PidPath)) { continue }
  $id = [int](Get-Content $PidPath -Raw)
  if (-not (Get-Process -Id $id -ErrorAction SilentlyContinue)) {
    $queue = Get-Content (Join-Path $Root 'state\experiment_queue.json') -Raw | ConvertFrom-Json
    if (($queue | Where-Object { $_.status -eq 'PENDING' }).Count -gt 0 -and $restarts -lt 1) {
      $restarts++; $restarts | Set-Content $RestartPath
      & (Join-Path $Root 'scripts\Start-WhisperResearch.ps1')
    }
    break
  }
}
