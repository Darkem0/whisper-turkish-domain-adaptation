# Whisper AR-GE agent rules

- Keep the `I3R -> EXE -> FFmpeg WAV -> Transformers Whisper` path intact.
- Do not add alternate ASR runtimes, VAD, diarization, external LMs, or download dependencies/data.
- `evaluation/` and `protocols/immutable_test_registry.json` are immutable while a run is active.
- Never resume `A3_legacy_aborted_step34_invalid`.
- Record absent evidence as `MISSING` or `BLOCKED`; do not infer experimental results.
- Large data and generated run artifacts remain untracked.
