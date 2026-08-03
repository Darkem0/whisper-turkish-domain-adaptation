# A6_v2 resource smoke

Status: `PASSED`.

- Fresh base; no parent adapter and no legacy resume.
- Two optimizer steps completed from 32 acoustic microbatches; replay was 0.
- Losses: 2.002747 and 1.930420; both finite.
- Runtime trainable parameter count: 3,276,800.
- Peak CUDA allocated/reserved: 1,836.20 / 2,044.00 MiB; reserved gate: under 10,000 MiB.
- Adapter SHA-256: `fa41da5bb5b9f8313e2576e451e24b1cea5423a9e037381fbd881f3c6f1891ba`.

The earlier smoke attempt is preserved under `runs/A6_v2_resource_smoke/attempts/pre-gradient-validation/`. The canonical attempt additionally verifies nonzero encoder and decoder gradient scopes.
