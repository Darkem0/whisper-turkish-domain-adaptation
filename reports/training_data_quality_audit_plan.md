# Training-data quality audit plan before A5

## Stage 1 — automated audit

Run on the locked A5 candidate manifest without training: transcript normalization/casing/punctuation consistency; exact and near duplicate audio/text; duration/text-length, SNR/level and codec distributions; silence/near-silence; segment-boundary and audio-text duration outliers; recording/speaker/template overrepresentation; Turkish/foreign-token and number/date/currency/name coverage; and manifest channel labels. Audio–text semantic alignment, crosstalk and agent/customer correctness are flags for review, not automatically asserted from metadata.

## Stage 2 — stratified human audit

Independently inspect clean telephone, noisy telephone, G.711, short/long speech, numbers/totals, proper names, agent/customer-labelled rows, high/low baseline WER and high A0/A4 disagreement rows. Record audio, transcript, normalized transcript, assessor decision and reason.

| Issue | Severity rule | Prevalence estimate | Likely model effect | Action |
| --- | --- | --- | --- | --- |
| Wrong/misaligned transcript | critical | stratified audited rate with CI | destructive supervision | remove/correct; re-lock split |
| Truncation/extra speech/crosstalk | high | automated flag + manual confirmation | deletion/insertion bias | re-segment or exclude |
| Wrong agent/customer channel | high | labelled-sample audit | role/domain mismatch | correct label or exclude |
| Silent/near-silent or codec imbalance | medium | full-manifest rate | spurious robustness result | rebalance/stratify |
| Duplicate audio/text/template dominance | high | exact/near-duplicate clusters | memorization and misleading validation | group-aware deduplicate |
| Number/name/foreign-token/normalization gaps | medium | coverage table + manual rate | business-critical substitutions | targeted data repair |

The audit must publish raw counts, sampling frame, reviewed sample IDs, reviewer rubric and unresolved blockers before an A5 training contract is materialized.
