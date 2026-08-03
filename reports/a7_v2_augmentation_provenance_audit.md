# A7_v2 augmentation provenance audit

## Result

`SUPERSEDED_BY_AUTHORIZED_A7_PRE_REGISTERED_POLICY`

The historical report describes a balanced-phone continuation with 8 kHz telephone-band processing, noise/gain augmentation and a 0.75x speed perturbation. It does not supply the executable recipe needed to reproduce these methods safely.

Repository evidence is explicitly negative: [contracts/A5_v2.phone_augmentation.yaml](../contracts/A5_v2.phone_augmentation.yaml) states that no repository artefact proves a pre-validated phone-augmentation recipe for this exact series. `ledger/experiments.jsonl` also marks the legacy balanced-phone recipe and repeat-safe result as `artifact_status=missing` and non-reproducible.

Found only as historical descriptions:

- approximate 8 h general / 16 h MediaSpeech weighting;
- learning rate `5e-6`;
- telephone-band/resampling, noise/gain and claimed 0.75x perturbation;
- a historical test.mp3 result.

Missing and therefore not materialized:

- balanced-phone manifest and immutable row list;
- per-augmentation probabilities and assignment policy;
- telephone-band filter/resampler implementation and exact parameters;
- noise source/provenance, SNR/range and gain range;
- executable 0.75x speed implementation and deterministic seed policy;
- G.711 choice/parameters, if any;
- legacy adapter/config hashes and test.mp3 prediction/reference artefacts.

No legacy values were inferred. The current A7 request authorizes a new pre-registered policy with explicit parameters, so this historical-provenance finding is no longer an independent A7 blocker. A7 remains blocked separately by `BLOCKED_A7_SOURCE_BUCKET_RESOLUTION`.
