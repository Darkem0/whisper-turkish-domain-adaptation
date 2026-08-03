# A5/A6 prediction and adapter parity audit

## Terminal precondition

`PASSED_CORRECTED_ANALYSIS`

The prior comparative-analysis defect is corrected with explicit A5 and A6 roots. This audit is read-only: it did not run inference, training, decoding, or modify an A0--A6 immutable run artefact.

## Direct locked-artefact result

The 28 checkpoint-by-dataset target pairs have complete `sample_id` parity, but they do **not** have prediction parity.

- `sample_id` parity: 28/28 targets.
- Different raw prediction strings: 4,059 total; every target has at least one difference.
- Different normalized WER and/or CER aggregate: 27/28 targets.
- Recomputed raw and normalized WER/CER match every saved per-target `metrics.json`: 56/56 experiment-target metrics.

The full, hash-addressed target inventory is [runs/A7_v2_staged_balanced_phone_parity_audit.json](../runs/A7_v2_staged_balanced_phone_parity_audit.json). The independent recomputation record is [runs/A7_v2_staged_balanced_phone_metric_recompute.json](../runs/A7_v2_staged_balanced_phone_metric_recompute.json).

Examples from the locked files:

| checkpoint | set | A5 normalized WER | A6 normalized WER | different predictions |
| --- | --- | ---: | ---: | ---: |
| step-050 | MediaSpeech Phone | 0.160748 | 0.158107 | 43 |
| step-100 | MediaSpeech Phone | 0.157968 | 0.160748 | 72 |
| step-150 | MediaSpeech G.711 | 0.150115 | 0.142748 | 116 |
| step-200 | MediaSpeech Phone | 0.161512 | 0.157203 | 115 |
| step-200 | FLEURS | 0.075210 | 0.068814 | 75 |

Thus the previously reported A5 best Phone (`step-100`, about 0.1580) and A6 best Phone (`step-200`, about 0.1572) are consistent with the raw prediction artefacts. The claim that all A5/A6 normalized metrics and paired CIs were zero is not.

## Cause of the false all-zero comparison

`scripts/analyze_a6_v2_results.py` derives its source by string replacement. Its final global replacement of `A5_v2` with `A6_v2` changes the inserted A5 frozen-evaluation root to the A6 path as well. Consequently, the generated comparison reads A6 predictions for both its A5 reference and A6 candidate, producing artificial zero deltas and `[0, 0]` intervals.

This is a comparative-analysis path-resolution defect. It does not alter the locked A5/A6 frozen-evaluation predictions or their per-target metrics, but it makes the derived A5--A6 paired-CI report non-authoritative until repaired and independently rerun from the immutable predictions.

## Adapter/load verification

The A6 frozen-evaluation worker is a minimum-diff A5 wrapper and resolves its `RUN` and `TRAIN_RUN` paths to A6. Each target `config.resolved.json` records the A6 checkpoint adapter SHA. The evaluator loads it with `PeftModel.from_pretrained(base, adapter_path)`.

Direct `safetensors` inspection confirms that every A6 checkpoint contains 160 LoRA tensors versus A5's 128, including 32 decoder Q/V LoRA A/B tensors. The decoder tensor norm sums are non-zero: 37.6455, 38.3650, 38.6963 and 38.7735 for steps 50, 100, 150 and 200. Therefore the decoder tensors are present and non-zero in the A6 adapter; the all-zero comparison is not evidence that the A6 adapter was identical to A5.

## Consequence

The explicit-path replacement is `scripts/analyze_a6_v2_results.py`. It regenerated the corrected metrics CSV, parity JSON, paired-CI JSON and trajectory. A7's remaining gate is source-bucket resolution, not A5/A6 prediction parity.
