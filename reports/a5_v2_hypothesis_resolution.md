# A5_v2 hypothesis resolution

## Pre-existing evidence

`experiments/matrix_v2.jsonl` defines the high-level A5 hypothesis: increasing clean replay from `0.0` to `0.1` should reduce forgetting. `docs/TARGET_PROXY_RESEARCH.md` additionally describes encoder+decoder Q/V LoRA at rank 16 with 10% clean replay. These are research-direction records, not a complete executable A5_v2 contract.

The only A5 contract artefact, `contracts/A5_v2.phone_augmentation.yaml`, has `validation: INVALID` and explicitly records absent source recipe/data evidence. It must not be treated as a valid training contract.

## Required fields audit

| Required field | Evidence state |
| --- | --- |
| Scientific hypothesis | PRESENT: `experiments/matrix_v2.jsonl:A5` |
| Exact intervention | PARTIAL: 10% clean replay is named; locked replay membership/mixture is absent |
| Initialization | MISSING: no A5 fresh-base/parent-adapter policy |
| LoRA modules/rank | PARTIAL: encoder+decoder Q/V r16 is documented; alpha/dropout are absent from an A5 contract |
| Optimizer/LR/scheduler | MISSING |
| Maximum steps | PARTIAL: 200-step matrix budget, no resolved A5 run policy |
| Checkpoint cadence | MISSING |
| Validation manifest | MISSING |
| Frozen evaluation plan | MISSING |
| Diagnostic or production-candidate status | MISSING |
| Deterministic seed | MISSING |

## Decision

`BLOCKED_A5_HYPOTHESIS_NOT_FULLY_DEFINED`

No A5 versioned population, schedule, contract, resource smoke, or full-training worker is materialized or started. Defining the missing fields is a new scientific/operational authorization, so it cannot be inferred from A2/A3/A4.
