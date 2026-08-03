# A4_v2 comparative analysis

All values are normalized corpus metrics reconstructed from locked predictions; lower is better. A4 remains diagnostic-only and no production promotion is made.

## A4 checkpoint trajectory

| Checkpoint | Clean WER | Phone WER | G.711 WER | Proxy | CV Scripted WER | FLEURS WER |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step-050 | 0.1437 | 0.1584 | 0.1439 | 0.1474 | 0.2249 | 0.0704 |
| step-100 | 0.1386 | 0.1585 | 0.1427 | 0.1446 | 0.2234 | 0.0698 |
| step-150 | 0.1386 | 0.1587 | 0.1413 | 0.1443 | 0.2416 | 0.0697 |
| step-200 | 0.1386 | 0.1591 | 0.1400 | 0.1441 | 0.2321 | 0.0697 |

## Category-specific references

- mediaspeech_clean: `step-150`.
- mediaspeech_phone: `step-050`.
- mediaspeech_g711: `step-200`.
- cv_scripted: `step-100`.
- fleurs: `step-150`.
- cv_spontaneous: `step-050`.
- tsc_exploratory: `step-100`.
- robustness_proxy: `step-200`.
- Lowest combined A0-relative CV Scripted + FLEURS WER regression: `step-100` (not a production score).

The full A0/A2/A3-step-050/A4 table, including WER/CER absolute deltas, is in `a0_a2_a3_a4_metrics_comparison.csv`. A3 step-050 is the meaningful frozen-evaluation reference; it is retained as research-only and its terminal decision is unchanged.
