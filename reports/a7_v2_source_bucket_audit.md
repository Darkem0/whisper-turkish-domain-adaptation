# A7_v2 source-bucket audit

## Terminal result

`SUPERSEDED_BY_SOURCE_ANCHOR_CONTRACT_REVISION`

The corrected A5/A6 analysis passed. The former clean/general bucket requirement is superseded: no TSC acoustic or linguistic-domain label is asserted. A7 now uses an exact-source `tsc_anchor_unchanged` population.

## Authoritative manifest evidence

The requested A7 population, `data/materialized/training_a5_v2/a5_train_manifest.jsonl`, has 172,231 rows and zero empty transcripts. Its available row-level domain-related fields are `source`, `sample_id`, audio hashes/paths, duration, and grouping metadata. The only source values are:

| source | rows | A7 interpretation supported by available metadata |
| --- | ---: | --- |
| `mediaspeech` | 1,919 | phone-like candidate, as explicitly allowed by the A7 request |
| `cv_spontaneous` | 17 | phone-like candidate, as explicitly allowed by the A7 request |
| `tsc` | 170,295 | `MISSING`: no manifest field or authoritative companion artefact labels it general, clean, or read speech |

The phone-like population is resolved from existing source labels. The TSC anchor requires only `source == tsc`, unchanged audio and unchanged transcript; it does not derive a clean/general/read label.

## Consequence

The replacement schedule and contract are now materialized under `data/materialized/training_a7_v2/` and `contracts/A7_v2_*`. The source-anchor revision does not make a clean-domain replay claim.
