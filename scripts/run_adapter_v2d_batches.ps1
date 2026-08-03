param(
    [Parameter(Mandatory = $true)][string]$Adapter,
    [Parameter(Mandatory = $true)][string]$OutputRoot,
    [string]$Python = ".\.venv\Scripts\python.exe",
    [string]$Suite = "evaluation\suite_v2d.json",
    [string]$ModelRevision = "41f01f3fe87f28c78e2fbf8b568835947dd65ed9"
)

$ErrorActionPreference = "Stop"

function Invoke-UntilComplete {
    param([string]$Manifest, [string]$Domain, [int]$BatchSize = 25)
    $domainRoot = Join-Path $OutputRoot $Domain
    while ($true) {
        & $Python -m whisper_arge.cli cache-adapter-predictions-batch --manifest $Manifest --output-root $domainRoot --adapter $Adapter --suite $Suite --model-revision $ModelRevision --batch-size $BatchSize
        if ($LASTEXITCODE -ne 0) { throw "Adapter prediction batch failed for $domainRoot" }
        $progress = Get-Content (Join-Path $domainRoot "progress.json") -Raw | ConvertFrom-Json
        if ($progress.completed) { break }
    }
    & $Python -m whisper_arge.cli finalize-base-predictions --output-root $domainRoot
    if ($LASTEXITCODE -ne 0) { throw "Adapter prediction finalization failed for $domainRoot" }
}

Invoke-UntilComplete "data\materialized\mediaspeech_v2d\paired\mediaspeech_holdout_paired_v2d.jsonl" "mediaspeech_paired"
Invoke-UntilComplete "data\materialized\hf_v2d\cv_scripted_test_v2d.jsonl" "cv_scripted"
Invoke-UntilComplete "data\materialized\fleurs_tr_v2d\fleurs_tr_test_v2d.jsonl" "fleurs"
Invoke-UntilComplete "data\materialized\cv_spontaneous_v2c\cv_spontaneous_holdout_v2c.jsonl" "cv_spontaneous"
Invoke-UntilComplete "data\materialized\tsc_v2a\tsc_full_v2a.jsonl" "tsc_exploratory"

& $Python -m whisper_arge.cli evaluate-candidate-v2d --candidate-root $OutputRoot
if ($LASTEXITCODE -ne 0) { throw "Candidate metric computation failed for $OutputRoot" }
