# A5_v2 decode warning audit

`WARNINGS_COMPARABLE_WITH_PRIOR_EVALUATIONS`

All 28 resolved target configurations lock the same decode settings: `language=tr`, `task=transcribe`, `num_beams=5`, `do_sample=false`, `condition_on_prev_tokens=false`, and `max_new_tokens=444`. Their common decode hash is `56da9f2ad11c84edbf3e9a894e06375a5fbe2a6830f5f7f7c3729a14a8564a6c`.

The worker used batch size one; no inter-sample padding was introduced. Observed non-fatal decoder warnings are comparable with the prior frozen-evaluation runs and do not evidence loss of Turkish forcing or a decode-configuration mismatch. No warning is promoted to a model-quality conclusion.
