# A3_v2 resource smoke

Status: **PASSED**. The final fresh-base smoke process exited with code 0. It ran exactly two optimizer steps and did not start the 200-step training run.

The pinned `openai/whisper-large-v3-turbo` base model was loaded from the local cache with no parent adapter. `legacy_resume_attempted=false`; `A3_legacy_aborted_step34_invalid` was not used. The locked sampler contributed 31 acoustic and 1 clean-replay microbatch across 32 microbatches, preserving the precomputed deterministic schedule for this short smoke.

Losses were 2.2802734375 and 2.88958740234375. Step wall times were 5.1471686 s and 3.8624748 s; total measured training-loop wall time was 9.0105442 s. No CUDA OOM or non-finite loss occurred.

Peak CUDA allocated/reserved memory was 1825.98/2030.00 MiB, peak driver VRAM was 3578 MiB, and process RSS was 1771.82 MiB. The reserved-memory gate (<10,000 MiB) passed. The adapter checkpoint SHA-256 is `1be3477259a5c9d8acab0d0c27b42676faa37398cde34edb8ce23aa52b82be5e`.

Evidence: `runs/A3_v2_resource_smoke/config.resolved.json`, `environment.json`, `metrics.json`, `training_progress.json`, `adapter/`, and `artifact_lock.json`.

The execution log also retains an earlier two-step attempt whose process returned 2 solely because the acceptance aggregator treated the descriptive `cuda_oom=false` observation as a failing boolean. Its measured model/resource gates were already passing; the aggregator was corrected and the final fresh-base two-step process above exited 0. No 200-step training was run in either attempt.
