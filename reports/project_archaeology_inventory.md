# Project archaeology inventory

Scanned `201256` files across declared roots. `data/manifests`, `outputs/evaluation` and `outputs/predictions` are absent in this checkout. Large materialized data was counted by metadata only; no raw transcript/audio content is published.

{
  "README.md": 1,
  "docs": 14,
  "reports": 191,
  "runs": 3212,
  "state": 43,
  "logs": 42,
  "scripts": 95,
  "contracts": 26,
  "schemas": 3,
  "data/manifests": 0,
  "data/materialized": 197629,
  "outputs/evaluation": 0,
  "outputs/predictions": 0
}

| Method | Intervention | class | evidence / limitation |
|---|---|---|---|
| Legacy-H0 | baseline | historical_only | legacy archive only |
| Legacy-H1 | MediaSpeech-only LoRA | limited | clean proxy degradation recorded |
| Legacy-H2 | General Turkish LoRA | inconclusive | targeted run incomplete |
| Legacy-H3 | balanced-phone continuation | limited | historical telephone benefit, external regression |
| Legacy-H4 | repeat-safe decode/VAD | limited | historical long-call mitigation; legacy-only |
| A0 | base baseline | successful | controlled reference |
| A2 | encoder+decoder Q/V r16 | failed | target proxy gain but FLEURS hard gate failure |
| A3 | encoder-only + replay | failed | no promotable checkpoint; CV Scripted failure |
| A4 | decoder-only zero replay | diagnostic_only | strong phone ablation |
| A5 | encoder-only clean schedule | limited | scope ablation did not dominate |
| A6 | encoder+decoder clean schedule | diagnostic_only | corrected after self-comparison bug |
| A7 | A2 parent + source anchor + staged phone augmentation | successful | best observed phone proxy; continuation limitation |
