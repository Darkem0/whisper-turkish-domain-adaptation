# Encoder–decoder attribution

## Design facts

| Experiment | Intervention | Replay |
| --- | --- | --- |
| A0 | base | n/a |
| A2 | encoder + decoder Q/V LoRA | experiment-specific prior design |
| A3 | encoder-only Q/V LoRA | 10% clean replay |
| A4 | decoder-only Q/V LoRA | 0% replay |

## Interpretation boundaries

- **Phone robustness is encoder-driven:** `HYPOTHESIS`, not established. A3/A4 differ simultaneously in LoRA location and replay, and A2 changes both encoder and decoder; the available factorial contrasts cannot isolate the encoder contribution.
- **Decoder-only helps the target domain:** supported only descriptively where an A4 MediaSpeech delta and its paired CI show a gain; it is not proof of a decoder-specific causal mechanism.
- **A3 CV Scripted regression is encoder-related:** `HYPOTHESIS`. Its measured regression is real in the A3 record, but A3's replay setting differs from A4.
- **Decoder involvement in A2 FLEURS regression:** `HYPOTHESIS` only. A2 is encoder+decoder and no decoder-only run with A2's replay/data conditions exists.
- **A2 requires the encoder+decoder combination:** unsupported. Its result cannot be decomposed without matched ablations.
- **Direct causal comparison blocked:** A3 versus A4 (layer target *and* replay), and A2 versus either A3/A4 (combined layer target plus prior experiment differences). The reports retain descriptive paired comparisons but do not convert them into causal claims.
