# P7 batched prediction diff

Only one normalized-text mismatch was found: `media-02ac484c-7866-45d8-bb3d-bb81be5fda3b--clean`.

| mode | raw text difference | normalized effect |
|---|---|---|
| MEM0 / batch 1 | `Karaismaylioğlu` | baseline |
| MEM3 / batch 3 | `Kara İsmailoğlu` | one normalized word difference |
| MEM4 / batch 6 | `Kara İsmailoğlu` | same as MEM3 |

The prediction rows were keyed and compared by `sample_id`; this is not an output-remapping error. A minimal parity run passed `attention_mask` to `model.generate` and used the same language/task, D3 beam configuration, decoder prompt, and special-token decoding. Batch sizes 2, 3, and 6 still produced the batched spelling while batch size 1 produced the baseline spelling. Thus the mismatch is batch-dependent generation behavior in Transformers 4.46, not missing attention-mask propagation.
