# A6_v2 decode comparability audit

`WARNINGS_COMPARABLE_WITH_PRIOR_EVALUATIONS`

A6 uses the same locked effective frozen-evaluation configuration as A3/A4/A5: `language=tr`, `task=transcribe`, `num_beams=5`, `do_sample=false`, `condition_on_prev_tokens=false`, and `max_new_tokens=444`. The batch size is one, so no inter-sample attention-mask padding is introduced. Forced-decoder-ID warnings retain the same non-fatal semantics as the prior evaluation workers; no effective decode-path difference was found.
