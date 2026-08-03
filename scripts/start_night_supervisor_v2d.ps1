param([switch]$DryRun, [switch]$RecoverA1MetricFailure, [switch]$Resume, [switch]$ContinueOnError)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$run = Join-Path $root "runs\night_supervisor_v2d"
New-Item -ItemType Directory -Force -Path $run | Out-Null
$scriptPath = Join-Path $PSScriptRoot "night_supervisor_v2d.py"
$argumentList = '"{0}"' -f $scriptPath
if ($DryRun) { $argumentList += " --dry-run" }
if ($RecoverA1MetricFailure) { $argumentList += " --recover-a1-metric-failure" }
if ($Resume) { $argumentList += " --resume" }
if ($ContinueOnError) { $argumentList += " --continue-on-error" }
$process = Start-Process -FilePath $python -ArgumentList $argumentList -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $run "launcher.stdout.log") -RedirectStandardError (Join-Path $run "launcher.stderr.log") -PassThru
$process.Id
