# A7_v2 clipping-safe augmentation audit

`PASSED` — audio-only validation covered all 533 noise-containing occurrences: 267 `noise_gain` and 266 `phone_band_noise_gain`. The unchanged schedule hash is `e1ba3363f8d8d43d6f3c7c92726b2cc15ee2c21c7e02e3a6dc38507ad08efdcb`.

- Requested gain cycle is `0, -3, -6 dB`; no positive gain.
- Maximum final peak is `0.9800000191`, below the `0.980001` gate.
- Safety attenuation was needed for 6 occurrences in each noise bucket.
- Tensor hashes were deterministic; no NaN, Inf or silent waveform occurred.
- Maximum SNR change through common attenuation was `0.0 dB`.

The versioned lock is `data/materialized/training_a7_v2/a7_schedule_lock_clipping_safe_v2.json`.
