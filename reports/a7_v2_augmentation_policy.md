# A7_v2 augmentation policy — clipping-safe v2

Revision reason: smoke-detected clipping before any optimizer step. `training_contamination=false`.

Noise buckets use deterministic SNR cycling of 10/15/20 dB and requested gain cycling of 0/−3/−6 dB. After mixing and requested attenuation, only minimum whole-waveform attenuation to cap peak at 0.98 is allowed. No limiter, compressor, soft clipping, peak normalization, or source-audio mutation is allowed.
