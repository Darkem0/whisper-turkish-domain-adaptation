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
