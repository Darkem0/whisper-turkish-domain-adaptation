# A4_v2 initialization decision

`fresh_base` is required. The A4 matrix changes only LoRA scope from A2's encoder+decoder q/v to decoder-only q/v. A3 checkpoints are prohibited as parent weights: their terminal negative result does not authorize transfer, and the matrix does not request it.
