# D7 repair summary

The D7 baseline subprofile completed 32/32 local WAV files and produced metrics. `D7_ALTERNATIVE_THRESHOLD` is `SKIPPED_UNSUPPORTED_PARAMETER`: the installed Transformers 4.46 Whisper path crashes when passed `no_speech_threshold`, so it is not falsely represented as applied. The exception boundary now writes a traceback and an append-only `technical_failed` event for future technical failures.
