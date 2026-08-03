# A5 decision gate

## Decision

`BLOCKED_A5_HYPOTHESIS_NOT_FULLY_DEFINED`

The automatic data-quality audit and the focused manual-review package are complete. The schedule-impact audit shows that the findings do not provide evidence that they explain the broad A2/A3/A4 target-domain gains or general-domain regressions: A2 issue exposure was zero; A3 had zero empty-transcript exposure and 1.25% duplicate-cluster exposure; A4 had 1.625% empty-transcript and 0.875% duplicate-cluster exposure. Placeholder rows are validation-only, with a 2/9,081 (0.02202%) theoretical row upper bound.

The blocker is independent of that audit: the pre-existing A5 record does not fully define an executable experiment. See `a5_v2_hypothesis_resolution.md` for the exact missing field list. No A5 contract, versioned manifest, smoke, training worker, A6 action, or production promotion is authorized.
