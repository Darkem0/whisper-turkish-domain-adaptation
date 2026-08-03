# A4_v2 contract audit

Status: `BLOCKED_A4_V2_CONTRACT_INPUTS`.

The matrix and readiness audit agree: A4 is the unchanged decoder-only q/v r16, diagnostic-only child of A2. It is fresh-base, uses no A3 parent weights, and inherits A2's 0 replay ratio and 200-step schedule. The pre-existing `contracts/A4_v2.layer_selective.yaml` is invalid and requests a different, layer-selective intervention; it is not used.

The contract cannot activate because its validation split cannot be locked without leakage.
