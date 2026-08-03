# Final method inventory

| Method | Scope / design | status | scientific contribution |
|---|---|---|---|
| Legacy-H0..H4 | historical baseline, LoRA, continuation and decode work | historical context | not pooled with controlled A0–A7 |
| A0 | base | reference | open-data baseline |
| A2 | encoder+decoder Q/V | limited | parent for A7 |
| A3 | encoder-only + replay | failed promotion | CV Scripted guardrail failure |
| A4 | decoder-only zero replay | diagnostic | strong ablation candidate |
| A5 | encoder-only clean schedule | limited | scope ablation |
| A6 | encoder+decoder clean schedule | diagnostic | corrected comparison retained |
| A7 | A2 parent + TSC anchor + staged phone augmentation | completed | staged integration test |
