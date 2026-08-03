# A4_v2 VRAM feasibility

RTX 4070 SUPER capacity is 12,282 MiB. A4 uses the A2-inherited fp16, batch 1, accumulation 16, checkpointing profile, but decoder-only trainable count and actual VRAM are `MISSING` until an authorized two-step smoke. The future smoke gate is reserved CUDA below 10,000 MiB; this is not a feasibility PASS.
