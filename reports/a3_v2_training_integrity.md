# A3_v2 training integrity

Status: **PASSED**.

- `optimizer_steps_completed=200`; progress spans steps 1 through 200.
- `training_progress.jsonl` has exactly 3,200 rows and exactly matches the locked sampler’s microbatch index, sample ID, and role sequence.
- Fresh-base configuration is recorded with `parent_adapter=null`, `parent_weights_loaded=false`, and `legacy_resume_attempted=false`.
- Trainable parameter count was 2,621,440. Only encoder Q/V LoRA A/B tensors were trainable; base model weights remained frozen throughout the run.
- All final artifact-lock output SHA-256 values match the corresponding files.
- Each of steps 50/100/150/200 has verified adapter model/config, optimizer, scheduler, and resume-state hashes.

The host command wrapper timed out while the worker was running, but the local Python worker continued and completed. This is not a training failure; the completed output lock and exit code 0 are the terminal evidence.
