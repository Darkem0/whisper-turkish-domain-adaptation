# Metric and artefact discrepancy log

- The former A5–A6 zero-delta/self-comparison result is `SUPERSEDED_DUE_TO_REFERENCE_PATH_BUG` and excluded. Corrected analysis found 4,059 prediction differences and differing aggregate metrics for 27/28 targets.
- P7 has an early fixed-order/warm-cache microbenchmark showing approximately 32.12% MEM2 speedup with prediction parity, and a later interleaved cold/warm validation ending `PASSED_NO_MEANINGFUL_SPEEDUP`. Reconciled classification: `microbenchmark_positive / deployment_inconclusive / not_canonical`; MEM0 remains canonical.
- MEM3/MEM4 changed predictions and are `rejected_due_to_prediction_drift`.
- A7 eval contract retained a pre-smoke readiness label after execution; completed run progress and checkpoint locks are authoritative for completion.
- A7 original-run step-200 and stale variants are excluded. Retry1 step-200 is authoritative; it is optimizer-reset continuation, not exact state resume.
- `origin/main` tracked both `docs/NEGATIVE_RESULTS.md` and `docs/negative_results.md`. Windows checkout collapsed them into one path. Reconciliation retains the comprehensive lowercase document and removes the three-line case-duplicate.
- Several local automation scripts contain environment-specific paths and process orchestration. They are not published unchanged.
- Legacy VAD/repeat-safe claims remain historical because complete raw artefact chains are not present in the public checkout.
