# D7 root cause

D7 alone injected `no_speech_threshold=0.5` into `model.generate`. With the installed Transformers 4.46 Whisper implementation this invokes fallback logic that dereferences an uninitialized `logprobs` local. The foreground traceback demonstrates the failure. The parameter is therefore unsupported for this executor/version combination and is not passed again.
