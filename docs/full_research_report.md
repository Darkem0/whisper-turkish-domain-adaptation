# Türkçe Telefon Konuşmaları için Whisper Large-v3-Turbo Uyarlaması

# Project timeline

1. Legacy-H0–H4: historical baseline, LoRA and long-call/repeat-safe work; evidence is archival.
2. A0–A2: controlled baseline and encoder+decoder Q/V adaptation; A2 improved proxy robustness but failed FLEURS gate.
3. A3–A6: scope/replay ablations; A3 had no promotable checkpoint; A5–A6 comparison was corrected after a path-replacement/self-comparison defect.
4. A7: A2-parent staged source-anchor/phone augmentation. Step-200 was completed in an isolated optimizer-reset continuation from step-150.
5. Frozen A7 evaluation: 28/28 targets completed with the locked A7 mapping.

# Authoritative metrics summary

Only prediction/checkpoint-backed values are listed. Phone and robustness are open-data proxies, not operational call-centre metrics.

| result | checkpoint | normalized WER |
|---|---:|---:|
| A7 best Phone | step-200 | 0.15428452289943706 |
| A7 best robustness proxy | step-150 | 0.14757801098061019 |
| A2 Phone | base | 0.170825 |
| A4 Phone | step-050 | 0.158385 |
| A6 Phone | step-200 | 0.157203 |

A7 step-200 provenance: `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET` from step-150; do not interpret it as an exact optimizer-state continuation.

# Metric and artefact discrepancy log

- The former A5–A6 zero-delta/self-comparison result is superseded and excluded.
- P7 has early placeholder/technical reports alongside later real interleaved validation; the authoritative terminal is `PASSED_NO_MEANINGFUL_SPEEDUP`, with MEM0 retained.
- A7 eval contract still names a pre-smoke readiness status although its run artefacts show completion; run progress and checkpoint locks are authoritative for completion.
- A7 original-run step-200 and stale variants are excluded. Retry1 step-200 is authoritative; it is optimizer-reset continuation, not exact state resume.
- Several scripts contain local cache/absolute paths: do not publish them unchanged.
- Legacy VAD/repeat-safe claims are historical because complete raw artefact chains are not present in this checkout.
