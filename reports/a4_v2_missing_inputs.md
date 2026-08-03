# A4_v2 missing inputs

- `data/materialized/training_a4_v2/a4_validation_manifest.jsonl`: MISSING.
- Required input: a matrix-authorized, deterministic speaker/recording-group-disjoint validation split for the A2 train population.
- Blocker evidence: `data/materialized/training_a3_v2/a3_validation_manifest.jsonl` shares 9,081 `audio_sha256` values with `data/materialized/training_v2d/target_train_v2d.jsonl`; it cannot be reused.
- Consequent missing paths: `a4_train_manifest.jsonl`, `a4_replay_manifest.jsonl`, and `a4_sample_schedule.jsonl` are deliberately not materialized because their lock would depend on the unresolved split.
- `lora.trainable_parameter_count`: MISSING until an authorized pre-smoke pinned-model target-resolution check; no model was loaded here.
