# A3/A4/A5 matched-ablation analysis

## A5 versus A4: encoder-only versus decoder-only, matched

A4 and A5 are fresh-base, zero-replay, same seed, 3,200 acoustic microbatches, batch/accumulation, optimizer, validation manifest and frozen suite. This is the controlled layer-scope comparison.

| checkpoint | A5-A4 Clean | Phone | G.711 | proxy | interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| step-050 | -0.0033 | +0.0024 | +0.0047 | +0.0001 | G.711 regression supported (CI [+0.0008, +0.0094]); other target deltas inconclusive. |
| step-100 | +0.0038 | -0.0006 | +0.0059 | +0.0032 | Clean and proxy regressions supported; Phone inconclusive. |
| step-150 | +0.0111 | +0.0025 | +0.0088 | +0.0084 | Clean, G.711 and proxy regressions supported. |
| step-200 | +0.0109 | +0.0024 | +0.0099 | +0.0085 | Clean, G.711 and proxy regressions supported. |

Negative deltas favor A5. A5 therefore does not outperform A4 on the primary MediaSpeech robustness proxy; only its step-100 Phone point estimate is lower, and that matched difference is inconclusive. The encoder-only zero-replay hypothesis is **not supported** by this frozen suite.

## A5 versus A3: replay contrast, not a fully controlled causal test

Both are encoder-only Q/V, but A3 has 10% clean replay and a different locked training population/schedule. A5 step-100 has a supported Phone gain over A3 step-100 (-0.0018, CI [-0.0038, -0.0001]); A5 steps 150/200 have supported G.711 gains over A3 (-0.0021 and -0.0023). These observations do not identify replay as the cause because the population and schedule also differ. The claim “zero replay is better than replay” is therefore **UNSUPPORTED**.

## A2 relationship

A2 differs in scope and locked data/schedule. Its observed pattern cannot isolate an encoder+decoder interaction or establish additivity from A3/A4/A5. An encoder+decoder diagnostic ablation remains informative, but it is not production evidence without a company-domain evaluation.
