# Metric and artefact discrepancy log

- The former A5–A6 zero-delta/self-comparison result is superseded and excluded.
- P7 has early placeholder/technical reports alongside later real interleaved validation; the authoritative terminal is `PASSED_NO_MEANINGFUL_SPEEDUP`, with MEM0 retained.
- A7 eval contract still names a pre-smoke readiness status although its run artefacts show completion; run progress and checkpoint locks are authoritative for completion.
- A7 original-run step-200 and stale variants are excluded. Retry1 step-200 is authoritative; it is optimizer-reset continuation, not exact state resume.
- Several scripts contain local cache/absolute paths: do not publish them unchanged.
- Legacy VAD/repeat-safe claims are historical because complete raw artefact chains are not present in this checkout.
