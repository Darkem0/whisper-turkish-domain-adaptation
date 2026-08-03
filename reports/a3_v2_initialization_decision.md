# A3_v2 initialization decision

A3_v2 uses `initialization_mode=fresh_base` from the pinned base model revision. `parent_adapter=null`, `parent_reference=A2_v2d_200`, and `parent_weights_loaded=false`. A2 is retained only as baseline/technical/comparison evidence; its failed promotion is neither a silent parent promotion nor a reason to relax any A3 gate. `src/whisper_arge/lora_train.py` is compatible because it loads the pinned base model and has no parent-adapter loading path. `A3_legacy_aborted_step34_invalid` is forbidden.
