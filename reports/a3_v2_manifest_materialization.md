# A3_v2 manifest materialization

Status: **MATERIALIZED_NOT_TRAINED**. Train/validation/replay rows are 155007/9081/17224. SHA-256 values are locked in `contracts/A3_v2_data_manifest.lock.json`. The 200-step sampler has exactly 2,880 acoustic and 320 clean-replay microbatches (90/10).

Seven source rows were excluded for missing required fields: cvsp-68089, cvsp-72082, cvsp-78549, cvsp-78550, cvsp-79391, cvsp-84256, cvsp-91623. No frozen-evaluation overlap was found. CV spontaneous uses speaker-disjoint grouping; its small pool resulted in 17 validation rows, which is above the approximate 5% target to preserve group isolation.
