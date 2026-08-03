# A7_v2 resource smoke

`BLOCKED_A7_AUGMENTATION_POLICY_SMOKE`

Preflight passed: the A2 parent adapter SHA, A7 contract hashes, schedule hash and augmentation implementation hash all matched. The 2-step smoke then failed during deterministic on-the-fly augmentation before completing an optimizer step.

Exact blocker: `ValueError: clipping detected; normalization is prohibited` from `src/whisper_arge/a7_augmentation.py:apply` while producing the smoke slice. The A7 policy explicitly prohibits silently normalizing clipping, so this is a correct validation failure rather than a fallback transformation.

The original noise clipping failure is `SUPERSEDED_BY_CLIPPING_SAFE_AUGMENTATION_POLICY`: v2 passed its 533-occurrence noise audit. The v2 smoke then found a separate `phone_band` final-peak failure. That bucket has no authorized attenuation rule, so no full worker was started. See `runs/A7_v2_resource_smoke_clipping_safe_v2/failure.json`.
