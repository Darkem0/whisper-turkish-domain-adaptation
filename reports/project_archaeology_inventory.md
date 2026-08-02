# Project archaeology inventory

The read-only archaeology scan counted `201256` files across the declared local roots. `data/manifests`, `outputs/evaluation`, and `outputs/predictions` were absent in that checkout. Large materialized data was counted by metadata only; no raw transcript/audio content is published.

| Method | Intervention | class | evidence / limitation |
|---|---|---|---|
| Legacy-H0–H4 | historical baseline, LoRA, balanced-phone, repeat-safe/VAD | historical/limited/inconclusive | archival evidence; separate from controlled series |
| A0 | base baseline | successful | controlled reference |
| A2 | encoder+decoder Q/V r16 | failed promotion | target proxy gain, FLEURS hard-gate failure |
| A3 | encoder-only + replay | failed | no promotable checkpoint; CV Scripted failure |
| A4 | decoder-only zero replay | diagnostic_only | strong phone ablation |
| A5 | encoder-only clean schedule | limited | scope ablation did not dominate |
| A6 | encoder+decoder clean schedule | diagnostic_only | corrected after self-comparison bug |
| A7 | A2 parent + source anchor + staged phone augmentation | successful research result | best observed phone proxy; optimizer-reset continuation limitation |

The local scan inventory is historical evidence, not a list of files published in this repository.
