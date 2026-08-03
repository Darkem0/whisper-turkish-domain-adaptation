# A5_v2 comparative analysis

A5 is a diagnostic-only fresh-base, encoder-only Q/V, zero-replay experiment. It is not a production candidate.

## A5 trajectory (normalized WER)

| checkpoint | Clean | Phone | G.711 | robustness proxy | CV Scripted | FLEURS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| step-050 | 0.1404 | 0.1607 | 0.1486 | **0.1475** | 0.2251 | 0.0702 |
| step-100 | 0.1425 | **0.1580** | 0.1487 | 0.1479 | **0.2224** | 0.0702 |
| step-150 | 0.1496 | 0.1612 | 0.1501 | 0.1527 | 0.2274 | **0.0700** |
| step-200 | 0.1496 | 0.1615 | 0.1499 | 0.1526 | 0.2225 | 0.0752 |

The best Phone result is A5 step-100 (0.1580); the best MediaSpeech robustness proxy is step-050 (0.1475). Later checkpoints worsen the proxy, so the public evidence does not support a late-checkpoint preference.

## Comparison with references

- Against A0, A5 step-100 has a supported Phone WER gain of -0.0177 (95% CI [-0.0356, -0.0026]), but has a supported CV Scripted regression of +0.0668 ([+0.0373, +0.0998]).
- Against A2, results are descriptive only: A2 differs in adaptation scope and locked population/schedule, so no causal attribution is made.
- Against A3/A4, checkpoint-matched paired results are in `a5_v2_statistical_analysis.md` and the full WER/CER grid is in `a0_a2_a3_a4_a5_metrics_comparison.csv`.

CV Scripted and FLEURS remain scientific monitoring sets rather than automatic production gates for this diagnostic experiment. Agent/customer, banking terminology, real call noise/crosstalk, critical-error rates, and a company call-center test set are `MISSING`; open-data results cannot justify deployment.
