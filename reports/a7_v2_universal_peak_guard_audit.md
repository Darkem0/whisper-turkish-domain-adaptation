# A7 v3 universal augmented-output peak guard audit

`PASSED`

All 1,493 augmented occurrences were decoded and transformed twice without model loading. Output hashes were deterministic, finite and non-silent; all final peaks were at or below `0.980001`.

| bucket | occurrences | peak guard triggered |
| --- | ---: | ---: |
| phone_band | 640 | 30 |
| speed_075 | 320 | 7 |
| noise_gain | 267 | 6 |
| phone_band_noise_gain | 266 | 6 |

Maximum final peak: `0.9800000191`. Noise SNR change through scalar attenuation: `0.0 dB`. Schedule hash remained `e1ba3363f8d8d43d6f3c7c92726b2cc15ee2c21c7e02e3a6dc38507ad08efdcb`.

V3 lock: `data/materialized/training_a7_v2/a7_schedule_lock_peak_guard_v3.json`.
