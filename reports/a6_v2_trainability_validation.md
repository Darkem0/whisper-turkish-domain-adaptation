# A6_v2 trainability validation

`PASSED`

All 160 trainable tensors are LoRA A/B tensors under encoder or decoder Q/V projections: 128 encoder tensors and 32 decoder tensors. No base-model or non-Q/V tensor is trainable. Runtime gradient L1 totals were encoder=524.902174 and decoder=759.485983, proving backward-flow through both authorized scopes.
