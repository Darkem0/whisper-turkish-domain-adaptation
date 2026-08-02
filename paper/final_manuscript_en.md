# Adapting Whisper Large-v3-Turbo for Turkish Telephone-Like Speech

## LoRA scope, staged domain adaptation, telephone augmentation, decoding, and negative transfer in an open-data study

**Author:** Emre Aslan  
**Research repository:** `Darkem0/whisper-turkish-domain-adaptation`

---

## Abstract

This study investigates adaptation of `openai/whisper-large-v3-turbo` to Turkish telephone-like and conversational speech. The work contains two distinct periods: archival Legacy experiments and a controlled A0–A7 series evaluated under a shared frozen protocol. The controlled series compares encoder-only, decoder-only, and encoder+decoder LoRA scopes; replay; clean schedules; parent-adapter continuation; source anchoring; and telephone-oriented waveform augmentation.

Evaluation covers MediaSpeech Clean, Phone, and G.711; CV Scripted; FLEURS; CV Spontaneous; and TSC, with raw and normalized WER/CER. The best controlled Phone result was produced by A7 step-200, a staged continuation from A2, with normalized WER `0.1542845`. A7 outperformed A2 (`0.170825`), decoder-only A4 (`0.158385`), and clean encoder+decoder A6 (`0.157203`) on the Phone proxy. Its best robustness-proxy result was `0.1475780` at step-150. However, A7 incurred a general-domain cost on CV Scripted, and A4 remained a strong Pareto candidate for robustness.

The results support staged domain adaptation for the telephone proxy, but do not support the claim that one adapter is best across all Turkish speech domains. Decoding, segmentation, stereo channel handling, prediction provenance, and checkpoint integrity were also found to be as important as model training. Because A7 changes parent continuation, source balance, and multiple augmentations together, the independent causal contribution of augmentation remains inconclusive.

**Keywords:** Whisper, Turkish ASR, LoRA, telephone speech, domain adaptation, negative transfer, WER, stereo speech processing.

---

## 1. Research question

The central question is not whether adding Turkish data automatically improves Whisper. The study asks:

1. How do encoder-only, decoder-only, and joint LoRA scopes affect telephone-like performance?
2. Can replay or staged continuation reduce forgetting?
3. Does a final integration of source anchoring and telephone-oriented augmentation improve the target proxy?
4. How should model, decoding, segmentation, and artifact integrity be evaluated together?

Telephone-like speech differs from clean read speech through short replies, interruptions, spontaneous wording, narrow-band channels, noise, repetition, and errors involving numbers, dates, amounts, and names. A single macro score is therefore insufficient.

---

## 2. Experimental periods

### 2.1. Archival Legacy series

The Legacy series used Common Voice, MediaSpeech, FLEURS, and Khan Academy material.

- **MediaSpeech-only LoRA:** MediaSpeech normalized WER degraded from `0.1558` to `0.2162`.
- **General Turkish LoRA:** Common Voice improved while MediaSpeech degraded.
- **Balanced-phone continuation:** improved in-distribution Common Voice/MediaSpeech tests but degraded an external clean-domain set from `0.0857` to `0.1018` normalized WER.
- **Repeat-safe decoding:** improved a long telephone example from `0.8469` to `0.6466` normalized WER.

The Legacy evidence establishes the historical motivation, but is not pooled with the controlled series because part of the original artifact chain is no longer available.

### 2.2. Controlled A0–A7 series

Shared controls include:

- plain Hugging Face Transformers Whisper,
- `openai/whisper-large-v3-turbo`,
- frozen base weights and PEFT/LoRA,
- rank 16, alpha 32, dropout 0.05,
- batch size 1 and gradient accumulation 16,
- FP16,
- shared frozen evaluation,
- raw and normalized WER/CER,
- prediction JSONL and SHA-256,
- checkpoint evaluation at steps 50, 100, 150, and 200,
- D3 decoding and MEM0 as the canonical comparison profiles.

---

## 3. Evaluation panels

| Panel | Datasets | Purpose |
|---|---|---|
| Telephone/conversational | MediaSpeech Phone, MediaSpeech G.711, robustness proxy, CV Spontaneous | Target-domain proxies |
| General Turkish monitoring | MediaSpeech Clean, CV Scripted, FLEURS, TSC | Negative transfer and generalization |

The results are open-data proxy measurements, not evidence of production call-center performance.

---

## 4. Controlled experiments

### A0 — Base model

A0 is the unadapted controlled reference. Its Phone normalized WER was approximately `0.17569`.

### A2 — Encoder+decoder Q/V LoRA

A2 improved target proxies and reached Phone WER `0.170825`, but showed a large FLEURS regression. It was not promoted as a production model and later served as the A7 parent.

### A3 — Encoder-only with 10% replay

A3 improved robustness but severely degraded CV Scripted. Ten percent replay did not preserve general-domain behavior, and the terminal decision was `A3_V2_NO_PROMOTABLE_CHECKPOINT`.

### A4 — Decoder-only, zero replay

A4 was a strong target-domain candidate:

- best Phone: step-050, `0.158385`,
- best robustness: approximately `0.1441`.

A4 remained a strong robustness Pareto candidate after A7.

### A5 — Encoder-only, clean schedule

A5 used a cleaned training manifest and zero replay. Its best Phone result was approximately `0.157968`, while its best robustness result was approximately `0.1475`. It did not surpass A4 on robustness.

### A6 — Encoder+decoder, clean schedule

A6 tested broader LoRA scope under the A5-matched data and schedule. Its best Phone result was `0.157203`. An initial report incorrectly claimed A5 and A6 were identical because a path-replacement bug compared A6 against itself. Re-analysis found 4,059 different predictions and different aggregate metrics in 27 of 28 targets.

### A7 — Staged source-anchored balanced-phone integration

A7 continued from the A2 adapter and used:

- an unchanged TSC source anchor,
- MediaSpeech and CV Spontaneous phone-like sources,
- phone-band processing,
- `0.75x` speed perturbation,
- noise/gain augmentation,
- combined phone-band and noise/gain augmentation,
- learning rate `5e-6`,
- 200 optimizer steps over 3,200 scheduled occurrences.

The augmentation policy evolved through three safety revisions. V3 applied a universal peak guard only to augmented buckets and passed an exhaustive 1,493/1,493 occurrence audit.

A7 training was interrupted when a worker terminal was closed. The final step-200 model was completed from the step-150 adapter using `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET`, with the sample schedule resumed from the correct global position. This is not an exact optimizer-state resume and is reported as a limitation.

---

## 5. Results

### 5.1. Phone comparison

| Model | Checkpoint | Normalized Phone WER |
|---|---:|---:|
| A0 | base | `0.17569` |
| A2 | base | `0.170825` |
| A4 | step-050 | `0.158385` |
| A5 | step-100 | `0.157968` |
| A6 | step-200 | `0.157203` |
| **A7** | **step-200** | **`0.1542845`** |

A7 point-estimate deltas were:

- `−0.021405` versus A0,
- `−0.016540` versus A2,
- `−0.004100` versus A4,
- `−0.002919` versus A6.

### 5.2. A7 checkpoint trajectory

| Target | Best checkpoint | Normalized WER |
|---|---:|---:|
| MediaSpeech Clean | step-200 | `0.134339` |
| MediaSpeech Phone | step-200 | `0.154285` |
| MediaSpeech G.711 | step-150 | `0.140802` |
| Robustness proxy | step-150 | `0.147578` |

No single checkpoint was best for every target.

### 5.3. General-domain cost

A7 did not preserve the A0/A2 CV Scripted level. The final scientific classification is:

- `staged_domain_adaptation_supported`,
- `staged_domain_adaptation_with_general_domain_cost`,
- `augmentation_contribution_inconclusive`.

The study therefore does not claim that A7 is universally superior.

---

## 6. Decoding and memory findings

D3 was selected as the supported decoding profile, with normalized WER `0.156021` in the controlled decode comparison.

Additional experiments found:

- no useful trigger for a second decoding pass,
- no safe deterministic ITN transformation in the evaluated outputs,
- no real n-best diversity suitable for rescoring.

In the memory benchmark:

- MEM1 provided a small equal-output speedup,
- MEM2 showed about 32.12% speedup in a small equal-output microbenchmark but lacked deployment-scale confirmation,
- MEM3 and MEM4 were faster but changed predictions.

MEM2 is classified as `microbenchmark-positive / deployment-inconclusive`; MEM3/MEM4 as `rejected_due_to_prediction_drift`. MEM0 remains canonical for scientific comparability.

---

## 7. Engineering reliability lessons

1. Validation loss alone does not select the best target-domain checkpoint.
2. Physical stereo channel information should precede diarization when reliable.
3. VAD, segmentation, and decoding can affect long-form quality as strongly as fine-tuning.
4. File extensions do not prove codec or sampling quality.
5. Prediction hashes and independent metric recomputation are essential.
6. PID/state files do not prove that a worker is alive or complete.
7. Model weights and sample-schedule position must resume from the same global step.
8. Checkpoints should be written atomically and recovery runs should use isolated directories.
9. A speed optimization that changes predictions is not the same scientific condition.
10. Negative results and implementation failures are part of the research record.

---

## 8. Public component ecosystem

The canonical research repository coordinates commit-pinned companion repositories:

- `turkish-speech-processing-platform` for channel-aware media processing,
- `contact-center-ai-evaluation-suite` for typed evidence-linked downstream evaluation,
- `research-publications` for source-backed publication metadata,
- `applied-ai-engineering-portfolio` for the evidence-aware project index.

The repositories remain independent to preserve their tests and Git histories. `ecosystem/components.lock.json` and the bootstrap utility materialize them into one local workspace.

---

## 9. Limitations

- Controlled results use public telephone-like proxies, not real company calls.
- A7 uses one seed and an optimizer-reset continuation.
- A7 does not isolate the causal contribution of each augmentation.
- CV Spontaneous is small and report-only.
- Some Legacy artifacts are no longer available.
- No large human-verified target set exists for numbers, amounts, dates, and names.
- A4 versus A7 has not been resolved on a real stereo call holdout.

---

## 10. Conclusion

A7 produced the best controlled Phone WER in this open-data study, while A4 remained a strong robustness candidate and A7 incurred a general-domain cost. The correct conclusion is not that one adapter is best everywhere.

> Turkish telephone-oriented ASR adaptation depends on data distribution, staged continuation, LoRA scope, channel and segmentation handling, decoding, and artifact integrity. Target-domain gains must be reported together with general-domain negative transfer and operational error profiles.

The open-data experimental line is closed with:

```text
OPEN_DATA_EXPERIMENT_LINE_COMPLETED
```

---

## Repository references

- `paper/final_manuscript_tr.md`
- `docs/full_research_report.md`
- `docs/complete_whisper_experience_archive.md`
- `docs/repository_ecosystem_audit.md`
- `public/metrics/a7_checkpoint_metrics.csv`
