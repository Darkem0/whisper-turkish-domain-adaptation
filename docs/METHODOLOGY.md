# Methodology

Evaluate raw and normalized WER/CER side by side. Keep domain splits separate; do not collapse clean read speech, conversational speech, telephone audio, or noisy material into an unsupported overall claim.

Test VAD and segmentation as independent conditions. Test repeat-safe decoding as a decoding condition, not as a substitute for correcting the corpus or model. Adapter routing is a hypothesis: a routing decision requires held-out evaluation, an abstention/fallback rule, and failure analysis.

For public experiments, pin public dataset revisions and model revisions. Publish the manifest and the evaluation code before reporting metrics.

The included VAD helper is deterministic and synthetic. It demonstrates how a segmentation condition should be recorded, not a claim of real-world voice-activity quality.
