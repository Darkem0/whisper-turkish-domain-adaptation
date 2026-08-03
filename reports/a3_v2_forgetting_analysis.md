# A3_v2 forgetting analysis

{
  "encoder_only_catastrophic_forgetting": "PARTIALLY_SUPPORTED: every A3 checkpoint regresses the frozen CV Scripted guardrail, but prediction-only evidence cannot identify parameter-level cause.",
  "transcript_style_or_data_mismatch": "PARTIALLY_SUPPORTED: regression varies by duration/reference-length buckets; no source/speaker subgroup evidence is available beyond dataset-level metadata.",
  "specific_cv_subgroups": "UNSUPPORTED: manifest speaker_id is null and no stable non-dataset group separates failures.",
  "clean_replay_effect": "UNSUPPORTED: the completed A3 run used a fixed 10 percent replay ratio; no replay-ablation prediction artefact exists.",
  "robustness_tradeoff": "PARTIALLY_SUPPORTED: prior frozen results show step-050/100 pass robustness while step-150/200 do not; causal explanation is not established."
}
