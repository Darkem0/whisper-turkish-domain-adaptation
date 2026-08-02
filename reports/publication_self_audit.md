# Publication self-audit

## Result

`PASS_WITH_DOCUMENTED_DISCREPANCIES`

The publication worktree was created from `origin/main`; the original dirty worktree remained read-only. Source commit `793c730` was reviewed as a detached snapshot and was not merged or cherry-picked.

## Scientific claims

- A7 Phone step-200: `0.15428452289943706` normalized WER.
- A7 robustness proxy step-150: `0.14757801098061019` normalized WER.
- A2 Phone: `0.170825`; A4 Phone: `0.158385`; A6 Phone: `0.157203`.
- A7 frozen evaluation: 28/28 targets integrity-verified.
- A7 authoritative step-200: `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET` from step-150, not exact optimizer-state resume.
- Former A5–A6 zero-delta result: superseded; corrected evidence records 4,059 differing predictions and 27/28 differing aggregate targets.
- Legacy-H0–H4 and controlled A0–A7 remain separate evidence classes.
- Phone/G.711/robustness values are open-data proxies, not actual company-domain performance.

## Memory-profile reconciliation

MEM2 is `microbenchmark_positive / deployment_inconclusive / not_canonical`. The early fixed-order warm-cache benchmark showed approximately 32.12% speedup with prediction parity; the later interleaved validation found 3.45% cold and -0.38% warm median change, below the promotion threshold. MEM0 remains canonical. MEM3/MEM4 are `rejected_due_to_prediction_drift`.

## Publication scope

Only documentation, aggregate CSV/JSON metrics, and reconciliation reports are included. No raw audio, transcript, prediction JSONL, manifest, checkpoint, adapter, log, state, cache, token, or company data is included.
