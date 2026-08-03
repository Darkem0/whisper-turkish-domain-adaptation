param(
    [string]$Python = ".\.venv\Scripts\python.exe",
    [string]$Suite = "evaluation\suite_v2d.json"
)

$ErrorActionPreference = "Stop"

function Invoke-UntilComplete {
    param([string]$Manifest, [string]$OutputRoot, [int]$BatchSize = 25)
    while ($true) {
        & $Python -m whisper_arge.cli cache-base-predictions-batch --manifest $Manifest --output-root $OutputRoot --suite $Suite --batch-size $BatchSize
        if ($LASTEXITCODE -ne 0) { throw "A0 batch failed for $OutputRoot" }
        $progress = Get-Content (Join-Path $OutputRoot "progress.json") -Raw | ConvertFrom-Json
        if ($progress.completed) { break }
    }
    & $Python -m whisper_arge.cli finalize-base-predictions --output-root $OutputRoot
    if ($LASTEXITCODE -ne 0) { throw "A0 prediction finalization failed for $OutputRoot" }
}

# CV Spontaneous holdout is already fully decoded in the smoke run. All other
# domains are separate full caches. No training or acceptance-lock action occurs.
Invoke-UntilComplete "data\materialized\mediaspeech_v2d\paired\mediaspeech_holdout_paired_v2d.jsonl" "runs\a0_v2d_full\mediaspeech_paired"
Invoke-UntilComplete "data\materialized\hf_v2d\cv_scripted_test_v2d.jsonl" "runs\a0_v2d_full\cv_scripted"
Invoke-UntilComplete "data\materialized\fleurs_tr_v2d\fleurs_tr_test_v2d.jsonl" "runs\a0_v2d_full\fleurs"
Invoke-UntilComplete "data\materialized\tsc_v2a\tsc_full_v2a.jsonl" "runs\a0_v2d_full\tsc_exploratory"
