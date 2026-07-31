param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$run = Join-Path $root 'runs\night_watchdog_v2d'
New-Item -ItemType Directory -Force -Path $run | Out-Null
$lock = Join-Path $run 'watchdog.lock'
$pidFile = Join-Path $run 'watchdog.pid'
$log = Join-Path $run 'watchdog.log'
$errorLog = Join-Path $run 'watchdog_error.log'
$heartbeat = Join-Path $run 'heartbeat.json'
function Stamp { [DateTime]::UtcNow.ToString('o') }
function Log([string]$Message, [bool]$Error=$false) { Add-Content -LiteralPath $(if($Error){$errorLog}else{$log}) -Value "$(Stamp) $Message" }
function Alive([int]$Id) { return [bool](Get-Process -Id $Id -ErrorAction SilentlyContinue) }
if (Test-Path $lock) {
  $old = Get-Content $lock -Raw | ConvertFrom-Json
  if (Alive $old.pid) { throw "watchdog already active: $($old.pid)" }
  Remove-Item -LiteralPath $lock -Force
}
@{pid=$PID;started_at=Stamp} | ConvertTo-Json | Set-Content -LiteralPath $lock
$PID | Set-Content -LiteralPath $pidFile
Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class PowerState { [DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint flags); }'
[PowerState]::SetThreadExecutionState([uint32]::Parse('80000001',[System.Globalization.NumberStyles]::HexNumber)) | Out-Null
$restarts = 0; $delays = @(5,10,20,40,60)
try {
  while ($true) {
    $statePath = Join-Path $root 'runs\night_supervisor_v2d\state.json'
    $supervisorPidPath = Join-Path $root 'runs\night_supervisor_v2d\supervisor.pid'
    $state = if(Test-Path $statePath){Get-Content $statePath -Raw | ConvertFrom-Json}else{$null}
    $supervisorPid = if(Test-Path $supervisorPidPath){[int](Get-Content $supervisorPidPath -Raw)}else{0}
    $alive = Alive $supervisorPid
    @{timestamp=Stamp;supervisor_pid=$supervisorPid;supervisor_alive=$alive;state=if($state){$state.state}else{'missing'};restarts=$restarts} | ConvertTo-Json | Set-Content -LiteralPath $heartbeat
    if($state -and $state.state -eq 'DONE'){ Log 'pipeline DONE; watchdog exiting'; break }
    if(-not $alive) {
      if($restarts -ge 20){ Log 'restart limit reached' $true; break }
      $delay = $delays[[Math]::Min($restarts, $delays.Count-1)]
      Log "starting/resuming supervisor after $delay minute backoff"
      Start-Sleep -Seconds ($delay * 60)
      & (Join-Path $PSScriptRoot 'start_night_supervisor_v2d.ps1') -Resume -ContinueOnError | Out-Null
      $restarts++
    }
    Start-Sleep -Seconds 30
  }
} catch { Log $_.Exception.Message $true } finally { [PowerState]::SetThreadExecutionState([uint32]::Parse('80000000',[System.Globalization.NumberStyles]::HexNumber)) | Out-Null; Remove-Item -LiteralPath $lock -Force -ErrorAction SilentlyContinue; Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue }
