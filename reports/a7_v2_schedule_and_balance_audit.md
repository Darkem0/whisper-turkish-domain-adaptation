# A7_v2 schedule and balance audit

`PASSED` — 3,200 deterministic acoustic occurrences were materialized with seed `20260730`.

- `tsc_anchor_unchanged`: 1,067 from exact source `tsc`; no clean/read/scripted/general-domain claim.
- Phone-like total: 2,133 from exact sources `mediaspeech` and `cv_spontaneous`.
- Phone-like allocation is Hamilton largest-remainder per augmentation bucket, using eligible population counts; both sources are represented in every phone-like bucket.
- The occurrence ledger records deterministic seeds, original audio hashes, policy parameters, source and source-bucket. Cross-bucket reuse is explicit through `occurrence_count`.

Authoritative details and hashes: `data/materialized/training_a7_v2/a7_schedule_lock.json`.
