# A3_v2 preflight contract audit

Status: **READY_FOR_A3_V2_RESOURCE_SMOKE**. No training, smoke, decoding, or inference was run. The A3_v2 train, validation, replay, sampler, initialization, checkpoint/eval cadence, pinned environment, and frozen evaluation gates are now materialized and hash-locked. The next action is only the separately authorized two-step A3_v2 resource smoke.

A3 starts fresh from the pinned base model; A2 weights are not loaded. A2 remains a failed-promotion comparison reference and does not weaken gates.
